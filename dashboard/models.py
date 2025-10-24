from django.db import models
from django.contrib.auth import get_user_model
from ckeditor.fields import RichTextField

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

class Expense(models.Model):
    """Model for tracking business expenses."""
    EXPENSE_TYPE_CHOICES = [
        ('ads', 'Ads'),
        ('courier_poly', 'Courier Poly'),
        ('tape', 'Tape'),
        ('sticker', 'Sticker'),
        ('box', 'Box'),
        ('others', 'Others'),
    ]
    
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='others')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True, help_text="Optional description for the expense")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Expenses'
    
    def __str__(self):
        return f"{self.get_expense_type_display()} - ${self.amount} ({self.created_at.strftime('%Y-%m-%d')})"


class EmailConfiguration(models.Model):
    """Model for storing email SMTP configuration settings."""
    SMTP_TYPE_CHOICES = [
        ('gmail', 'Gmail SMTP'),
        ('business', 'Business SMTP'),
    ]
    
    name = models.CharField(max_length=100, help_text="Configuration name for identification")
    smtp_type = models.CharField(max_length=20, choices=SMTP_TYPE_CHOICES, default='gmail')
    
    # SMTP Settings
    smtp_host = models.CharField(max_length=255, help_text="SMTP server hostname")
    smtp_port = models.IntegerField(default=587, help_text="SMTP server port")
    smtp_use_tls = models.BooleanField(default=True, help_text="Use TLS encryption")
    smtp_use_ssl = models.BooleanField(default=False, help_text="Use SSL encryption")
    
    # Authentication
    smtp_username = models.CharField(max_length=255, help_text="SMTP username (usually email address)")
    smtp_password = models.CharField(max_length=255, help_text="SMTP password or app password")
    
    # Sender Information
    from_email = models.EmailField(help_text="Default sender email address")
    from_name = models.CharField(max_length=255, help_text="Default sender name")
    
    # Configuration status
    is_active = models.BooleanField(default=False, help_text="Use this configuration for sending emails")
    is_verified = models.BooleanField(default=False, help_text="Configuration has been tested and verified")
    
    # Test email settings
    test_email_sent = models.BooleanField(default=False)
    last_test_date = models.DateTimeField(null=True, blank=True)
    test_result = models.TextField(blank=True, help_text="Result of last test email")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Email Configurations'
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_smtp_type_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure only one active configuration
        if self.is_active:
            EmailConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_config(cls):
        """Get the currently active email configuration."""
        return cls.objects.filter(is_active=True).first()


class EmailTemplate(models.Model):
    """Model for storing email templates with rich text content."""
    TEMPLATE_TYPE_CHOICES = [
        ('welcome', 'Welcome Email'),
        ('activation', 'Account Activation'),
        ('password_reset', 'Password Reset'),
        ('order_confirmed', 'Order Confirmed'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('newsletter', 'Newsletter'),
        ('custom', 'Custom Template'),
    ]
    
    name = models.CharField(max_length=100, help_text="Template name for identification")
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, unique=True)
    subject = models.CharField(max_length=255, help_text="Email subject line (supports variables)")
    
    # Email content
    html_content = RichTextField(
        help_text="HTML email content (supports variables like {{user_name}}, {{order_number}}, etc.)"
    )
    text_content = models.TextField(
        blank=True, 
        help_text="Plain text email content (optional, will be auto-generated from HTML if empty)"
    )
    
    # Template settings
    is_active = models.BooleanField(default=True, help_text="Enable this email template")
    send_to_user_email = models.BooleanField(default=True, help_text="Send to user's profile email if logged in")
    send_to_checkout_email = models.BooleanField(default=True, help_text="Send to checkout form email if no user email")
    
    # Available variables for this template
    available_variables = models.TextField(
        blank=True,
        help_text="JSON list of available variables for this template",
        default='[]'
    )
    
    # Template metadata
    description = models.TextField(blank=True, help_text="Description of when this template is used")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Email Templates'
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def get_rendered_subject(self, context=None):
        """Render subject with context variables."""
        if not context:
            return self.subject
        
        try:
            from django.template import Template, Context
            template = Template(self.subject)
            return template.render(Context(context))
        except Exception:
            return self.subject
    
    def get_rendered_content(self, context=None):
        """Render HTML content with context variables."""
        if not context:
            return self.html_content
        
        try:
            from django.template import Template, Context
            template = Template(self.html_content)
            return template.render(Context(context))
        except Exception:
            return self.html_content


class EmailLog(models.Model):
    """Model for logging sent emails."""
    STATUS_CHOICES = [
        ('sent', 'Sent Successfully'),
        ('failed', 'Failed to Send'),
        ('pending', 'Pending'),
    ]
    
    # Email details
    recipient_email = models.EmailField()
    sender_email = models.EmailField()
    subject = models.CharField(max_length=255)
    
    # Template information
    template = models.ForeignKey(
        EmailTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='email_logs'
    )
    
    # Send status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Related objects
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Email configuration used
    email_config = models.ForeignKey(
        EmailConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Email Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_email', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Email to {self.recipient_email} - {self.subject} ({self.status})"


