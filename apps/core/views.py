from django.shortcuts import render
from apps.search.models import Book


def home(request):
    """Landing page with stats and quick search."""
    stats = {
        "books": Book.objects.count(),
        "subjects": Book.objects.values("subject").distinct().count(),
    }
    context = {"stats": stats}
    return render(request, "core/home.html", context)


def about(request):
    """About page."""
    return render(request, "core/about.html")


def contact(request):
    """Contact page."""
    return render(request, "core/contact.html")
