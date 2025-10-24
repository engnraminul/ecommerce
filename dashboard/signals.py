"""
Signals for handling email notifications when order status changes.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone

from orders.models import Order, OrderStatusHistory
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """Track order status changes before saving."""
    if instance.pk:  # Only for existing orders
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# @receiver(post_save, sender=Order)
# def send_order_status_email(sender, instance, created, **kwargs):
#     """Send email notification when order status changes."""
#     if created:
#         # New order created - send confirmation email
#         try:
#             from .email_service import email_service
#             email_service.send_order_status_email(instance, 'confirmed')
#             logger.info(f"Order confirmation email sent for order {instance.order_number}")
#         except Exception as e:
#             logger.error(f"Failed to send order confirmation email for {instance.order_number}: {str(e)}")
#     else:
#         # Existing order updated - check if status changed
#         old_status = getattr(instance, '_old_status', None)
#         if old_status and old_status != instance.status:
#             try:
#                 # Send status change email
#                 from .email_service import email_service
#                 email_service.send_order_status_email(instance, instance.status)
#                 logger.info(f"Order status change email sent for order {instance.order_number}: {old_status} -> {instance.status}")
#             except Exception as e:
#                 logger.error(f"Failed to send order status email for {instance.order_number}: {str(e)}")


@receiver(post_save, sender=OrderStatusHistory)
def send_order_status_history_email(sender, instance, created, **kwargs):
    """Send email notification when order status history is created."""
    if created and instance.is_customer_visible:
        try:
            # Map status history to email template
            status_email_map = {
                'confirmed': 'order_confirmed',
                'processing': None,  # No email for processing
                'packed': None,  # No email for packed
                'ready_for_shipped': None,  # No email for ready to ship
                'shipped': 'order_shipped',
                'out_for_delivery': None,  # No email for out for delivery
                'delivered': 'order_delivered',
                'cancelled': 'order_cancelled',
                'refunded': 'order_cancelled',  # Use same template as cancelled
            }
            
            email_template = status_email_map.get(instance.status)
            if email_template:
                from .email_service import email_service
                email_service.send_order_status_email(instance.order, instance.status)
                logger.info(f"Order status history email sent for order {instance.order.order_number}: {instance.status}")
        except Exception as e:
            logger.error(f"Failed to send order status history email for {instance.order.order_number}: {str(e)}")


# User registration signals
from django.contrib.auth import get_user_model
User = get_user_model()


@receiver(post_save, sender=User)
def send_user_emails(sender, instance, created, **kwargs):
    """Send welcome and activation emails for new users."""
    if created:
        try:
            from .email_service import email_service
            if not instance.is_email_verified and not instance.is_active:
                # Send activation email for new unverified users
                instance.email_verification_sent_at = timezone.now()
                instance.save()
                email_service.send_activation_email(instance)
                logger.info(f"Activation email sent to {instance.email}")
            elif instance.is_active and instance.is_email_verified:
                # Send welcome email for already verified users (admin created)
                email_service.send_welcome_email(instance)
                logger.info(f"Welcome email sent to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send user email for {instance.email}: {str(e)}")


@receiver(user_logged_in)
def send_welcome_on_first_login(sender, request, user, **kwargs):
    """Send welcome email on first login for verified users."""
    if user.is_email_verified and not hasattr(user, '_welcome_sent'):
        try:
            # Check if this is their first login (you might want to track this differently)
            if user.last_login is None or user.date_joined == user.last_login:
                from .email_service import email_service
                email_service.send_welcome_email(user)
                user._welcome_sent = True
                logger.info(f"Welcome email sent to {user.email} on first login")
        except Exception as e:
            logger.error(f"Failed to send welcome email on login for {user.email}: {str(e)}")


# Import timezone here to avoid circular imports
from django.utils import timezone