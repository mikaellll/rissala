import logging
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Book
from .fetcher import search_shamela_books, fetch_book_metadata
from apps.ai_engine.tasks import run_ai_query

logger = logging.getLogger(__name__)


def search_view(request):
    """Main IA search page: combines local index + shamela live fetch."""
    query = request.GET.get("q", "").strip()
    results = []
    local_books = []
    error = None

    if query:
        # 1. Search local index first
        local_books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(subject__icontains=query) |
            Q(description__icontains=query)
        )[:20]

        # 2. If nothing local, fetch from shamela.ws (limited)
        if not local_books.exists():
            try:
                results = search_shamela_books(query, limit=10)
            except Exception as e:
                logger.error(f"Shamela fetch error: {e}")
                error = "Impossible de contacter shamela.ws. Vérifiez votre connexion."

    context = {
        "query": query,
        "local_books": local_books,
        "shamela_results": results,
        "error": error,
    }
    return render(request, "search/search.html", context)


def book_list(request):
    """List all books in the local index with pagination and filtering."""
    subject_filter = request.GET.get("subject", "")
    query = request.GET.get("q", "")

    books_qs = Book.objects.all()
    if subject_filter:
        books_qs = books_qs.filter(subject__icontains=subject_filter)
    if query:
        books_qs = books_qs.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        )

    subjects = Book.objects.values_list("subject", flat=True).distinct().exclude(subject="").order_by("subject")
    paginator = Paginator(books_qs, 20)
    page = paginator.get_page(request.GET.get("page"))

    context = {
        "books_page": page,
        "subjects": subjects,
        "current_subject": subject_filter,
        "query": query,
    }
    return render(request, "search/book_list.html", context)


def book_detail(request, shamela_id):
    """Book detail: local or fetched from shamela."""
    book = Book.objects.filter(shamela_id=shamela_id).first()

    if not book:
        # Try to fetch from shamela
        meta = fetch_book_metadata(shamela_id)
        if meta:
            book = Book.objects.create(**meta)

    if not book:
        from django.http import Http404
        raise Http404("Livre non trouvé")

    chunks = book.chunks.all()[:5]  # Preview only

    context = {
        "book": book,
        "chunks": chunks,
    }
    return render(request, "search/book_detail.html", context)
