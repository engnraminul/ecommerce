# Incomplete Orders App

A comprehensive Django app for tracking and recovering incomplete/abandoned orders in your ecommerce system.

## 🎯 Features

### Core Functionality
- **Track Incomplete Orders**: Automatically save unfinished orders when customers abandon their carts
- **Recovery System**: Send automated recovery emails to customers
- **Conversion Tracking**: Convert incomplete orders to complete orders
- **Analytics**: Track conversion rates, recovery success, and lost revenue
- **Admin Interface**: Full Django admin integration for managing incomplete orders

### Advanced Features
- **Guest Order Support**: Track both authenticated and guest user orders
- **Multiple Recovery Attempts**: Configurable recovery email sequences
- **Expiration Management**: Auto-expire old incomplete orders
- **History Tracking**: Complete audit trail of all actions
- **Analytics Dashboard**: Detailed insights into abandonment patterns

## 📦 Installation

1. The app is already created in your project. Make sure it's in `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'incomplete_orders.apps.IncompleteOrdersConfig',
]
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Add URLs to your main `urls.py`:
```python
# urls.py
urlpatterns = [
    # ... other patterns
    path('api/v1/incomplete-orders/', include('incomplete_orders.urls')),
]
```

## 🏗️ Models Overview

### IncompleteOrder
The main model that stores incomplete order data:
- Order identification and user info
- Financial information (subtotal, shipping, taxes, etc.)
- Recovery tracking (attempts, last attempt date)
- Browser/device information for analytics
- Conversion tracking

### IncompleteOrderItem
Individual items in incomplete orders:
- Product and variant references
- Quantity and pricing at time of addition
- Product details snapshot for record keeping

### IncompleteShippingAddress
Shipping address information for incomplete orders (optional).

### IncompleteOrderHistory
Complete audit trail of all actions performed on incomplete orders.

### RecoveryEmailLog
Tracks all recovery emails sent, including delivery and engagement metrics.

### IncompleteOrderAnalytics
Daily analytics data for reporting and insights.

## 🚀 Quick Start

### 1. Basic Integration with Cart

```python
from incomplete_orders.utils import create_incomplete_order_from_cart

# In your cart/checkout views
def checkout_view(request):
    try:
        # Your checkout logic here
        pass
    except Exception as e:
        # Save cart as incomplete order when checkout fails
        incomplete_order = create_incomplete_order_from_cart(
            request, 
            abandon_reason="Checkout error occurred"
        )
        # Handle error
```

### 2. Track Cart Abandonment

```python
from incomplete_orders.utils import track_checkout_abandonment

# Track when user leaves checkout
def track_abandonment(request):
    incomplete_order = track_checkout_abandonment(
        request, 
        stage='payment'  # or 'checkout', 'shipping', etc.
    )
```

### 3. Convert Incomplete Order to Complete Order

```python
from incomplete_orders.models import IncompleteOrder

# Convert incomplete order
incomplete_order = IncompleteOrder.objects.get(incomplete_order_id='INC-12345678')
if incomplete_order.can_convert:
    complete_order = incomplete_order.convert_to_order()
    print(f"Created order: {complete_order.order_number}")
```

## 📧 Recovery Email System

### Automated Recovery Sequence

1. **First Email** (2 hours after abandonment): "You left something in your cart"
2. **Second Email** (24 hours): "Complete your purchase"  
3. **Final Email** (72 hours): "Last chance - Special discount offer"

### Send Recovery Email

```python
from incomplete_orders.services import IncompleteOrderService

# Send recovery email
success = IncompleteOrderService.send_recovery_email(
    incomplete_order, 
    email_type='abandoned_cart'
)
```

### Email Types
- `abandoned_cart`: Initial abandonment email
- `payment_reminder`: Payment completion reminder
- `final_reminder`: Final chance with discount offer
- `discount_offer`: Special discount email

## 🎛️ Management Commands

### Cleanup Expired Orders
```bash
# Delete orders older than 90 days
python manage.py cleanup_incomplete_orders --days=90

# Dry run to see what would be deleted
python manage.py cleanup_incomplete_orders --dry-run
```

### Send Recovery Emails
```bash
# Send emails to orders abandoned 2+ hours ago
python manage.py send_recovery_emails --hours-after=2 --max-attempts=3

# Dry run to see what emails would be sent
python manage.py send_recovery_emails --dry-run
```

### Update Analytics
```bash
# Update daily analytics
python manage.py update_analytics

# Update analytics for specific date
python manage.py update_analytics --date=2023-12-01
```

## 🔧 API Endpoints

### List Incomplete Orders
```http
GET /api/v1/incomplete-orders/api/incomplete-orders/
```

### Get Statistics
```http
GET /api/v1/incomplete-orders/api/incomplete-orders/statistics/
```

### Convert to Order
```http
POST /api/v1/incomplete-orders/api/incomplete-orders/{id}/convert_to_order/
```

### Mark as Abandoned
```http
POST /api/v1/incomplete-orders/api/incomplete-orders/{id}/mark_abandoned/
Content-Type: application/json

{
    "reason": "Customer called to cancel"
}
```

### Send Recovery Email
```http
POST /api/v1/incomplete-orders/api/incomplete-orders/{id}/send_recovery_email/
Content-Type: application/json

{
    "email_type": "abandoned_cart"
}
```

## 📊 Admin Interface

The app provides a comprehensive Django admin interface:

### IncompleteOrder Admin Features
- List view with customer info, status, total amount, and recovery attempts
- Filtering by status, date, recovery attempts
- Search by order ID, customer email, username
- Bulk actions to convert orders or send recovery emails
- Inline editing of items and shipping address
- Complete history tracking

### Analytics Admin
- Daily analytics with conversion rates and recovery metrics
- Summary statistics in changelist view
- Date-based filtering

## 🔄 Integration Examples

### Frontend JavaScript Tracking
```javascript
// Track when user is about to leave checkout
window.addEventListener('beforeunload', function(e) {
    if (window.location.pathname.includes('/checkout/')) {
        navigator.sendBeacon('/api/v1/incomplete-orders/track-abandonment/', 
            JSON.stringify({
                stage: 'checkout',
                reason: 'page_leave'
            })
        );
    }
});
```

### Cart Recovery URL Handler
```python
def recover_cart(request, incomplete_order_id):
    incomplete_order = get_object_or_404(
        IncompleteOrder, 
        incomplete_order_id=incomplete_order_id
    )
    
    # Migrate items back to cart
    cart = migrate_incomplete_order_to_cart(incomplete_order, request)
    
    # Redirect to checkout
    return redirect('checkout')
```

### Email Template Context
```html
<!-- Recovery email template -->
<h2>Hi {{ customer_name }},</h2>
<p>You left {{ total_items }} items in your cart worth ${{ incomplete_order.total_amount }}!</p>

<div class="items">
    {% for item in items %}
    <div>{{ item.quantity }}x {{ item.product_name }} - ${{ item.total_price }}</div>
    {% endfor %}
</div>

<a href="{{ recovery_url }}">Complete Your Order</a>

{% if discount_offer %}
<p>Use code {{ discount_offer.code }} for {{ discount_offer.percentage }}% off!</p>
{% endif %}
```

## ⚙️ Configuration Options

### Settings
Add these to your Django settings:

```python
# Incomplete Orders Settings
INCOMPLETE_ORDER_EXPIRY_DAYS = 30  # Default: 30 days
INCOMPLETE_ORDER_MAX_RECOVERY_ATTEMPTS = 3  # Default: 3 attempts
INCOMPLETE_ORDER_RECOVERY_INTERVALS = [2, 24, 72]  # Hours between attempts

# Email settings for recovery
DEFAULT_FROM_EMAIL = 'noreply@yourstore.com'
FRONTEND_URL = 'https://yourstore.com'  # For recovery URLs
```

### Celery Tasks (Optional)
For automated processing, add these Celery tasks:

```python
# celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('ecommerce')

app.conf.beat_schedule = {
    'send-recovery-emails': {
        'task': 'incomplete_orders.tasks.send_recovery_emails',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    'cleanup-expired-orders': {
        'task': 'incomplete_orders.tasks.cleanup_expired_orders',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
    },
    'update-analytics': {
        'task': 'incomplete_orders.tasks.update_daily_analytics',
        'schedule': crontab(minute=0, hour=1),  # Daily at 1 AM
    },
}
```

## 📈 Analytics & Reporting

### Key Metrics Tracked
- **Conversion Rate**: Percentage of incomplete orders that convert
- **Recovery Rate**: Percentage of recovery emails that lead to conversion
- **Lost Revenue**: Total value of abandoned orders
- **Recovered Revenue**: Total value of converted orders
- **Average Days to Abandon**: Time before users abandon carts

### Dashboard Integration
```python
def dashboard_view(request):
    from incomplete_orders.models import IncompleteOrderAnalytics
    
    analytics = IncompleteOrderAnalytics.objects.order_by('-date')[:30]
    
    context = {
        'incomplete_order_analytics': analytics,
        'conversion_rate': analytics.aggregate(Avg('conversion_rate'))['conversion_rate__avg'],
        'total_lost_revenue': analytics.aggregate(Sum('total_lost_revenue'))['total_lost_revenue__sum'],
    }
    
    return render(request, 'dashboard.html', context)
```

## 🧪 Testing

Run the included tests:

```bash
# Run all incomplete orders tests
python manage.py test incomplete_orders

# Run specific test classes
python manage.py test incomplete_orders.tests.IncompleteOrderModelTest
python manage.py test incomplete_orders.tests.IncompleteOrderAPITest
```

## 🔒 Security Considerations

1. **User Isolation**: Users can only access their own incomplete orders
2. **Session Security**: Guest orders are tied to session IDs
3. **Expiry Management**: Orders automatically expire after configured time
4. **Staff Permissions**: Admin actions require staff permissions

## 🤝 Integration with Existing Orders

The app seamlessly integrates with your existing Order model:

1. **Data Structure**: Mirrors your Order/OrderItem structure
2. **Conversion**: One-click conversion to complete orders
3. **History**: Maintains link between incomplete and complete orders
4. **Analytics**: Tracks conversion success rates

## 📝 Best Practices

1. **Set Appropriate Expiry**: 30-90 days depending on your business
2. **Limit Recovery Attempts**: 3-5 attempts to avoid spam
3. **Personalize Emails**: Use customer data and purchase history
4. **Monitor Analytics**: Track and optimize conversion rates
5. **Clean Up Regularly**: Remove expired orders to maintain performance

## 🐛 Troubleshooting

### Common Issues

1. **Migration Errors**: Ensure all dependencies are migrated first
2. **Import Errors**: Check that serializer imports match your products app
3. **Permission Errors**: Verify user permissions for API endpoints
4. **Email Delivery**: Configure proper email backend in settings

### Debug Mode

Enable debug logging:
```python
LOGGING = {
    'loggers': {
        'incomplete_orders': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## 🚀 Production Deployment

1. **Database Indexes**: The app includes optimized indexes for performance
2. **Celery Setup**: Use Celery for automated tasks in production
3. **Email Service**: Integrate with proper email service (SendGrid, Mailgun, etc.)
4. **Monitoring**: Set up alerts for high abandonment rates
5. **Backup**: Include incomplete orders in your backup strategy

## 📄 License

This code is provided as part of your ecommerce system. Modify and use as needed for your business requirements.

---

For more examples and advanced usage, see the `examples.py` file in the app directory.