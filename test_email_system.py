#!/usr/bin/env python
"""
Test script for email system functionality.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from dashboard.models import EmailConfiguration, EmailTemplate
from dashboard.email_forms import EmailConfigurationForm, EmailTemplateForm


def test_email_configuration_form():
    """Test email configuration form handling."""
    print("=== TESTING EMAIL CONFIGURATION FORM ===")
    
    # Get the existing configuration
    config = EmailConfiguration.objects.first()
    if not config:
        print("No email configuration found!")
        return
    
    print(f"Original Config: {config.name}")
    print(f"Original SMTP Host: {config.smtp_host}")
    print(f"Original SMTP Username: {config.smtp_username}")
    print(f"Original From Email: {config.from_email}")
    
    # Test form with new data
    form_data = {
        'name': 'Updated Gmail Configuration',
        'smtp_type': 'gmail',
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_use_tls': True,
        'smtp_use_ssl': False,
        'smtp_username': 'updated-email@gmail.com',
        'smtp_password': 'new-app-password',
        'from_email': 'updated-email@gmail.com',
        'from_name': 'Updated Store Name',
        'is_active': True
    }
    
    # Test the form
    form = EmailConfigurationForm(data=form_data, instance=config)
    print(f"\nForm is valid: {form.is_valid()}")
    
    if not form.is_valid():
        print("Form errors:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
    else:
        # Don't save, just test validation
        print("Form validation passed!")
        print("Updated values would be:")
        for field, value in form.cleaned_data.items():
            print(f"  {field}: {value}")


def test_email_template_list():
    """Test email template listing."""
    print("\n=== TESTING EMAIL TEMPLATE LIST ===")
    
    templates = EmailTemplate.objects.all().order_by('template_type', 'name')
    print(f"Total templates found: {templates.count()}")
    
    for template in templates:
        print(f"Template: {template.name}")
        print(f"  Type: {template.template_type}")
        print(f"  Subject: {template.subject}")
        print(f"  Active: {template.is_active}")
        print(f"  Send to user email: {template.send_to_user_email}")
        print(f"  Send to checkout email: {template.send_to_checkout_email}")
        print("  ---")


def test_template_form():
    """Test email template form."""
    print("\n=== TESTING EMAIL TEMPLATE FORM ===")
    
    # Test creating a new template form
    form_data = {
        'name': 'Test Template',
        'template_type': 'test',
        'subject': 'Test Subject',
        'html_content': '<h1>Test Content</h1>',
        'text_content': 'Test Content',
        'is_active': True,
        'send_to_user_email': True,
        'send_to_checkout_email': False,
        'description': 'Test template description'
    }
    
    form = EmailTemplateForm(data=form_data)
    print(f"Form is valid: {form.is_valid()}")
    
    if not form.is_valid():
        print("Form errors:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
    else:
        print("Template form validation passed!")


if __name__ == '__main__':
    print("Testing Email System Components...")
    test_email_configuration_form()
    test_email_template_list()
    test_template_form()
    print("\nTest completed!")