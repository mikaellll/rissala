"""Thin wrapper so views can call run_ai_query without knowing RAG internals."""
from .rag import run_rag_query


def run_ai_query(query: str, language: str = "fr") -> dict:
    """Run the full RAG pipeline. Returns {answer, sources, backend, duration_ms}."""
    return run_rag_query(query, language=language)
