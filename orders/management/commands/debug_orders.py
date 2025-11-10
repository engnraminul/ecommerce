from django.core.management.base import BaseCommand
from orders.models import Order, ShippingAddress
from django.db.models import Q

class Command(BaseCommand):
    help = 'Debug order tracking issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== ORDER TRACKING DEBUG ==='))
        
        # Check total orders
        total_orders = Order.objects.count()
        self.stdout.write(f'Total orders: {total_orders}')
        
        # Check orders with phone numbers
        orders_with_customer_phone = Order.objects.exclude(customer_phone='').count()
        orders_with_shipping_phone = Order.objects.filter(shipping_address__phone__isnull=False).exclude(shipping_address__phone='').count()
        
        self.stdout.write(f'Orders with customer_phone: {orders_with_customer_phone}')
        self.stdout.write(f'Orders with shipping_address phone: {orders_with_shipping_phone}')
        
        # Show first 5 orders with details
        self.stdout.write('\n=== SAMPLE ORDERS ===')
        orders = Order.objects.select_related('shipping_address').order_by('-created_at')[:5]
        
        for order in orders:
            self.stdout.write(f'\nOrder: {order.order_number}')
            self.stdout.write(f'  Customer Phone: "{order.customer_phone}"')
            self.stdout.write(f'  Customer Email: {order.customer_email}')
            
            if hasattr(order, 'shipping_address') and order.shipping_address:
                self.stdout.write(f'  Shipping Phone: "{order.shipping_address.phone}"')
                self.stdout.write(f'  Shipping Email: "{order.shipping_address.email}"')
            else:
                self.stdout.write('  No shipping address')
        
        # Test phone search with normalization
        from orders.phone_utils import normalize_bangladeshi_phone
        
        test_phones = ['01777173040', '01777-173040', '+8801777173040', '8801777173040']
        self.stdout.write('\n=== PHONE SEARCH TEST ===')
        
        for phone in test_phones:
            normalized = normalize_bangladeshi_phone(phone)
            self.stdout.write(f'\nTesting phone: "{phone}" -> normalized: "{normalized}"')
            
            # Test exact matches with original
            customer_phone_matches = Order.objects.filter(customer_phone=phone).count()
            shipping_phone_matches = Order.objects.filter(shipping_address__phone=phone).count()
            
            self.stdout.write(f'  Original matches - Customer: {customer_phone_matches}, Shipping: {shipping_phone_matches}')
            
            # Test with normalized phone (this is what the fixed view will do)
            normalized_customer_matches = Order.objects.filter(customer_phone=normalized).count()
            normalized_shipping_matches = Order.objects.filter(shipping_address__phone=normalized).count()
            
            self.stdout.write(f'  Normalized matches - Customer: {normalized_customer_matches}, Shipping: {normalized_shipping_matches}')
            
            # Test the Q query from the view with normalized phone
            total_normalized_matches = Order.objects.filter(
                Q(customer_phone=normalized) | Q(shipping_address__phone=normalized)
            ).count()
            self.stdout.write(f'  Total normalized matches: {total_normalized_matches}')