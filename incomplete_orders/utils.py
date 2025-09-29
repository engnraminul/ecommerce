"""
Integration utilities between cart and incomplete orders
"""
from django.utils import timezone
from cart.models import Cart, CartItem
from .services import IncompleteOrderService


def create_incomplete_order_from_cart(request, abandon_reason=''):
    """
    Create an incomplete order from user's cart
    
    Args:
        request: Django request object
        abandon_reason: Reason for abandonment
    
    Returns:
        IncompleteOrder instance or None
    """
    # Get user's cart
    cart = None
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            pass
    else:
        # For anonymous users, get cart by session
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_id=session_key)
            except Cart.DoesNotExist:
                pass
    
    if not cart or not cart.items.exists():
        return None
    
    # Convert cart items to format expected by service
    cart_items = []
    for item in cart.items.all():
        cart_items.append({
            'product_id': item.product.id,
            'variant_id': item.variant.id if item.variant else None,
            'quantity': item.quantity,
            'unit_price': item.product.price  # or item.variant.price if variant has price
        })
    
    # Prepare customer data
    customer_data = {}
    if request.user.is_authenticated:
        customer_data = {
            'email': request.user.email,
            'phone': getattr(request.user, 'phone', ''),
        }
    
    # Create incomplete order
    incomplete_order = IncompleteOrderService.create_from_cart(
        request, 
        cart_items, 
        customer_data
    )
    
    # Mark as abandoned if reason provided
    if abandon_reason:
        incomplete_order.mark_as_abandoned(abandon_reason)
    
    return incomplete_order


def track_cart_session_abandonment(request):
    """
    Track when user session expires with items in cart
    Can be called from session middleware or periodic task
    """
    return create_incomplete_order_from_cart(request, 'Session timeout')


def track_checkout_abandonment(request, stage='checkout'):
    """
    Track when user abandons checkout process
    Can be called from checkout views when user navigates away
    """
    abandonment_reasons = {
        'checkout': 'Abandoned at checkout page',
        'shipping': 'Abandoned at shipping page',
        'payment': 'Abandoned at payment page',
        'review': 'Abandoned at order review page'
    }
    
    reason = abandonment_reasons.get(stage, 'Abandoned during checkout')
    return create_incomplete_order_from_cart(request, reason)


def convert_cart_to_incomplete_order_on_error(request, error_type='general'):
    """
    Convert cart to incomplete order when an error occurs during checkout
    
    Args:
        request: Django request object
        error_type: Type of error that occurred
    
    Returns:
        IncompleteOrder instance or None
    """
    error_reasons = {
        'payment_failed': 'Payment processing failed',
        'inventory_error': 'Inventory check failed',
        'shipping_error': 'Shipping calculation error',
        'validation_error': 'Form validation failed',
        'general': 'Checkout error occurred'
    }
    
    reason = error_reasons.get(error_type, 'Unknown error')
    incomplete_order = create_incomplete_order_from_cart(request, reason)
    
    if incomplete_order:
        # Set specific status based on error type
        if error_type == 'payment_failed':
            incomplete_order.status = 'payment_failed'
            incomplete_order.save()
    
    return incomplete_order


def migrate_incomplete_order_to_cart(incomplete_order, request):
    """
    Migrate an incomplete order back to user's cart for recovery
    
    Args:
        incomplete_order: IncompleteOrder instance
        request: Django request object
    
    Returns:
        Cart instance
    """
    # Get or create cart
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key or request.session.create()
        cart, created = Cart.objects.get_or_create(session_id=session_key)
    
    # Clear existing cart items to avoid duplicates
    cart.clear()
    
    # Add items from incomplete order
    for item in incomplete_order.items.all():
        # Check if product/variant still exists and has stock
        if item.product.is_active and item.product.stock_quantity > 0:
            # Check variant stock if applicable
            if item.variant and item.variant.stock_quantity <= 0:
                continue
            
            # Adjust quantity if stock is insufficient
            available_stock = item.variant.stock_quantity if item.variant else item.product.stock_quantity
            quantity = min(item.quantity, available_stock)
            
            if quantity > 0:
                CartItem.objects.create(
                    cart=cart,
                    product=item.product,
                    variant=item.variant,
                    quantity=quantity
                )
    
    # Log recovery in incomplete order history
    from .models import IncompleteOrderHistory
    IncompleteOrderHistory.objects.create(
        incomplete_order=incomplete_order,
        action='recovered',
        details='Customer returned and cart was restored',
        created_by_system=True
    )
    
    return cart


# Middleware to track cart abandonment
class CartAbandonmentMiddleware:
    """
    Middleware to track cart abandonment
    This should be added to your MIDDLEWARE setting
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track if user is leaving site with items in cart
        # This is a basic implementation - you might want to make it more sophisticated
        if hasattr(request, 'session') and request.session.get('leaving_site'):
            create_incomplete_order_from_cart(request, 'Left website')
            # Clear the flag
            del request.session['leaving_site']
        
        return response


# Recovery email templates context processor
def get_recovery_email_context(incomplete_order):
    """
    Get context data for recovery email templates
    
    Args:
        incomplete_order: IncompleteOrder instance
    
    Returns:
        Dictionary with template context
    """
    context = {
        'incomplete_order': incomplete_order,
        'customer_name': incomplete_order.user.get_full_name() if incomplete_order.user else 'Customer',
        'items': incomplete_order.items.all(),
        'total_amount': incomplete_order.total_amount,
        'total_items': incomplete_order.total_items,
        'created_days_ago': incomplete_order.days_since_created,
        'recovery_url': f"/checkout/recover/{incomplete_order.incomplete_order_id}/",
        'discount_offer': None,  # You can add discount logic here
    }
    
    # Add discount offer for multiple attempts
    if incomplete_order.recovery_attempts >= 2:
        context['discount_offer'] = {
            'percentage': 10,
            'code': f'SAVE10-{incomplete_order.incomplete_order_id[:8]}'
        }
    
    return context