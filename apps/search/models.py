from django.db import models


class Book(models.Model):
    """Metadata record for a book from shamela.ws."""
    shamela_id = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=500, db_index=True)
    author = models.CharField(max_length=300, blank=True)
    subject = models.CharField(max_length=200, blank=True, db_index=True)
    description = models.TextField(blank=True)
    shamela_url = models.URLField(blank=True)
    indexed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Livre"
        verbose_name_plural = "Livres"
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} — {self.author}"


class BookChunk(models.Model):
    """A text chunk from a book page (for RAG)."""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chunks")
    page_number = models.PositiveIntegerField(default=1)
    content = models.TextField()
    # FAISS index row id for this chunk
    faiss_id = models.IntegerField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Extrait de Livre"
        verbose_name_plural = "Extraits de Livres"
        ordering = ["book", "page_number"]

    def __str__(self):
        return f"{self.book.title} — p.{self.page_number}"
