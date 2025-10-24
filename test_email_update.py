#!/usr/bin/env python
"""
Simple test to verify email configuration can be updated.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from dashboard.models import EmailConfiguration
from dashboard.email_forms import EmailConfigurationForm


def test_update_email_config():
    """Test updating email configuration."""
    print("=== TESTING EMAIL CONFIGURATION UPDATE ===")
    
    # Get the existing configuration
    config = EmailConfiguration.objects.first()
    if not config:
        print("ERROR: No email configuration found!")
        return False
    
    print(f"Current Config: {config.name}")
    print(f"Current SMTP Username: {config.smtp_username}")
    print(f"Current From Email: {config.from_email}")
    
    # Test updating the configuration
    updated_data = {
        'name': config.name,
        'smtp_type': config.smtp_type,
        'smtp_host': config.smtp_host,
        'smtp_port': config.smtp_port,
        'smtp_use_tls': config.smtp_use_tls,
        'smtp_use_ssl': config.smtp_use_ssl,
        'smtp_username': 'newuser@gmail.com',
        'smtp_password': 'new-secure-password',
        'from_email': 'newuser@gmail.com',
        'from_name': 'Updated Store Name',
        'is_active': True
    }
    
    # Create form and validate
    form = EmailConfigurationForm(data=updated_data, instance=config)
    
    if form.is_valid():
        # Save the updated configuration
        updated_config = form.save()
        print("SUCCESS: Configuration updated successfully!")
        print(f"New SMTP Username: {updated_config.smtp_username}")
        print(f"New From Email: {updated_config.from_email}")
        print(f"New From Name: {updated_config.from_name}")
        return True
    else:
        print("ERROR: Form validation failed!")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
        return False


if __name__ == '__main__':
    success = test_update_email_config()
    if success:
        print("\nSUCCESS: Email configuration system is working correctly!")
    else:
        print("\nWARNING: Email configuration system has issues!")