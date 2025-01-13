from django.db import models
import uuid

# Model for storing vector data
class DocumentVector(models.Model):
    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    vector = models.BinaryField()