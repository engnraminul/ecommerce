"""
Forms for email configuration and template management.
"""
from django import forms
from django.core.exceptions import ValidationError
from ckeditor.widgets import CKEditorWidget
from .models import EmailConfiguration, EmailTemplate


class EmailConfigurationForm(forms.ModelForm):
    """Form for email configuration settings."""
    
    smtp_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter SMTP password or app password'
        }),
        help_text="For Gmail, use an App Password instead of your regular password",
        required=False  # Allow empty passwords for editing existing configurations
    )
    
    class Meta:
        model = EmailConfiguration
        fields = [
            'name', 'smtp_type', 'smtp_host', 'smtp_port', 'smtp_use_tls', 
            'smtp_use_ssl', 'smtp_username', 'smtp_password', 'from_email', 
            'from_name', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_type': forms.Select(attrs={'class': 'form-control'}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control'}),
            'smtp_username': forms.EmailInput(attrs={'class': 'form-control'}),
            'from_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'from_name': forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smtp_use_ssl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default values based on SMTP type
        if not self.instance.pk:
            self.fields['smtp_type'].initial = 'gmail'
            self.fields['smtp_host'].initial = 'smtp.gmail.com'
            self.fields['smtp_port'].initial = 587
            self.fields['smtp_use_tls'].initial = True
    
    def clean_smtp_password(self):
        """Handle password field for updates."""
        password = self.cleaned_data.get('smtp_password')
        
        # If this is an update and password is empty, keep the existing password
        if self.instance.pk and not password:
            return self.instance.smtp_password
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        smtp_type = cleaned_data.get('smtp_type')
        smtp_host = cleaned_data.get('smtp_host')
        smtp_port = cleaned_data.get('smtp_port')
        smtp_use_tls = cleaned_data.get('smtp_use_tls')
        smtp_use_ssl = cleaned_data.get('smtp_use_ssl')
        
        # Validate Gmail settings
        if smtp_type == 'gmail':
            if smtp_host != 'smtp.gmail.com':
                raise ValidationError("Gmail SMTP host must be 'smtp.gmail.com'")
            if smtp_port not in [587, 465]:
                raise ValidationError("Gmail SMTP port must be 587 (TLS) or 465 (SSL)")
            if smtp_port == 587 and not smtp_use_tls:
                raise ValidationError("Gmail SMTP on port 587 requires TLS")
            if smtp_port == 465 and not smtp_use_ssl:
                raise ValidationError("Gmail SMTP on port 465 requires SSL")
        
        # Validate TLS/SSL settings
        if smtp_use_tls and smtp_use_ssl:
            raise ValidationError("Cannot use both TLS and SSL. Choose one.")
        
        return cleaned_data


class EmailTemplateForm(forms.ModelForm):
    """Form for email template management."""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'template_type', 'subject', 'html_content', 'text_content',
            'is_active', 'send_to_user_email', 'send_to_checkout_email', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'html_content': CKEditorWidget(config_name='default'),
            'text_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_to_user_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_to_checkout_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_template_type(self):
        template_type = self.cleaned_data['template_type']
        
        # Check if template type already exists (for new templates)
        if not self.instance.pk:
            if EmailTemplate.objects.filter(template_type=template_type).exists():
                raise ValidationError(f"A template with type '{template_type}' already exists.")
        
        return template_type


class TestEmailForm(forms.Form):
    """Form for testing email configuration."""
    
    test_email = forms.EmailField(
        label="Test Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address to send test email'
        }),
        help_text="A test email will be sent to this address to verify the configuration."
    )


class EmailTemplatePreviewForm(forms.Form):
    """Form for previewing email templates with sample data."""
    
    template_id = forms.IntegerField(widget=forms.HiddenInput())
    
    # Sample context variables
    user_name = forms.CharField(
        initial="John Doe",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Sample user name for preview"
    )
    
    user_email = forms.EmailField(
        initial="john@example.com",
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text="Sample user email for preview"
    )
    
    order_number = forms.CharField(
        initial="MB1001",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Sample order number for preview"
    )
    
    order_total = forms.DecimalField(
        initial=99.99,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Sample order total for preview"
    )


class BulkEmailForm(forms.Form):
    """Form for sending bulk emails."""
    
    RECIPIENT_CHOICES = [
        ('all_users', 'All Users'),
        ('active_users', 'Active Users Only'),
        ('newsletter_subscribers', 'Newsletter Subscribers'),
        ('recent_customers', 'Recent Customers (Last 30 days)'),
        ('custom', 'Custom Email List'),
    ]
    
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Recipients"
    )
    
    custom_emails = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter email addresses separated by commas or new lines'
        }),
        required=False,
        help_text="Only required if 'Custom Email List' is selected"
    )
    
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select email template"
    )
    
    subject_override = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Leave empty to use template subject"
    )
    
    send_immediately = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send immediately or queue for background processing"
    )
    
    def clean_custom_emails(self):
        recipient_type = self.cleaned_data.get('recipient_type')
        custom_emails = self.cleaned_data.get('custom_emails')
        
        if recipient_type == 'custom' and not custom_emails:
            raise ValidationError("Custom emails are required when 'Custom Email List' is selected.")
        
        if custom_emails:
            # Parse and validate email addresses
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            emails = []
            for line in custom_emails.split('\n'):
                for email in line.split(','):
                    email = email.strip()
                    if email:
                        if not re.match(email_pattern, email):
                            raise ValidationError(f"Invalid email address: {email}")
                        emails.append(email)
            
            return emails
        
        return custom_emails