from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("history/<int:pk>/delete/", views.delete_history_item, name="delete_history"),
]
