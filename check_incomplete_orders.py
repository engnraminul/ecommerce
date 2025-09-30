import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from incomplete_orders.models import IncompleteOrder
from django.utils import timezone

def check_incomplete_orders():
    print('🔍 Checking for incomplete orders...')
    print()
    
    # Get all incomplete orders
    incomplete_orders = IncompleteOrder.objects.all().order_by('-created_at')
    
    if not incomplete_orders.exists():
        print('📝 No incomplete orders found yet.')
        print('💡 Try filling out the checkout form and then navigating away!')
        return
    
    print(f'📊 Found {incomplete_orders.count()} incomplete order(s):')
    print()
    
    for order in incomplete_orders:
        print(f'🆔 Order ID: {order.incomplete_order_id}')
        print(f'📧 Customer: {order.customer_email or order.guest_email or "No email"}')
        print(f'📱 Phone: {order.customer_phone or "No phone"}')
        print(f'📝 Status: {order.status}')
        print(f'💰 Total: ${order.total_amount}')
        print(f'📦 Items: {order.total_items}')
        print(f'🕐 Created: {order.created_at}')
        print(f'📍 Abandonment: {order.abandonment_reason or "Not specified"}')
        
        if hasattr(order, 'shipping_address') and order.shipping_address:
            addr = order.shipping_address
            print(f'📮 Address: {addr.first_name} {addr.last_name}, {addr.address_line_1}')
        
        print('─' * 50)
    
    print()
    print('✨ Checkout abandonment tracking is working!')

if __name__ == '__main__':
    check_incomplete_orders()