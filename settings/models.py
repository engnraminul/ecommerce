from django.db import models

class Curier(models.Model):
    """Model for storing courier API credentials"""
    name = models.CharField(max_length=100, default="Default")
    api_url = models.URLField(max_length=255)
    api_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curier"
        verbose_name_plural = "Curiers"

    def __str__(self):
        return f"{self.name} ({self.api_url})"
