"""
Incomplete Orders Integration Examples

This file demonstrates how to integrate the incomplete orders system 
with your existing ecommerce application.
"""

# Example 1: Integrating with Cart Views
# Add this to your cart/views.py

from incomplete_orders.cart_integration import (
    create_incomplete_order_from_cart,
    auto_save_cart_as_incomplete_order,
    process_recovery_click
)

class CheckoutView(generics.CreateAPIView):
    """
    Enhanced checkout view with incomplete order tracking
    """
    def post(self, request, *args, **kwargs):
        try:
            # Your existing checkout logic here
            cart = get_user_cart(request)
            
            # Before processing payment, save as incomplete order
            incomplete_order = create_incomplete_order_from_cart(
                request, 
                cart,
                customer_data={
                    'email': request.data.get('email'),
                    'phone': request.data.get('phone'),
                    'notes': request.data.get('notes', '')
                },
                shipping_data=request.data.get('shipping_address', {})
            )
            
            # Try to process payment
            payment_result = process_payment(request.data)
            
            if payment_result['success']:
                # Convert incomplete order to complete order
                complete_order = incomplete_order.convert_to_order()
                cart.clear()  # Clear the cart
                
                return Response({
                    'success': True,
                    'order_number': complete_order.order_number,
                    'order_id': complete_order.id
                })
            else:
                # Payment failed, mark incomplete order accordingly
                incomplete_order.status = 'payment_failed'
                incomplete_order.save()
                
                return Response({
                    'success': False,
                    'message': 'Payment failed',
                    'incomplete_order_id': incomplete_order.incomplete_order_id
                }, status=400)
                
        except Exception as e:
            return Response({'error': str(e)}, status=500)


# Example 2: Cart Recovery Endpoint
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recover_cart(request, incomplete_order_id):
    """
    Recover cart from incomplete order
    """
    result = process_recovery_click(request, incomplete_order_id)
    
    if result['success']:
        return Response({
            'message': result['message'],
            'cart_items': result['cart_items'],
            'redirect_url': '/checkout/'
        })
    else:
        return Response({
            'error': result['message']
        }, status=404)


# Example 3: Automatic Cart Tracking Middleware
# Add this to your middleware settings

class EnhancedCartAbandonmentMiddleware:
    """
    Enhanced middleware for tracking cart abandonment
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track cart abandonment on page transitions
        if self.should_track_abandonment(request, response):
            auto_save_cart_as_incomplete_order(request, self.get_stage(request))
        
        return response
    
    def should_track_abandonment(self, request, response):
        """Determine if we should track abandonment"""
        # Track when leaving checkout or cart pages
        leaving_important_pages = (
            request.path.startswith('/cart/') or 
            request.path.startswith('/checkout/')
        )
        
        # And going to a different section
        redirect_location = response.get('Location', '')
        leaving_flow = (
            response.status_code in [301, 302] and
            not redirect_location.startswith('/cart/') and
            not redirect_location.startswith('/checkout/')
        )
        
        return leaving_important_pages and leaving_flow
    
    def get_stage(self, request):
        """Get the current stage for abandonment tracking"""
        if request.path.startswith('/cart/'):
            return 'cart'
        elif request.path.startswith('/checkout/shipping'):
            return 'shipping'
        elif request.path.startswith('/checkout/payment'):
            return 'payment'
        elif request.path.startswith('/checkout/'):
            return 'checkout'
        return 'unknown'


# Example 4: JavaScript Integration
# Add this to your frontend templates

"""
<!-- Add this JavaScript to track cart abandonment -->
<script>
// Track when user leaves the page with items in cart
window.addEventListener('beforeunload', function(e) {
    if (hasItemsInCart()) {
        // Send request to track abandonment
        navigator.sendBeacon('/api/v1/incomplete-orders/track-abandonment/', 
            JSON.stringify({
                'stage': getCurrentStage(),
                'reason': 'browser_close'
            })
        );
    }
});

// Track timeout abandonment
let abandonmentTimer;
function resetAbandonmentTimer() {
    clearTimeout(abandonmentTimer);
    abandonmentTimer = setTimeout(() => {
        if (hasItemsInCart()) {
            fetch('/api/v1/incomplete-orders/track-abandonment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    'stage': getCurrentStage(),
                    'reason': 'timeout'
                })
            });
        }
    }, 15 * 60 * 1000); // 15 minutes
}

// Reset timer on user activity
document.addEventListener('mousemove', resetAbandonmentTimer);
document.addEventListener('keypress', resetAbandonmentTimer);
document.addEventListener('click', resetAbandonmentTimer);
</script>
"""


# Example 5: Email Template Integration
# Create these templates in your templates/emails/ directory

"""
<!-- templates/emails/abandoned_cart.html -->
<!DOCTYPE html>
<html>
<head>
    <title>You left something in your cart!</title>
</head>
<body>
    <h2>Hi {{ customer_name }},</h2>
    
    <p>You left some great items in your cart. Don't miss out!</p>
    
    <div class="cart-items">
        {% for item in items %}
        <div class="item">
            <h4>{{ item.product_name }}</h4>
            <p>Quantity: {{ item.quantity }}</p>
            <p>Price: ${{ item.unit_price }}</p>
        </div>
        {% endfor %}
    </div>
    
    <p><strong>Total: ${{ incomplete_order.total_amount }}</strong></p>
    
    <a href="{{ recovery_url }}" class="cta-button">
        Complete Your Purchase
    </a>
    
    <p>This link will restore your cart and take you directly to checkout.</p>
</body>
</html>
"""


# Example 6: Management Command Usage
# Run these commands via cron jobs or scheduled tasks

"""
# Daily cleanup of old incomplete orders
python manage.py cleanup_incomplete_orders --days=90

# Send recovery emails
python manage.py send_recovery_emails --hours-after=2 --max-attempts=3

# Update analytics
python manage.py update_analytics

# Dry run to see what would happen
python manage.py cleanup_incomplete_orders --days=90 --dry-run
python manage.py send_recovery_emails --dry-run
"""


# Example 7: Dashboard Integration
# Add these views to your admin dashboard

class IncompleteOrderDashboardView(APIView):
    """
    Dashboard view for incomplete order analytics
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        from incomplete_orders.services import IncompleteOrderService
        from incomplete_orders.models import IncompleteOrder
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        # Get statistics for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        stats = IncompleteOrder.objects.filter(
            created_at__gte=thirty_days_ago
        ).aggregate(
            total_incomplete=Count('id'),
            total_value=Sum('total_amount'),
            abandoned_count=Count('id', filter=Q(status='abandoned')),
            converted_count=Count('id', filter=Q(status='converted')),
            abandoned_value=Sum('total_amount', filter=Q(status='abandoned')),
            recovered_value=Sum('total_amount', filter=Q(status='converted'))
        )
        
        # Calculate rates
        conversion_rate = 0
        if stats['total_incomplete'] > 0:
            conversion_rate = (stats['converted_count'] / stats['total_incomplete']) * 100
        
        # Get recovery candidates
        recovery_candidates = IncompleteOrderService.get_recovery_candidates()
        
        return Response({
            'period': '30 days',
            'total_incomplete_orders': stats['total_incomplete'],
            'total_value': stats['total_value'] or 0,
            'abandoned_count': stats['abandoned_count'],
            'abandoned_value': stats['abandoned_value'] or 0,
            'converted_count': stats['converted_count'],
            'recovered_value': stats['recovered_value'] or 0,
            'conversion_rate': round(conversion_rate, 2),
            'recovery_candidates': recovery_candidates.count(),
            'potential_recovery_value': recovery_candidates.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
        })


# Example 8: Celery Task Integration
# If you're using Celery for background tasks

"""
from celery import shared_task
from incomplete_orders.services import IncompleteOrderService
from incomplete_orders.models import IncompleteOrder

@shared_task
def send_recovery_emails_task():
    '''Send recovery emails to abandoned carts'''
    candidates = IncompleteOrderService.get_recovery_candidates()
    
    sent_count = 0
    for incomplete_order in candidates:
        try:
            success = IncompleteOrderService.send_recovery_email(
                incomplete_order, 
                email_type='abandoned_cart'
            )
            if success:
                sent_count += 1
        except Exception as e:
            # Log error
            print(f"Failed to send recovery email for {incomplete_order.incomplete_order_id}: {e}")
    
    return f"Sent {sent_count} recovery emails"

@shared_task
def cleanup_expired_orders_task():
    '''Clean up expired incomplete orders'''
    count = IncompleteOrderService.auto_expire_orders(days_old=30)
    return f"Expired {count} old incomplete orders"

# Add to your Celery beat schedule:
CELERY_BEAT_SCHEDULE = {
    'send-recovery-emails': {
        'task': 'your_app.tasks.send_recovery_emails_task',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    'cleanup-expired-orders': {
        'task': 'your_app.tasks.cleanup_expired_orders_task',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
    },
}
"""


# Example 9: Frontend React/Vue Component Integration

"""
// React component for cart recovery banner
const CartRecoveryBanner = ({ incompleteOrderId }) => {
    const [isVisible, setIsVisible] = useState(true);
    
    const handleRecover = async () => {
        try {
            const response = await fetch(`/api/v1/incomplete-orders/recover/${incompleteOrderId}/`);
            const data = await response.json();
            
            if (data.success) {
                // Redirect to checkout
                window.location.href = data.redirect_url;
            } else {
                alert(data.error);
                setIsVisible(false);
            }
        } catch (error) {
            console.error('Recovery failed:', error);
        }
    };
    
    if (!isVisible) return null;
    
    return (
        <div className="cart-recovery-banner">
            <p>We saved your cart! Complete your purchase now.</p>
            <button onClick={handleRecover}>
                Recover Cart ({data.cart_items} items)
            </button>
            <button onClick={() => setIsVisible(false)}>×</button>
        </div>
    );
};
"""