# Incomplete Orders App

The Incomplete Orders app is designed to track unfinished orders (abandoned carts, pending payments, or partially filled orders) and provides functionality to recover them by converting them into completed orders.

## Features

### ✅ Core Functionality
- **Create & Store Incomplete Orders**: Save user cart sessions as IncompleteOrder when checkout isn't completed
- **Track Recovery Attempts**: Monitor recovery email attempts and customer responses
- **Admin Panel Support**: Full Django admin interface with filtering and bulk actions
- **Convert to Completed Order**: Seamlessly move data from IncompleteOrder to Order model
- **Auto Clean/Expire**: Automatically manage old incomplete orders with configurable retention periods

### ✅ Advanced Features
- **Analytics Dashboard**: Track conversion rates, abandonment patterns, and recovery performance
- **Email Recovery System**: Automated email campaigns for cart recovery
- **Session Tracking**: Support for both authenticated users and guest sessions
- **Integration API**: RESTful API for frontend integration
- **Management Commands**: CLI tools for maintenance and automated tasks

## Installation & Setup

### 1. Add to INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ... your other apps
    'incomplete_orders.apps.IncompleteOrdersConfig',
]
```

### 2. Add URLs
```python
# In your main urls.py
urlpatterns = [
    # ... your other URLs
    path('api/v1/incomplete-orders/', include('incomplete_orders.urls')),
]
```

### 3. Run Migrations
```bash
python manage.py migrate
```

## Quick Start

### Creating an Incomplete Order from Cart
```python
from incomplete_orders.services import IncompleteOrderService

# Create incomplete order from cart
incomplete_order = IncompleteOrderService.create_from_cart(
    request, 
    cart_items,
    customer_data={
        'email': 'customer@example.com',
        'phone': '1234567890'
    }
)
```

### Converting to Complete Order
```python
# Convert incomplete order to complete order
if incomplete_order.can_convert:
    complete_order = incomplete_order.convert_to_order()
    print(f"Created order: {complete_order.order_number}")
```

## Management Commands

### Cleanup Expired Orders
```bash
python manage.py cleanup_incomplete_orders --days=90 --dry-run
```

### Send Recovery Emails
```bash
python manage.py send_recovery_emails --hours-after=2 --max-attempts=3 --dry-run
```

### Update Analytics
```bash
python manage.py update_analytics
```

For detailed documentation, see the integration_examples.py file.