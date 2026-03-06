"""
Management command: import_shamela

Usage:
    python manage.py import_shamela
    python manage.py import_shamela --ids 1 2 3 100 200
    python manage.py import_shamela --range-start 1 --range-end 100
    python manage.py import_shamela --rebuild-index

This command:
1. Fetches book metadata from shamela.ws (or uses built-in seed data)
2. Saves Book records to DB
3. Fetches text chunks for each book
4. Rebuilds the FAISS vector index
"""

import time
import logging
from django.core.management.base import BaseCommand, CommandError
from apps.search.models import Book, BookChunk
from apps.search.fetcher import fetch_book_metadata, fetch_book_text

logger = logging.getLogger(__name__)

# Seed data — well-known Shamela book IDs to bootstrap the index
SEED_BOOK_IDS = [
    "1",    # Sahih Bukhari
    "2",    # Sahih Muslim
    "3",    # Sunan Abu Dawood
    "9",    # Muwatta Malik
    "23",   # Quran Tafsir Ibn Kathir
    "97",   # Riyadh as-Salihin
    "382",  # Al-Aqeedah al-Wasitiyya
]


class Command(BaseCommand):
    help = "Import books from shamela.ws into the local database and rebuild the vector index."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ids",
            nargs="+",
            type=str,
            help="Specific Shamela book IDs to import",
        )
        parser.add_argument(
            "--range-start",
            type=int,
            default=None,
            help="Start of book ID range to import",
        )
        parser.add_argument(
            "--range-end",
            type=int,
            default=None,
            help="End of book ID range to import",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=3,
            help="Number of pages to fetch per book (default: 3)",
        )
        parser.add_argument(
            "--rebuild-index",
            action="store_true",
            help="Rebuild the FAISS vector index from all DB chunks",
        )
        parser.add_argument(
            "--seed",
            action="store_true",
            default=True,
            help="Import the built-in seed books (default: True)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=2.0,
            help="Delay between requests in seconds (default: 2.0)",
        )

    def handle(self, *args, **options):
        if options["rebuild_index"]:
            self._rebuild_index()
            return

        # Determine which IDs to process
        ids_to_import = []
        if options.get("ids"):
            ids_to_import = options["ids"]
        elif options.get("range_start") and options.get("range_end"):
            ids_to_import = [str(i) for i in range(options["range_start"], options["range_end"] + 1)]
        else:
            # Default: seed data
            ids_to_import = SEED_BOOK_IDS

        self.stdout.write(
            self.style.NOTICE(f"📚 Importing {len(ids_to_import)} books from shamela.ws…")
        )

        success_count = 0
        error_count = 0
        new_chunks = []

        for i, book_id in enumerate(ids_to_import):
            self.stdout.write(f"  [{i+1}/{len(ids_to_import)}] Processing book #{book_id}…", ending="\r")

            try:
                # 1. Fetch / update metadata
                book = Book.objects.filter(shamela_id=book_id).first()
                if not book:
                    meta = fetch_book_metadata(book_id)
                    if meta:
                        book = Book.objects.create(**meta)
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Imported: {book.title[:60]}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  ⚠ Could not fetch metadata for #{book_id}"))
                        error_count += 1
                        continue
                else:
                    self.stdout.write(f"  → Already in DB: {book.title[:60]}")

                # 2. Fetch text pages
                pages_to_fetch = options["pages"]
                for page_num in range(1, pages_to_fetch + 1):
                    if BookChunk.objects.filter(book=book, page_number=page_num).exists():
                        continue  # Already indexed

                    text = fetch_book_text(book_id, page=page_num)
                    if text and len(text.strip()) > 50:
                        chunk = BookChunk.objects.create(
                            book=book,
                            page_number=page_num,
                            content=text[:4000],
                        )
                        new_chunks.append(chunk)

                    time.sleep(options["delay"])

                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error with #{book_id}: {e}"))
                error_count += 1

            # Polite delay between books
            if i < len(ids_to_import) - 1:
                time.sleep(options["delay"])

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Done! {success_count} books imported, {error_count} errors, "
                f"{len(new_chunks)} new chunks."
            )
        )

        if new_chunks:
            self.stdout.write("🔧 Adding new chunks to FAISS index…")
            try:
                from apps.ai_engine.rag import add_chunks_to_index
                add_chunks_to_index(new_chunks)
                self.stdout.write(self.style.SUCCESS("✅ FAISS index updated."))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠ Could not update FAISS index: {e}"))

    def _rebuild_index(self):
        """Completely rebuild the FAISS index from all DB chunks."""
        self.stdout.write("🔧 Rebuilding FAISS index from all DB chunks…")
        try:
            # Reset cached index
            import apps.ai_engine.rag as rag_module
            rag_module._faiss_index = None
            rag_module._faiss_ids = []

            # Delete existing index files
            from django.conf import settings
            from pathlib import Path
            index_dir = Path(settings.VECTOR_INDEX_DIR)
            for f in ["shamela.index", "shamela.ids.npy"]:
                fp = index_dir / f
                if fp.exists():
                    fp.unlink()

            # Rebuild
            index, ids = rag_module.get_faiss_index()
            self.stdout.write(
                self.style.SUCCESS(f"✅ FAISS index rebuilt with {index.ntotal} vectors.")
            )
        except Exception as e:
            raise CommandError(f"Failed to rebuild index: {e}")
