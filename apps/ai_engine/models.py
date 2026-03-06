from django.db import models
from django.contrib.auth.models import User


class QueryHistory(models.Model):
    """Records every AI query a user makes."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="queries", null=True, blank=True
    )
    query = models.TextField()
    response = models.TextField(blank=True)
    sources = models.JSONField(default=list, blank=True)  # list of {title, url}
    ai_backend = models.CharField(max_length=50, default="openai")
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historique Requête"
        verbose_name_plural = "Historique Requêtes"
        ordering = ["-created_at"]

    def __str__(self):
        user_str = self.user.username if self.user else "Anonyme"
        return f"[{user_str}] {self.query[:60]}"
