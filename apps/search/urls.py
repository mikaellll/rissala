from django.urls import path
from . import views

app_name = "search"

urlpatterns = [
    path("", views.search_view, name="search"),
    path("books/", views.book_list, name="book_list"),
    path("books/<str:shamela_id>/", views.book_detail, name="book_detail"),
]
