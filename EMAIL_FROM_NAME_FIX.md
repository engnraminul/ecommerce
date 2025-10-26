# Email From Name Fix

## Problem
The email from_name field was not showing correctly in email inboxes. Instead of showing the configured name (e.g., "Manob Bazar"), emails were displaying generic text like "your store".

## Root Cause
1. **Django EmailMultiAlternatives Format Issue**: The `from_email` parameter in `EmailMultiAlternatives` constructor was using the format `"Name <email@domain.com>"`, but this format wasn't being properly parsed by some email clients.

2. **Multiple Email Sending Points**: There were multiple places in the codebase sending emails:
   - `dashboard/email_service.py` - Main email service
   - `incomplete_orders/services.py` - Recovery emails using Django's `send_mail`

## Solution Applied

### 1. Fixed EmailMultiAlternatives Format
**File**: `dashboard/email_service.py`

**Before**:
```python
email = EmailMultiAlternatives(
    subject=subject,
    body=text_content or strip_tags(html_content),
    from_email=f"{self.active_config.from_name} <{self.active_config.from_email}>",
    to=[recipient_email],
    connection=self.get_connection()
)
```

**After**:
```python
email = EmailMultiAlternatives(
    subject=subject,
    body=text_content or strip_tags(html_content),
    from_email=self.active_config.from_email,
    to=[recipient_email],
    connection=self.get_connection()
)

# Set the From header with both name and email
from_header = f"{self.active_config.from_name} <{self.active_config.from_email}>"
email.extra_headers['From'] = from_header

logger.info(f"Sending email with From header: {from_header}")
```

### 2. Updated Incomplete Orders Service
**File**: `incomplete_orders/services.py`

**Before**:
```python
from django.core.mail import send_mail

send_mail(
    subject=subject,
    message='',
    html_message=html_content,
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[recipient_email],
    fail_silently=False,
)
```

**After**:
```python
from dashboard.email_service import email_service

success = email_service.send_email(
    subject=subject,
    html_content=html_content,
    recipient_email=recipient_email,
    text_content='Please enable HTML to view this email.'
)
```

## Benefits
1. **Consistent From Name**: All emails now use the configured from_name from EmailConfiguration model
2. **Centralized Email Handling**: All email sending goes through the dashboard email service
3. **Better Compatibility**: Using `extra_headers['From']` ensures better email client compatibility
4. **Proper Logging**: Added logging to track the from_header being used

## Testing
- Email configuration test functionality automatically uses the fix
- Manual testing confirmed emails are sent successfully
- All email sending points now use the centralized service

## Configuration
The from_name is configured in the Django admin under:
**Dashboard > Email Configurations > [Your Config] > Sender Information > From Name**

Current active configuration shows: "Manob Bazar"