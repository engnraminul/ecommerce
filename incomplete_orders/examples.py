"""
Incomplete Orders Integration Examples

This file shows how to integrate the incomplete_orders app with your existing ecommerce system.
"""

# Example 1: Integration with Cart Views
# Add this to your cart/views.py

from incomplete_orders.utils import (
    create_incomplete_order_from_cart,
    track_checkout_abandonment,
    convert_cart_to_incomplete_order_on_error
)


class CheckoutView(generics.CreateAPIView):
    """
    Example checkout view with incomplete order tracking
    """
    
    def post(self, request, *args, **kwargs):
        try:
            # Your existing checkout logic here
            # ...
            
            # If checkout succeeds, clear any incomplete orders for this user
            from incomplete_orders.models import IncompleteOrder
            if request.user.is_authenticated:
                IncompleteOrder.objects.filter(
                    user=request.user,
                    status__in=['pending', 'abandoned']
                ).update(status='converted')
            
            return Response({'success': True})
            
        except PaymentException as e:
            # Create incomplete order when payment fails
            incomplete_order = convert_cart_to_incomplete_order_on_error(
                request, 'payment_failed'
            )
            return Response({
                'error': 'Payment failed',
                'incomplete_order_id': incomplete_order.incomplete_order_id if incomplete_order else None
            }, status=400)
        
        except Exception as e:
            # Create incomplete order for any other checkout error
            convert_cart_to_incomplete_order_on_error(request, 'general')
            return Response({'error': str(e)}, status=500)


# Example 2: JavaScript Integration for Frontend
# Add this JavaScript to track user behavior

javascript_example = """
// Track when user is about to leave checkout page
window.addEventListener('beforeunload', function(e) {
    if (window.location.pathname.includes('/checkout/')) {
        // Send beacon to track abandonment
        navigator.sendBeacon('/api/v1/incomplete-orders/track-abandonment/', 
            JSON.stringify({
                stage: 'checkout',
                reason: 'page_leave'
            })
        );
    }
});

// Track scroll behavior to detect engagement
let maxScroll = 0;
window.addEventListener('scroll', function() {
    const scrollPercent = Math.round(
        (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
    );
    maxScroll = Math.max(maxScroll, scrollPercent);
});

// Send engagement data when leaving
window.addEventListener('beforeunload', function() {
    if (maxScroll > 50) { // User was engaged
        navigator.sendBeacon('/api/v1/incomplete-orders/track-engagement/', 
            JSON.stringify({engagement_score: maxScroll})
        );
    }
});
"""


# Example 3: Celery Tasks for Automated Recovery
# Create this in incomplete_orders/tasks.py

from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from .models import IncompleteOrder
from .services import IncompleteOrderService

@shared_task
def send_recovery_emails():
    """
    Celery task to send recovery emails
    Run this every 2 hours
    """
    # Get candidates for first recovery email (2 hours after abandonment)
    first_recovery = IncompleteOrderService.get_recovery_candidates(
        hours_since_creation=2,
        max_attempts=1
    ).filter(recovery_attempts=0)
    
    for order in first_recovery:
        IncompleteOrderService.send_recovery_email(order, 'abandoned_cart')
    
    # Get candidates for second recovery email (24 hours after abandonment)
    second_recovery = IncompleteOrderService.get_recovery_candidates(
        hours_since_creation=24,
        max_attempts=2
    ).filter(recovery_attempts=1)
    
    for order in second_recovery:
        IncompleteOrderService.send_recovery_email(order, 'payment_reminder')
    
    # Get candidates for final recovery email (72 hours after abandonment)
    final_recovery = IncompleteOrderService.get_recovery_candidates(
        hours_since_creation=72,
        max_attempts=3
    ).filter(recovery_attempts=2)
    
    for order in final_recovery:
        IncompleteOrderService.send_recovery_email(order, 'final_reminder')

@shared_task
def cleanup_expired_orders():
    """
    Celery task to clean up expired orders
    Run this daily
    """
    return IncompleteOrderService.auto_expire_orders(days_old=90)

@shared_task
def update_daily_analytics():
    """
    Celery task to update analytics
    Run this daily at midnight
    """
    from .signals import update_daily_analytics
    return update_daily_analytics()


# Example 4: Recovery URL Handler
# Add this to your frontend/views.py

from django.shortcuts import render, get_object_or_404
from incomplete_orders.models import IncompleteOrder
from incomplete_orders.utils import migrate_incomplete_order_to_cart

def recover_cart(request, incomplete_order_id):
    """
    View to handle cart recovery from email links
    """
    incomplete_order = get_object_or_404(
        IncompleteOrder, 
        incomplete_order_id=incomplete_order_id,
        status__in=['pending', 'abandoned']
    )
    
    # Check if order can still be recovered
    if incomplete_order.is_expired:
        return render(request, 'recovery/expired.html', {
            'incomplete_order': incomplete_order
        })
    
    # Migrate items back to cart
    cart = migrate_incomplete_order_to_cart(incomplete_order, request)
    
    # Redirect to checkout with special recovery tracking
    request.session['recovered_order'] = incomplete_order.incomplete_order_id
    
    return render(request, 'recovery/success.html', {
        'cart': cart,
        'incomplete_order': incomplete_order,
        'discount_offer': incomplete_order.recovery_attempts >= 2
    })


# Example 5: Admin Integration
# Add this to your admin.py files for better integration

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from orders.models import Order

class OrderAdmin(admin.ModelAdmin):
    # Add incomplete order tracking to regular orders
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def incomplete_orders_link(self, obj):
        if obj.user:
            count = obj.user.incomplete_orders.count()
            if count > 0:
                url = reverse('admin:incomplete_orders_incompleteorder_changelist')
                return format_html(
                    '<a href="{}?user__id__exact={}">{} incomplete orders</a>',
                    url, obj.user.id, count
                )
        return '-'
    
    incomplete_orders_link.short_description = 'Incomplete Orders'
    
    list_display = ('order_number', 'user', 'status', 'total_amount', 'incomplete_orders_link')


# Example 6: Analytics Integration
# Add this to your dashboard views

from incomplete_orders.models import IncompleteOrderAnalytics
from django.db.models import Sum, Avg

def dashboard_analytics(request):
    """
    Dashboard view with incomplete order analytics
    """
    # Get recent analytics
    recent_analytics = IncompleteOrderAnalytics.objects.order_by('-date')[:30]
    
    # Calculate summary metrics
    summary = recent_analytics.aggregate(
        total_incomplete=Sum('total_incomplete_orders'),
        total_converted=Sum('converted_orders'),
        total_lost_revenue=Sum('total_lost_revenue'),
        total_recovered_revenue=Sum('recovered_revenue'),
        avg_conversion_rate=Avg('conversion_rate')
    )
    
    # Current incomplete orders needing attention
    from incomplete_orders.models import IncompleteOrder
    pending_recovery = IncompleteOrder.objects.filter(
        status__in=['pending', 'abandoned'],
        recovery_attempts__lt=3,
        expires_at__gt=timezone.now()
    ).count()
    
    context = {
        'incomplete_order_summary': summary,
        'recent_analytics': recent_analytics,
        'pending_recovery': pending_recovery,
    }
    
    return render(request, 'dashboard/analytics.html', context)


# Example 7: API Integration
# Add these endpoints to your API

from rest_framework.decorators import api_view
from incomplete_orders.utils import track_checkout_abandonment

@api_view(['POST'])
def track_abandonment(request):
    """
    API endpoint to track cart/checkout abandonment from frontend
    """
    stage = request.data.get('stage', 'unknown')
    reason = request.data.get('reason', '')
    
    incomplete_order = track_checkout_abandonment(request, stage)
    
    if incomplete_order:
        return Response({
            'tracked': True,
            'incomplete_order_id': incomplete_order.incomplete_order_id
        })
    
    return Response({'tracked': False, 'reason': 'No cart items found'})

@api_view(['POST'])
def track_engagement(request):
    """
    Track user engagement during checkout
    """
    engagement_score = request.data.get('engagement_score', 0)
    
    # You can use this data to improve recovery email targeting
    # High engagement users might be more likely to respond to recovery emails
    
    return Response({'recorded': True})


# Example 8: Email Templates
# Create these in templates/emails/

abandoned_cart_template = """
<!-- templates/emails/abandoned_cart.html -->
<html>
<body>
    <h2>Hi {{ customer_name }},</h2>
    
    <p>You left some great items in your cart! Don't miss out on these products:</p>
    
    <div class="cart-items">
        {% for item in items %}
        <div class="item">
            <h3>{{ item.product_name }}</h3>
            <p>Quantity: {{ item.quantity }}</p>
            <p>Price: ${{ item.unit_price }}</p>
        </div>
        {% endfor %}
    </div>
    
    <p><strong>Total: ${{ incomplete_order.total_amount }}</strong></p>
    
    <a href="{{ recovery_url }}" class="btn">Complete Your Order</a>
    
    <p>This cart will expire in {{ days_until_expiry }} days.</p>
</body>
</html>
"""

final_reminder_template = """
<!-- templates/emails/final_reminder.html -->
<html>
<body>
    <h2>Last Chance, {{ customer_name }}!</h2>
    
    <p>Your cart is about to expire. Complete your order now and save 10%!</p>
    
    {% if discount_offer %}
    <div class="discount-offer">
        <h3>Special Offer: {{ discount_offer.percentage }}% Off</h3>
        <p>Use code: <strong>{{ discount_offer.code }}</strong></p>
    </div>
    {% endif %}
    
    <div class="cart-summary">
        <p>{{ total_items }} items worth ${{ incomplete_order.total_amount }}</p>
    </div>
    
    <a href="{{ recovery_url }}" class="btn">Complete Order & Save</a>
</body>
</html>
"""

# Example 9: Webhook Integration
# For tracking email opens, clicks, etc.

@api_view(['POST'])
def email_webhook(request):
    """
    Webhook to track email delivery events
    """
    event_type = request.data.get('event')
    email_id = request.data.get('email_id')  # Your email service ID
    
    try:
        from incomplete_orders.models import RecoveryEmailLog
        email_log = RecoveryEmailLog.objects.get(id=email_id)
        
        if event_type == 'delivered':
            email_log.delivered = True
        elif event_type == 'opened':
            email_log.opened = True
        elif event_type == 'clicked':
            email_log.clicked = True
        
        email_log.save()
        
        return Response({'status': 'updated'})
    
    except RecoveryEmailLog.DoesNotExist:
        return Response({'status': 'not_found'}, status=404)


# Example 10: Management Commands Usage
# Run these commands in your deployment scripts

commands_example = """
# Daily cleanup (add to cron)
python manage.py cleanup_incomplete_orders --days=90

# Send recovery emails (run every 2 hours)
python manage.py send_recovery_emails --hours-after=2 --max-attempts=3

# Update analytics (run daily at midnight)
python manage.py update_analytics

# Dry run to see what would be cleaned up
python manage.py cleanup_incomplete_orders --dry-run

# Send recovery emails with custom settings
python manage.py send_recovery_emails --hours-after=1 --max-attempts=5
"""