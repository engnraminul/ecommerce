"""
Quick Integration Example for Orders App
Add these code snippets to integrate Meta Conversions API with your order system.
"""

# ===== 1. Add to orders/views.py =====

# Add this import at the top
from settings.meta_conversions_api import send_purchase_event, send_initiate_checkout_event

# Example: Order Success View (after payment completed)
def order_success(request, order_id):
    """Order success page with Meta CAPI purchase tracking"""
    try:
        order = Order.objects.get(id=order_id, customer_phone=request.session.get('customer_phone'))
        
        # Prepare order data for Meta CAPI
        order_data = {
            'order_id': order.id,
            'total_amount': float(order.total),
            'currency': 'BDT',
            'items': [
                {
                    'product_id': item.product.id,
                    'quantity': item.quantity,
                    'price': float(item.price)
                } for item in order.orderitem_set.all()
            ]
        }
        
        # Prepare user data
        user_data = {
            'email': getattr(order, 'customer_email', None),
            'phone': getattr(order, 'customer_phone', None),
            'first_name': getattr(order, 'customer_name', '').split()[0] if getattr(order, 'customer_name', None) else None,
            'city': getattr(order, 'city', None),
            'country': 'BD'
        }
        
        # Send purchase event to Meta CAPI
        send_purchase_event(request, order_data, user_data)
        
        context = {
            'order': order,
            'success_message': 'Your order has been placed successfully!'
        }
        return render(request, 'orders/success.html', context)
        
    except Order.DoesNotExist:
        return redirect('frontend:home')


# Example: Checkout Initiation (when user starts checkout)
def checkout_view(request):
    """Checkout page with initiate checkout tracking"""
    # ... your existing checkout logic ...
    
    # Get cart data from session/cart
    cart_items = request.session.get('cart', {})
    
    if cart_items:
        # Prepare cart data for Meta CAPI
        cart_data = {
            'currency': 'BDT',
            'items': []
        }
        
        for item_key, item_data in cart_items.items():
            cart_data['items'].append({
                'product_id': item_data.get('product_id'),
                'quantity': item_data.get('quantity', 1),
                'price': float(item_data.get('price', 0))
            })
        
        # Send initiate checkout event
        user_data = {
            'email': request.user.email if request.user.is_authenticated else None
        }
        send_initiate_checkout_event(request, cart_data, user_data)
    
    return render(request, 'frontend/checkout.html', context)


# ===== 2. Add to cart/views.py =====

# Add this import at the top
from settings.meta_conversions_api import send_add_to_cart_event

# Example: Add to Cart API
def add_to_cart_api(request):
    """Add to cart with Meta CAPI tracking"""
    if request.method == 'POST':
        # ... your existing add to cart logic ...
        
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            from products.models import Product
            product = Product.objects.get(id=product_id)
            
            # Your cart logic here...
            
            # Send add to cart event to Meta CAPI
            product_data = {
                'product_id': product.id,
                'product_name': product.name,
                'price': product.price,
                'currency': 'BDT',
                'category': product.category.name if product.category else ''
            }
            
            user_data = {
                'email': request.user.email if request.user.is_authenticated else None
            }
            
            send_add_to_cart_event(request, product_data, user_data)
            
            return JsonResponse({'success': True, 'message': 'Added to cart successfully'})
            
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# ===== 3. Add to frontend/templates/frontend/checkout.html =====

# Add this JavaScript at the bottom of checkout.html (before closing </body>)
"""
<script>
// Meta Pixel Checkout Funnel Tracking
document.addEventListener('DOMContentLoaded', function() {
    // Track checkout initiation
    if (typeof fbq !== 'undefined') {
        fbq('trackCustom', 'InitiateCheckout', {
            page_url: window.location.href,
            checkout_step: 'customer_info'
        });
    }
    
    // Track when user proceeds to shipping
    const shippingSection = document.querySelector('[data-section="shipping"]');
    if (shippingSection) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && typeof fbq !== 'undefined') {
                    fbq('trackCustom', 'CheckoutShipping', {
                        page_url: window.location.href,
                        checkout_step: 'shipping'
                    });
                }
            });
        }, { threshold: 0.5 });
        
        observer.observe(shippingSection);
    }
    
    // Track when user reaches payment section
    const paymentSection = document.querySelector('[data-section="payment"]');
    if (paymentSection) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && typeof fbq !== 'undefined') {
                    fbq('trackCustom', 'CheckoutPayment', {
                        page_url: window.location.href,
                        checkout_step: 'payment'
                    });
                }
            });
        }, { threshold: 0.5 });
        
        observer.observe(paymentSection);
    }
    
    // Track payment abandonment
    window.addEventListener('beforeunload', function() {
        const currentSection = getCurrentCheckoutSection();
        if (currentSection === 'payment' && typeof fbq !== 'undefined') {
            fbq('trackCustom', 'PaymentAbandon', {
                page_url: window.location.href
            });
        }
    });
    
    function getCurrentCheckoutSection() {
        if (window.location.hash.includes('payment') || 
            document.querySelector('.payment-section.active')) {
            return 'payment';
        }
        return 'info';
    }
});
</script>
"""


# ===== 4. Add data attributes to checkout.html sections =====

# Replace your checkout sections with these (add data-section attributes):
"""
<!-- Customer Information Section -->
<div class="form-section" data-section="customer">
    <h2 class="section-title">Customer Information</h2>
    <!-- ... your form fields ... -->
</div>

<!-- Shipping Information Section -->  
<div class="form-section" data-section="shipping">
    <h2 class="section-title">Shipping Information</h2>
    <!-- ... your shipping fields ... -->
</div>

<!-- Payment Section -->
<div class="form-section" data-section="payment">
    <h2 class="section-title">Payment Information</h2>
    <!-- ... your payment fields ... -->
</div>
"""


# ===== 5. Settings Configuration =====

"""
After implementing the code above:

1. Go to Dashboard > Settings > Integration Settings
2. Enable Meta Pixel
3. Enter your Meta Pixel ID (from Facebook Events Manager)
4. Enter your Access Token (from Facebook App)
5. Enable these tracking options:
   ✅ Advanced Cart Tracking
   ✅ Checkout Funnel Tracking  
   ✅ Server-Side Conversions API (CAPI)
6. Save settings

Test by:
- Adding products to cart
- Going to checkout
- Completing an order
- Check Facebook Events Manager for events
"""


# ===== 6. Error Handling & Logging =====

import logging
logger = logging.getLogger(__name__)

def safe_meta_tracking(func):
    """Decorator to safely handle Meta CAPI calls"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Meta CAPI error in {func.__name__}: {str(e)}")
            # Continue with normal flow even if tracking fails
            pass
    return wrapper

# Use decorator like this:
@safe_meta_tracking
def track_purchase(request, order_data, user_data):
    send_purchase_event(request, order_data, user_data)