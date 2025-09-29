#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order
from django.db.models import Count

# Get all orders grouped by status
orders_by_status = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
print('Current orders by status:')
for item in orders_by_status:
    print(f'  {item["status"]}: {item["count"]}')

print(f'\nTotal orders: {Order.objects.count()}')

# Show recent orders with their statuses
recent_orders = Order.objects.order_by('-created_at')[:10]
print('\nRecent orders:')
for order in recent_orders:
    print(f'  {order.order_number}: {order.status}')

# Count pending orders specifically
pending_count = Order.objects.filter(status='pending').count()
print(f'\nExact pending count: {pending_count}')

# Show all pending orders
pending_orders = Order.objects.filter(status='pending').order_by('-created_at')
print('\nPending orders:')
for order in pending_orders:
    print(f'  {order.order_number}: {order.created_at}')