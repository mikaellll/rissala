from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    preferred_language = models.CharField(
        max_length=5,
        choices=[("fr", "Français"), ("ar", "العربية")],
        default="fr",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"

    def __str__(self):
        return f"Profil de {self.user.username}"

    @property
    def query_count(self):
        from apps.ai_engine.models import QueryHistory
        return QueryHistory.objects.filter(user=self.user).count()
