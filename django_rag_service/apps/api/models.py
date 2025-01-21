from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=455)
    content = models.TextField()
    file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, related_name='chunks', on_delete=models.CASCADE)
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('document', 'chunk_index')
        ordering = ['chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of Document {self.document.title}"