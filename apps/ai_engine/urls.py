from django.urls import path
from . import views

app_name = "ai"

urlpatterns = [
    path("", views.ai_search, name="search"),
    path("query/", views.ai_query_ajax, name="query_ajax"),
]
