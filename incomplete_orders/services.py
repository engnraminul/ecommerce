"""
Service functions for incomplete orders
"""
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from .models import (
    IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress,
    IncompleteOrderHistory, RecoveryEmailLog
)


class IncompleteOrderService:
    """Service class for handling incomplete order operations"""
    
    @staticmethod
    def create_from_cart(request, cart_items, customer_data=None, shipping_data=None):
        """
        Create an incomplete order from cart items
        
        Args:
            request: Django request object
            cart_items: List of cart items or cart item objects
            customer_data: Dict with customer information
            shipping_data: Dict with shipping address information
        
        Returns:
            IncompleteOrder instance
        """
        # Prepare order data
        order_data = {
            'user': request.user if request.user.is_authenticated else None,
            'is_guest_order': not request.user.is_authenticated,
            'session_id': request.session.session_key,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'referrer_url': request.META.get('HTTP_REFERER', ''),
        }
        
        # Add customer data if provided
        if customer_data:
            order_data.update({
                'customer_email': customer_data.get('email', ''),
                'customer_phone': customer_data.get('phone', ''),
                'customer_notes': customer_data.get('notes', ''),
                'guest_email': customer_data.get('email', '') if not request.user.is_authenticated else '',
            })
        
        # Create the incomplete order
        incomplete_order = IncompleteOrder.objects.create(**order_data)
        
        # Add items
        for cart_item in cart_items:
            # Handle both cart objects and dict data
            if hasattr(cart_item, 'product'):
                # Cart object
                IncompleteOrderItem.objects.create(
                    incomplete_order=incomplete_order,
                    product=cart_item.product,
                    variant=getattr(cart_item, 'variant', None),
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product.price
                )
            else:
                # Dict data
                IncompleteOrderItem.objects.create(
                    incomplete_order=incomplete_order,
                    product_id=cart_item['product_id'],
                    variant_id=cart_item.get('variant_id'),
                    quantity=cart_item['quantity'],
                    unit_price=cart_item['unit_price']
                )
        
        # Add shipping address if provided
        if shipping_data:
            IncompleteShippingAddress.objects.create(
                incomplete_order=incomplete_order,
                **shipping_data
            )
        
        # Calculate totals
        incomplete_order.calculate_totals()
        
        return incomplete_order
    
    @staticmethod
    def track_abandonment(request, cart_items, stage='cart', reason=''):
        """
        Track cart abandonment at different stages
        
        Args:
            request: Django request object
            cart_items: List of cart items
            stage: Stage where abandonment occurred
            reason: Reason for abandonment
        
        Returns:
            IncompleteOrder instance or None
        """
        if not cart_items:
            return None
        
        # Create incomplete order
        incomplete_order = IncompleteOrderService.create_from_cart(request, cart_items)
        
        # Set abandonment reason based on stage
        abandonment_reasons = {
            'cart': 'Left cart page',
            'checkout': 'Abandoned at checkout',
            'payment': 'Abandoned at payment',
            'shipping': 'Abandoned at shipping',
            'session_timeout': 'Session timeout',
            'browser_close': 'Browser closed'
        }
        
        abandonment_reason = reason or abandonment_reasons.get(stage, 'Unknown')
        incomplete_order.mark_as_abandoned(abandonment_reason)
        
        return incomplete_order
    
    @staticmethod
    def send_recovery_email(incomplete_order, email_type='abandoned_cart', custom_subject=None):
        """
        Send recovery email to customer
        
        Args:
            incomplete_order: IncompleteOrder instance
            email_type: Type of recovery email
            custom_subject: Custom email subject
        
        Returns:
            Boolean indicating success
        """
        if not incomplete_order.customer_email and not incomplete_order.guest_email:
            return False
        
        recipient_email = incomplete_order.customer_email or incomplete_order.guest_email
        
        # Determine email content based on type
        email_templates = {
            'abandoned_cart': {
                'subject': 'You left something in your cart!',
                'template': 'emails/abandoned_cart.html'
            },
            'payment_reminder': {
                'subject': 'Complete your purchase',
                'template': 'emails/payment_reminder.html'
            },
            'final_reminder': {
                'subject': 'Last chance - Complete your order',
                'template': 'emails/final_reminder.html'
            },
            'discount_offer': {
                'subject': 'Special discount on your cart!',
                'template': 'emails/discount_offer.html'
            }
        }
        
        email_config = email_templates.get(email_type, email_templates['abandoned_cart'])
        subject = custom_subject or email_config['subject']
        
        # Create recovery URL (you'll need to implement this based on your frontend)
        recovery_url = f"{settings.FRONTEND_URL}/checkout/recover/{incomplete_order.incomplete_order_id}"
        
        # Prepare email context
        context = {
            'incomplete_order': incomplete_order,
            'recovery_url': recovery_url,
            'customer_name': incomplete_order.user.get_full_name() if incomplete_order.user else 'Customer',
            'items': incomplete_order.items.all(),
        }
        
        try:
            # Render email content
            html_content = render_to_string(email_config['template'], context)
            
            # Send email using dashboard email service
            from dashboard.email_service import email_service
            
            success = email_service.send_email(
                subject=subject,
                html_content=html_content,
                recipient_email=recipient_email,
                text_content='Please enable HTML to view this email.'
            )
            
            # Log the email
            RecoveryEmailLog.objects.create(
                incomplete_order=incomplete_order,
                email_type=email_type,
                recipient_email=recipient_email,
                subject=subject
            )
            
            # Increment recovery attempts
            incomplete_order.increment_recovery_attempt()
            
            # Log in history
            IncompleteOrderHistory.objects.create(
                incomplete_order=incomplete_order,
                action='recovery_sent',
                details=f'Recovery email sent: {email_type}',
                created_by_system=True
            )
            
            return True
            
        except Exception as e:
            # Log the error
            IncompleteOrderHistory.objects.create(
                incomplete_order=incomplete_order,
                action='recovery_sent',
                details=f'Failed to send recovery email: {str(e)}',
                created_by_system=True
            )
            return False
    
    @staticmethod
    def get_recovery_candidates(hours_since_creation=2, max_attempts=3):
        """
        Get incomplete orders that are candidates for recovery emails
        
        Args:
            hours_since_creation: Hours since order creation
            max_attempts: Maximum recovery attempts
        
        Returns:
            QuerySet of IncompleteOrder instances
        """
        cutoff_time = timezone.now() - timedelta(hours=hours_since_creation)
        
        return IncompleteOrder.objects.filter(
            status__in=['pending', 'abandoned'],
            created_at__lte=cutoff_time,
            recovery_attempts__lt=max_attempts,
            expires_at__gt=timezone.now()
        ).exclude(
            customer_email='',
            guest_email=''
        )
    
    @staticmethod
    def auto_expire_orders(days_old=30):
        """
        Automatically expire old incomplete orders
        
        Args:
            days_old: Days after which orders should expire
        
        Returns:
            Number of expired orders
        """
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        orders_to_expire = IncompleteOrder.objects.filter(
            created_at__lte=cutoff_date,
            status__in=['pending', 'abandoned', 'payment_pending']
        )
        
        count = 0
        for order in orders_to_expire:
            order.status = 'expired'
            order.save()
            
            # Log expiration
            IncompleteOrderHistory.objects.create(
                incomplete_order=order,
                action='expired',
                details=f'Automatically expired after {days_old} days',
                created_by_system=True
            )
            count += 1
        
        return count
    
    @staticmethod
    def convert_to_order(incomplete_order):
        """
        Convert incomplete order to complete order
        
        Args:
            incomplete_order: IncompleteOrder instance
        
        Returns:
            Order instance or raises exception
        """
        if not incomplete_order.can_convert:
            raise ValueError("Cannot convert this incomplete order")
        
        return incomplete_order.convert_to_order()
    
    @staticmethod
    def get_user_incomplete_orders(user=None, session_id=None):
        """
        Get incomplete orders for a user or session
        
        Args:
            user: User instance
            session_id: Session ID for guest users
        
        Returns:
            QuerySet of IncompleteOrder instances
        """
        if user and user.is_authenticated:
            return IncompleteOrder.objects.filter(user=user)
        elif session_id:
            return IncompleteOrder.objects.filter(session_id=session_id, user__isnull=True)
        else:
            return IncompleteOrder.objects.none()


# Utility function for cart integration
def create_incomplete_order_from_session(request):
    """
    Create incomplete order from current session cart
    This can be called when user navigates away or session expires
    """
    # This would integrate with your cart system
    # Example implementation:
    
    # Get cart items from session or database
    cart_items = []  # You'll need to implement this based on your cart system
    
    if cart_items:
        return IncompleteOrderService.create_from_cart(request, cart_items)
    
    return None