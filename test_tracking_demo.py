"""
Test script to demonstrate the Professional Order Tracking System
This script will create realistic order status updates to showcase all features.
"""

import os
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order, OrderStatusHistory
from orders.signals import add_tracking_update

def test_professional_tracking():
    """Demonstrate the professional order tracking system"""
    
    print("=== Professional Order Tracking System Demo ===\n")
    
    # Get a test order and reset it to pending
    order = Order.objects.filter(status='pending').first()
    if not order:
        # If no pending orders, reset the first order
        order = Order.objects.first()
        order.status = 'pending'
        order.save()
    
    print(f"Testing with Order: {order.order_number}")
    print(f"Initial Status: {order.status}")
    print(f"Initial Status History Count: {order.status_history.count()}\n")
    
    # Simulate order progression with realistic tracking updates
    tracking_steps = [
        {
            'status': 'processing',
            'updates': [
                {
                    'title': 'Order Being Prepared',
                    'description': 'Your order is being prepared in our warehouse.',
                    'is_milestone': True
                },
                {
                    'title': 'Items Picked',
                    'description': 'All items have been picked from inventory and verified.',
                    'location': 'Warehouse - Bay 3',
                    'is_milestone': False
                }
            ]
        },
        {
            'status': 'shipped',
            'updates': [
                {
                    'title': 'Package Dispatched',
                    'description': 'Your package has been dispatched and is on its way to you.',
                    'tracking_number': 'DHL1234567890',
                    'carrier': 'DHL Express',
                    'carrier_url': 'https://www.dhl.com/track?shipmentId=DHL1234567890',
                    'location': 'DHL Hub - New York',
                    'estimated_delivery': timezone.now() + timedelta(days=2),
                    'is_milestone': True
                },
                {
                    'title': 'In Transit',
                    'description': 'Package is in transit to regional distribution center.',
                    'tracking_number': 'DHL1234567890',
                    'carrier': 'DHL Express',
                    'location': 'Regional Hub - Philadelphia',
                    'is_milestone': False
                }
            ]
        },
        {
            'status': 'out_for_delivery',
            'updates': [
                {
                    'title': 'Out for Delivery',
                    'description': 'Your package is on the delivery truck and will arrive today.',
                    'tracking_number': 'DHL1234567890',
                    'carrier': 'DHL Express',
                    'location': 'Local Delivery Center',
                    'estimated_delivery': timezone.now() + timedelta(hours=4),
                    'is_milestone': True
                }
            ]
        }
    ]
    
    # Apply tracking steps
    for step in tracking_steps:
        print(f"--- Updating to {step['status']} ---")
        
        # Update order status (this triggers automatic status history via signals)
        order.status = step['status']
        order.save()
        
        # Add custom tracking updates
        for update in step['updates']:
            add_tracking_update(
                order=order,
                title=update['title'],
                description=update['description'],
                tracking_number=update.get('tracking_number'),
                carrier=update.get('carrier'),
                carrier_url=update.get('carrier_url'),
                location=update.get('location'),
                estimated_delivery=update.get('estimated_delivery'),
                is_milestone=update['is_milestone']
            )
            print(f"  ✓ Added: {update['title']}")
        
        print(f"  Status History Count: {order.status_history.count()}")
        print()
    
    # Show final tracking history
    print("=== Final Order Tracking History ===")
    for i, history in enumerate(order.status_history.all(), 1):
        status_icon = "🎯" if history.is_milestone else "📝"
        visibility = "👁️" if history.is_customer_visible else "🔒"
        
        print(f"{i}. {status_icon} {visibility} {history.get_display_title()}")
        print(f"   📅 {history.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📝 {history.get_display_description()}")
        
        if history.tracking_number:
            print(f"   📦 Tracking: {history.tracking_number} ({history.carrier})")
        if history.location:
            print(f"   📍 Location: {history.location}")
        if history.estimated_delivery:
            print(f"   ⏰ Est. Delivery: {history.estimated_delivery.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    print(f"🎉 Demo completed! Order {order.order_number} now has {order.status_history.count()} tracking entries.")
    print(f"🌐 Visit: http://127.0.0.1:8000/track-order/?order_number={order.order_number}")
    print(f"🌐 Enhanced: http://127.0.0.1:8000/order-tracking/?order_number={order.order_number}")

if __name__ == "__main__":
    test_professional_tracking()
