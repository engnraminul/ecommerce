"""
Integration utilities for incomplete orders with cart system
"""
from django.utils import timezone
from .models import IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress
from .services import IncompleteOrderService


def create_incomplete_order_from_cart(request, cart, customer_data=None, shipping_data=None, abandonment_reason=''):
    """
    Create an incomplete order from a cart instance
    
    Args:
        request: Django request object
        cart: Cart instance
        customer_data: Dict with customer information
        shipping_data: Dict with shipping address information  
        abandonment_reason: Reason for abandonment
    
    Returns:
        IncompleteOrder instance
    """
    # Convert cart items to the format expected by IncompleteOrderService
    cart_items = []
    for cart_item in cart.items.all():
        cart_items.append({
            'product_id': cart_item.product.id,
            'variant_id': cart_item.variant.id if cart_item.variant else None,
            'quantity': cart_item.quantity,
            'unit_price': cart_item.product.price
        })
    
    # Create incomplete order using the service
    incomplete_order = IncompleteOrderService.create_from_cart(
        request, cart_items, customer_data, shipping_data
    )
    
    # Mark as abandoned if reason provided
    if abandonment_reason:
        incomplete_order.mark_as_abandoned(abandonment_reason)
    
    return incomplete_order


def restore_cart_from_incomplete_order(request, incomplete_order):
    """
    Restore cart from an incomplete order
    
    Args:
        request: Django request object
        incomplete_order: IncompleteOrder instance
    
    Returns:
        Cart instance or None
    """
    from cart.models import Cart, CartItem
    
    # Get or create cart
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_key)
    
    # Clear existing cart items
    cart.clear()
    
    # Add items from incomplete order
    for incomplete_item in incomplete_order.items.all():
        if incomplete_item.product.is_active and incomplete_item.product.stock_quantity > 0:
            CartItem.objects.create(
                cart=cart,
                product=incomplete_item.product,
                variant=incomplete_item.variant,
                quantity=min(incomplete_item.quantity, incomplete_item.product.stock_quantity)
            )
    
    return cart


def track_cart_abandonment_on_exit(request):
    """
    Track cart abandonment when user leaves the site
    Call this from JavaScript before page unload
    
    Args:
        request: Django request object
    
    Returns:
        IncompleteOrder instance or None
    """
    from cart.models import Cart
    
    try:
        # Get user's cart
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:
            session_key = request.session.session_key
            if session_key:
                cart = Cart.objects.get(session_id=session_key)
            else:
                return None
        
        # Only create incomplete order if cart has items
        if cart.items.exists():
            return create_incomplete_order_from_cart(
                request, cart, abandonment_reason='Browser/tab closed'
            )
    
    except Cart.DoesNotExist:
        pass
    
    return None


def auto_save_cart_as_incomplete_order(request, stage='cart'):
    """
    Automatically save cart as incomplete order at different stages
    
    Args:
        request: Django request object
        stage: Stage where this is called ('cart', 'checkout', 'payment', etc.)
    
    Returns:
        IncompleteOrder instance or None
    """
    from cart.models import Cart
    
    stage_reasons = {
        'cart': 'Left cart page',
        'checkout': 'Abandoned at checkout',
        'shipping': 'Abandoned at shipping',
        'payment': 'Abandoned at payment',
        'review': 'Abandoned at order review'
    }
    
    try:
        # Get user's cart
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:
            session_key = request.session.session_key
            if session_key:
                cart = Cart.objects.get(session_id=session_key)
            else:
                return None
        
        # Only create incomplete order if cart has items
        if cart.items.exists():
            # Check if we already have a recent incomplete order for this cart
            existing_incomplete = IncompleteOrder.objects.filter(
                user=request.user if request.user.is_authenticated else None,
                session_id=request.session.session_key if not request.user.is_authenticated else None,
                status__in=['pending', 'abandoned'],
                created_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).first()
            
            if existing_incomplete:
                # Update existing incomplete order
                existing_incomplete.abandonment_reason = stage_reasons.get(stage, f'Abandoned at {stage}')
                existing_incomplete.save()
                return existing_incomplete
            else:
                # Create new incomplete order
                return create_incomplete_order_from_cart(
                    request, cart, abandonment_reason=stage_reasons.get(stage, f'Abandoned at {stage}')
                )
    
    except Cart.DoesNotExist:
        pass
    
    return None


def get_user_recovery_link(incomplete_order):
    """
    Generate a recovery link for incomplete order
    
    Args:
        incomplete_order: IncompleteOrder instance
    
    Returns:
        Recovery URL string
    """
    from django.conf import settings
    
    # This would be customized based on your frontend URLs
    base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    return f"{base_url}/checkout/recover/{incomplete_order.incomplete_order_id}"


def process_recovery_click(request, incomplete_order_id):
    """
    Process when user clicks on recovery link
    
    Args:
        request: Django request object
        incomplete_order_id: ID of incomplete order
    
    Returns:
        Dict with success status and cart info
    """
    try:
        incomplete_order = IncompleteOrder.objects.get(
            incomplete_order_id=incomplete_order_id,
            status__in=['pending', 'abandoned']
        )
        
        # Restore cart from incomplete order
        cart = restore_cart_from_incomplete_order(request, incomplete_order)
        
        # Log recovery attempt
        from .models import IncompleteOrderHistory
        IncompleteOrderHistory.objects.create(
            incomplete_order=incomplete_order,
            action='recovered',
            details='Customer returned via recovery link',
            created_by_system=True,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Update recovery email logs if applicable
        from .models import RecoveryEmailLog
        RecoveryEmailLog.objects.filter(
            incomplete_order=incomplete_order,
            responded=False
        ).update(
            responded=True,
            response_date=timezone.now()
        )
        
        return {
            'success': True,
            'cart_items': cart.total_items if cart else 0,
            'message': 'Cart restored successfully'
        }
        
    except IncompleteOrder.DoesNotExist:
        return {
            'success': False,
            'message': 'Recovery link expired or invalid'
        }


# Middleware class for automatic cart tracking
class CartAbandonmentTrackingMiddleware:
    """
    Middleware to automatically track cart abandonment
    Add this to MIDDLEWARE in settings.py
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track abandonment on certain conditions
        if hasattr(request, 'user') and request.session.session_key:
            # Check if user is leaving checkout process
            if (request.path.startswith('/checkout/') and 
                response.status_code in [301, 302] and 
                not response.get('Location', '').startswith('/checkout/')):
                
                # User is leaving checkout, save cart as incomplete order
                auto_save_cart_as_incomplete_order(request, 'checkout')
        
        return response