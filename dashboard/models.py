from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardSetting(models.Model):
    """Model for storing dashboard settings and preferences."""
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key

class AdminActivity(models.Model):
    """Model for tracking admin user activities in the dashboard."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Admin activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
