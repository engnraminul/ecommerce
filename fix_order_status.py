#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order

# Find orders with incorrect capitalized status
incorrect_orders = Order.objects.filter(status='Pending')  # Capital P
print(f'Found {incorrect_orders.count()} orders with incorrect capitalization')

for order in incorrect_orders:
    print(f'Fixing order {order.order_number}: {order.status} -> pending')
    order.status = 'pending'  # lowercase
    order.save()

print('Fixed all orders with incorrect capitalization')

# Verify the fix
pending_count = Order.objects.filter(status='pending').count()
print(f'Total pending orders now: {pending_count}')

# Show all pending orders
pending_orders = Order.objects.filter(status='pending').order_by('-created_at')
print('\nAll pending orders:')
for order in pending_orders:
    print(f'  {order.order_number}: {order.status}')