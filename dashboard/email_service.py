"""
Email service for handling dynamic SMTP configuration and template-based email sending.
"""
import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    User = get_user_model()
else:
    User = None

from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailService:
    """
    Service class for handling email operations with dynamic SMTP configuration.
    """
    
    def __init__(self):
        self.active_config = None
        self._load_active_config()
    
    def _load_active_config(self):
        """Load the active email configuration."""
        try:
            from .models import EmailConfiguration
            self.active_config = EmailConfiguration.get_active_config()
        except Exception:
            # During migrations or if table doesn't exist yet
            self.active_config = None
            logger.warning("Could not load email configuration - database may not be ready")
    
    def get_connection(self):
        """Get email connection using active configuration."""
        if not self.active_config:
            self._load_active_config()
        
        if not self.active_config:
            # Fallback to Django's default email backend
            return get_connection()
        
        # Create connection with custom SMTP settings
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=self.active_config.smtp_host,
            port=self.active_config.smtp_port,
            username=self.active_config.smtp_username,
            password=self.active_config.smtp_password,
            use_tls=self.active_config.smtp_use_tls,
            use_ssl=self.active_config.smtp_use_ssl,
        )
        
        return connection
    
    def send_template_email(
        self,
        template_type: str,
        recipient_email: str,
        context: Dict[str, Any] = None,
        user = None,
        order = None,
        attachments: List = None
    ) -> bool:
        """
        Send an email using a template.
        
        Args:
            template_type: Type of email template to use
            recipient_email: Recipient's email address
            context: Template context variables
            user: User object (optional)
            order: Order object (optional)
            attachments: List of file attachments (optional)
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            from .models import EmailTemplate
            
            # Get email template
            template = EmailTemplate.objects.filter(
                template_type=template_type,
                is_active=True
            ).first()
            
            if not template:
                logger.error(f"No active email template found for type: {template_type}")
                return False
            
            # Prepare context
            if context is None:
                context = {}
            
            # Add default context variables
            context.update({
                'site_name': getattr(settings, 'SITE_NAME', 'Our Store'),
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                'current_year': datetime.now().year,
            })
            
            if user:
                context.update({
                    'user_name': user.first_name or user.username,
                    'user_email': user.email,
                    'user_full_name': f"{user.first_name} {user.last_name}".strip(),
                })
            
            if order:
                context.update({
                    'order_number': order.order_number,
                    'order_total': order.total_amount,
                    'order_status': order.get_status_display(),
                    'order_date': order.created_at,
                })
            
            # Render template content
            subject = template.get_rendered_subject(context)
            html_content = template.get_rendered_content(context)
            
            # Generate text content if not provided
            text_content = template.text_content
            if not text_content:
                text_content = strip_tags(html_content)
            else:
                # Render text content with context
                text_template = Template(text_content)
                text_content = text_template.render(Context(context))
            
            # Send email
            success = self.send_email(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipient_email=recipient_email,
                attachments=attachments
            )
            
            # Log email
            self._log_email(
                template=template,
                recipient_email=recipient_email,
                subject=subject,
                status='sent' if success else 'failed',
                user=user,
                order=order,
                error_message="" if success else "Failed to send email"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending template email: {str(e)}")
            
            # Log failed email
            self._log_email(
                template=template if 'template' in locals() else None,
                recipient_email=recipient_email,
                subject=template_type,
                status='failed',
                user=user,
                order=order,
                error_message=str(e)
            )
            
            return False
    
    def send_email(
        self,
        subject: str,
        html_content: str,
        recipient_email: str,
        text_content: str = None,
        attachments: List = None
    ) -> bool:
        """
        Send a single email.
        
        Args:
            subject: Email subject
            html_content: HTML email content
            recipient_email: Recipient's email address
            text_content: Plain text content (optional)
            attachments: List of file attachments (optional)
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            if not self.active_config:
                logger.error("No active email configuration available")
                return False
            
            # Create email message
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
            
            # Add HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    if hasattr(attachment, 'read'):
                        # File-like object
                        email.attach(
                            attachment.name,
                            attachment.read(),
                            attachment.content_type
                        )
                    elif isinstance(attachment, dict):
                        # Dictionary with filename, content, mimetype
                        email.attach(
                            attachment['filename'],
                            attachment['content'],
                            attachment.get('mimetype', 'application/octet-stream')
                        )
            
            # Send email
            email.send()
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {str(e)}")
            return False
    
    def test_email_configuration(self, config_id: int, test_email: str) -> Dict[str, Any]:
        """
        Test an email configuration by sending a test email.
        
        Args:
            config_id: EmailConfiguration ID to test
            test_email: Email address to send test email to
        
        Returns:
            dict: Test result with success status and message
        """
        try:
            from .models import EmailConfiguration
            
            config = EmailConfiguration.objects.get(id=config_id)
            
            # Temporarily set as active for testing
            old_active = self.active_config
            self.active_config = config
            
            # Send test email
            subject = "Email Configuration Test"
            html_content = """
            <h2>Email Configuration Test</h2>
            <p>This is a test email to verify your email configuration is working correctly.</p>
            <p><strong>Configuration:</strong> {config_name} ({smtp_type})</p>
            <p><strong>SMTP Host:</strong> {smtp_host}:{smtp_port}</p>
            <p><strong>Sent at:</strong> {timestamp}</p>
            """.format(
                config_name=config.name,
                smtp_type=config.get_smtp_type_display(),
                smtp_host=config.smtp_host,
                smtp_port=config.smtp_port,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            success = self.send_email(
                subject=subject,
                html_content=html_content,
                recipient_email=test_email
            )
            
            # Update configuration test status
            config.test_email_sent = True
            config.last_test_date = datetime.now(timezone.utc)
            config.is_verified = success
            
            if success:
                config.test_result = "Test email sent successfully"
                result = {
                    'success': True,
                    'message': 'Test email sent successfully'
                }
            else:
                config.test_result = "Failed to send test email"
                result = {
                    'success': False,
                    'message': 'Failed to send test email'
                }
            
            config.save()
            
            # Restore previous active config
            self.active_config = old_active
            
            return result
            
        except Exception as e:
            from .models import EmailConfiguration
            
            if 'DoesNotExist' in str(type(e)):
                return {
                    'success': False,
                    'message': 'Email configuration not found'
                }
            
            logger.error(f"Error testing email configuration: {str(e)}")
            return {
                'success': False,
                'message': f'Error testing configuration: {str(e)}'
            }
    
    def send_order_status_email(self, order, new_status: str):
        """
        Send order status update email with logic for user vs checkout email.
        
        Args:
            order: Order object
            new_status: New order status
        """
        try:
            # Determine recipient email based on user login status
            recipient_email = None
            
            if order.user and order.user.email:
                # User is logged in, use user's profile email
                recipient_email = order.user.email
            elif order.customer_email:
                # Guest order, use checkout form email
                recipient_email = order.customer_email
            
            if not recipient_email:
                logger.warning(f"No email address found for order {order.order_number}")
                return False
            
            # Map order status to email template type
            status_template_map = {
                'confirmed': 'order_confirmed',
                'shipped': 'order_shipped',
                'delivered': 'order_delivered',
                'cancelled': 'order_cancelled',
            }
            
            template_type = status_template_map.get(new_status)
            if not template_type:
                logger.info(f"No email template configured for status: {new_status}")
                return False
            
            # Send email
            return self.send_template_email(
                template_type=template_type,
                recipient_email=recipient_email,
                user=order.user,
                order=order,
                context={
                    'order': order,
                    'new_status': new_status,
                    'status_display': order.get_status_display(),
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending order status email: {str(e)}")
            return False
    
    def send_welcome_email(self, user):
        """Send welcome email to new user."""
        return self.send_template_email(
            template_type='welcome',
            recipient_email=user.email,
            user=user
        )
    
    def send_activation_email(self, user):
        """Send account activation email."""
        activation_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/verify-email/{user.email_verification_token}/"
        
        return self.send_template_email(
            template_type='activation',
            recipient_email=user.email,
            user=user,
            context={
                'activation_url': activation_url,
                'activation_token': user.email_verification_token,
            }
        )
    
    def send_password_reset_email(self, user):
        """Send password reset email."""
        reset_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/reset-password/{user.password_reset_token}/"
        
        return self.send_template_email(
            template_type='password_reset',
            recipient_email=user.email,
            user=user,
            context={
                'reset_url': reset_url,
                'reset_token': user.password_reset_token,
            }
        )
    
    def _log_email(
        self,
        recipient_email: str,
        subject: str,
        status: str,
        template = None,
        user = None,
        order = None,
        error_message: str = ""
    ):
        """Log email sending attempt."""
        try:
            from .models import EmailLog
            
            sender_email = self.active_config.from_email if self.active_config else "system@example.com"
            
            EmailLog.objects.create(
                recipient_email=recipient_email,
                sender_email=sender_email,
                subject=subject,
                template=template,
                status=status,
                error_message=error_message or "",
                user=user,
                order=order,
                email_config=self.active_config,
                sent_at=datetime.now(timezone.utc) if status == 'sent' else None
            )
        except Exception as e:
            logger.error(f"Error logging email: {str(e)}")


# Global email service instance
email_service = EmailService()