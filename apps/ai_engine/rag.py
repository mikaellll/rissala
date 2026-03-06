"""
RAG (Retrieval-Augmented Generation) engine.

Pipeline:
1. Retrieve relevant BookChunks from local FAISS index (or DB fallback)
2. If no local chunks, fetch from shamela.ws and index on-the-fly
3. Build prompt with retrieved context
4. Call AI backend (OpenAI or Ollama)
5. Return answer + source references
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedding model (lazy-loaded singleton)
# ---------------------------------------------------------------------------
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        model_name = getattr(settings, "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        logger.info(f"Loading embedding model: {model_name}")
        _embedder = SentenceTransformer(model_name)
    return _embedder


# ---------------------------------------------------------------------------
# FAISS index (lazy-loaded)
# ---------------------------------------------------------------------------
_faiss_index = None
_faiss_ids = []   # maps FAISS row → BookChunk pk

def _index_path() -> Path:
    path = Path(settings.VECTOR_INDEX_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_faiss_index():
    """Load or build the FAISS index from DB chunks."""
    global _faiss_index, _faiss_ids
    import faiss
    from apps.search.models import BookChunk

    index_file = _index_path() / "shamela.index"
    ids_file = _index_path() / "shamela.ids.npy"

    if _faiss_index is not None:
        return _faiss_index, _faiss_ids

    if index_file.exists() and ids_file.exists():
        logger.info("Loading FAISS index from disk…")
        _faiss_index = faiss.read_index(str(index_file))
        _faiss_ids = np.load(str(ids_file)).tolist()
        return _faiss_index, _faiss_ids

    # Build from DB
    logger.info("Building FAISS index from DB chunks…")
    chunks = list(BookChunk.objects.all())
    if not chunks:
        logger.warning("No chunks in DB — index will be empty.")
        dim = 384  # MiniLM dim
        _faiss_index = faiss.IndexFlatIP(dim)
        _faiss_ids = []
        return _faiss_index, _faiss_ids

    embedder = get_embedder()
    texts = [c.content[:512] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype("float32"))

    faiss.write_index(index, str(index_file))
    np.save(str(ids_file), np.array([c.pk for c in chunks]))

    _faiss_index = index
    _faiss_ids = [c.pk for c in chunks]
    return _faiss_index, _faiss_ids


def add_chunks_to_index(chunks):
    """Add new BookChunk instances to the running FAISS index."""
    global _faiss_index, _faiss_ids
    import faiss
    from apps.search.models import BookChunk

    embedder = get_embedder()
    texts = [c.content[:512] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)

    index, ids = get_faiss_index()
    start_id = index.ntotal
    index.add(embeddings.astype("float32"))

    for i, chunk in enumerate(chunks):
        chunk.faiss_id = start_id + i
        chunk.save(update_fields=["faiss_id"])
        _faiss_ids.append(chunk.pk)

    # Persist
    import faiss as _faiss
    _faiss.write_index(index, str(_index_path() / "shamela.index"))
    np.save(str(_index_path() / "shamela.ids.npy"), np.array(_faiss_ids))


def retrieve_context(query: str, top_k: int = 5) -> list[dict]:
    """
    Retrieve top-k relevant chunks for a query.
    Returns list of dicts: {content, book_title, book_author, shamela_url}
    """
    from apps.search.models import BookChunk

    try:
        index, ids = get_faiss_index()
    except Exception as e:
        logger.error(f"FAISS error: {e}")
        return []

    if index.ntotal == 0:
        return []

    embedder = get_embedder()
    q_emb = embedder.encode([query], normalize_embeddings=True).astype("float32")
    scores, faiss_rows = index.search(q_emb, min(top_k, index.ntotal))

    results = []
    for score, row in zip(scores[0], faiss_rows[0]):
        if row < 0 or score < 0.1:
            continue
        try:
            chunk_pk = ids[row]
            chunk = BookChunk.objects.select_related("book").get(pk=chunk_pk)
            results.append({
                "content": chunk.content,
                "book_title": chunk.book.title,
                "book_author": chunk.book.author,
                "shamela_url": chunk.book.shamela_url,
                "score": float(score),
            })
        except Exception:
            continue

    return results


# ---------------------------------------------------------------------------
# AI Backend
# ---------------------------------------------------------------------------
def build_prompt(query: str, context_chunks: list[dict], language: str = "fr") -> str:
    """Construct the RAG prompt."""
    if language == "ar":
        system_note = "أجب باللغة العربية بشكل واضح ودقيق."
        context_header = "النصوص المرجعية من مكتبة شاملة:"
        question_header = "السؤال:"
    else:
        system_note = "Réponds en français de manière claire, précise et académique."
        context_header = "Textes de référence extraits de la bibliothèque Shamela :"
        question_header = "Question :"

    if context_chunks:
        context_text = "\n\n---\n\n".join(
            f"[{c['book_title']} — {c['book_author']}]\n{c['content'][:800]}"
            for c in context_chunks
        )
        context_section = f"\n{context_header}\n\n{context_text}\n\n"
    else:
        context_section = "\n[Aucun texte de référence trouvé dans l'index local.]\n\n"

    prompt = (
        f"{system_note}\n"
        f"{context_section}"
        f"{question_header} {query}\n\n"
        "---\n"
        "Réponse basée sur les textes ci-dessus :"
    )
    return prompt


def call_openai(prompt: str) -> str:
    """Call OpenAI GPT API."""
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un assistant spécialisé en littérature islamique arabe. "
                    "Tu aides les utilisateurs à comprendre les textes de la bibliothèque Shamela. "
                    "Tu cites toujours tes sources. Tu es précis, respectueux et académique."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_ollama(prompt: str) -> str:
    """Call local Ollama model."""
    import ollama as _ollama
    client = _ollama.Client(host=settings.OLLAMA_HOST)
    response = client.generate(
        model=settings.OLLAMA_MODEL,
        prompt=prompt,
        options={"temperature": 0.3, "num_predict": 1500},
    )
    return response.get("response", "")


def run_rag_query(query: str, language: str = "fr") -> dict:
    """
    Full RAG pipeline.
    Returns dict: {answer, sources, backend, duration_ms}
    """
    start = time.time()
    backend = getattr(settings, "AI_BACKEND", "openai")

    # 1. Retrieve context
    contexts = retrieve_context(query, top_k=5)

    # 2. If no context, try live Shamela fetch and index on-the-fly
    if not contexts:
        try:
            from apps.search.fetcher import search_shamela_books, fetch_book_text
            from apps.search.models import Book, BookChunk

            live_results = search_shamela_books(query, limit=3)
            for res in live_results[:2]:
                book, _ = Book.objects.get_or_create(
                    shamela_id=res["shamela_id"],
                    defaults={
                        "title": res["title"],
                        "author": res["author"],
                        "subject": res["subject"],
                        "shamela_url": res["url"],
                    },
                )
                if not book.chunks.exists():
                    text = fetch_book_text(res["shamela_id"], page=1)
                    if text:
                        chunk = BookChunk.objects.create(
                            book=book,
                            page_number=1,
                            content=text[:3000],
                        )
                        add_chunks_to_index([chunk])

            contexts = retrieve_context(query, top_k=5)
        except Exception as e:
            logger.error(f"Live fetch error: {e}")

    # 3. Build prompt
    prompt = build_prompt(query, contexts, language)

    # 4. Call AI
    answer = ""
    try:
        if backend == "ollama":
            answer = call_ollama(prompt)
        else:
            answer = call_openai(prompt)
    except Exception as e:
        logger.error(f"AI call failed ({backend}): {e}")
        if backend == "openai":
            answer = (
                "⚠️ Le service IA est temporairement indisponible. "
                "Vérifiez votre clé API OpenAI ou passez en mode Ollama local."
            )
        else:
            answer = (
                "⚠️ Le modèle IA local (Ollama) est inaccessible. "
                f"Assurez-vous qu'Ollama tourne sur {settings.OLLAMA_HOST}."
            )

    duration_ms = int((time.time() - start) * 1000)

    sources = [
        {"title": c["book_title"], "author": c["book_author"], "url": c["shamela_url"]}
        for c in contexts
    ]

    return {
        "answer": answer,
        "sources": sources,
        "backend": backend,
        "duration_ms": duration_ms,
    }
