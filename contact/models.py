from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class ContactSetting(models.Model):
    """Model for storing contact page settings and business information."""
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
    
    class Meta:
        verbose_name = 'Contact Setting'
        verbose_name_plural = 'Contact Settings'


class Contact(models.Model):
    """Model for storing contact form submissions."""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('resolved', 'Resolved'),
        ('spam', 'Spam'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Contact information
    name = models.CharField(max_length=100, help_text="Full name of the person contacting")
    phone = models.CharField(max_length=20, help_text="Phone number")
    email = models.EmailField(help_text="Email address")
    
    # Message details
    subject = models.CharField(max_length=200, blank=True, help_text="Subject of the inquiry")
    message = models.TextField(help_text="Contact message")
    
    # File attachment
    attachment = models.FileField(
        upload_to='contact_attachments/%Y/%m/',
        blank=True,
        null=True,
        help_text="Optional file attachment (max 10MB)"
    )
    
    # Status and priority
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='new',
        help_text="Current status of the contact"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level"
    )
    
    # Tracking information
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the submitter"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser user agent string"
    )
    
    # Admin notes
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for admin reference"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_app_assignments',
        help_text="Admin user assigned to handle this contact"
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    replied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When a reply was sent"
    )
    
    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', '-submitted_at']),
            models.Index(fields=['priority', '-submitted_at']),
            models.Index(fields=['email', '-submitted_at']),
        ]
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'
    
    def __str__(self):
        return f"{self.name} - {self.email} ({self.get_status_display()})"
    
    def clean(self):
        """Validate contact form data"""
        import re
        
        # Validate phone number format
        if self.phone:
            # Remove any formatting characters
            clean_phone = re.sub(r'[^\d+\-\(\)\s]', '', self.phone)
            if len(re.sub(r'[^\d]', '', clean_phone)) < 10:
                raise ValidationError({
                    'phone': 'Please enter a valid phone number with at least 10 digits.'
                })
        
        # Validate file size if attachment exists
        if self.attachment:
            if self.attachment.size > 10 * 1024 * 1024:  # 10MB limit
                raise ValidationError({
                    'attachment': 'File size cannot exceed 10MB.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def mark_as_read(self, user=None):
        """Mark contact as read"""
        if self.status == 'new':
            self.status = 'read'
            if user:
                self.assigned_to = user
            self.save(update_fields=['status', 'assigned_to', 'updated_at'])
    
    def mark_as_replied(self, user=None):
        """Mark contact as replied"""
        self.status = 'replied'
        self.replied_at = timezone.now()
        if user:
            self.assigned_to = user
        self.save(update_fields=['status', 'replied_at', 'assigned_to', 'updated_at'])
    
    def get_attachment_url(self):
        """Get attachment URL if exists"""
        if self.attachment:
            return self.attachment.url
        return None
    
    def get_attachment_name(self):
        """Get attachment filename if exists"""
        if self.attachment:
            return self.attachment.name.split('/')[-1]
        return None
    
    @property
    def days_since_submission(self):
        """Calculate days since submission"""
        return (timezone.now() - self.submitted_at).days
    
    @property
    def is_urgent(self):
        """Check if contact needs urgent attention"""
        return self.priority == 'urgent' or (self.status == 'new' and self.days_since_submission > 2)
    
    @classmethod
    def get_unread_count(cls):
        """Get count of unread contacts"""
        return cls.objects.filter(status='new').count()
    
    @classmethod
    def get_pending_count(cls):
        """Get count of contacts pending reply"""
        return cls.objects.filter(status__in=['new', 'read']).count()


class ContactActivity(models.Model):
    """Model for tracking contact-related activities."""
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contact_activities'
    )
    action = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Contact Activity'
        verbose_name_plural = 'Contact Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.contact.name}"
