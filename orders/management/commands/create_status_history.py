from django.core.management.base import BaseCommand
from orders.models import Order, OrderStatusHistory
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create status history for existing orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate status history even if it exists',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Define status messages and descriptions
        status_info = {
            'pending': {
                'title': 'Order Placed',
                'description': 'Your order has been received and is being reviewed.',
            },
            'confirmed': {
                'title': 'Order Confirmed',
                'description': 'Your order has been confirmed and payment verified.',
            },
            'processing': {
                'title': 'Processing Order',
                'description': 'Your order is being prepared for shipment.',
            },
            'packed': {
                'title': 'Order Packed',
                'description': 'Your order has been packed and is ready for pickup.',
            },
            'shipped': {
                'title': 'Order Shipped',
                'description': 'Your order is on its way to you.',
            },
            'out_for_delivery': {
                'title': 'Out for Delivery',
                'description': 'Your order is out for delivery and will arrive soon.',
            },
            'delivered': {
                'title': 'Delivered',
                'description': 'Your order has been successfully delivered.',
            },
            'cancelled': {
                'title': 'Order Cancelled',
                'description': 'Your order has been cancelled.',
            },
            'refunded': {
                'title': 'Order Refunded',
                'description': 'Your order has been refunded.',
            },
        }

        orders = Order.objects.all()
        created_count = 0
        updated_count = 0

        for order in orders:
            # Check if order already has status history
            if not force and order.status_history.exists():
                self.stdout.write(
                    self.style.WARNING(f'Order {order.order_number} already has status history. Skipping...')
                )
                continue

            if force:
                # Delete existing status history
                order.status_history.all().delete()

            # Create status history based on order timestamps
            histories_to_create = []

            # 1. Order Placed (created_at)
            info = status_info.get('pending', {})
            histories_to_create.append({
                'status': 'pending',
                'title': info.get('title', 'Order Placed'),
                'description': info.get('description', ''),
                'created_at': order.created_at,
            })

            # 2. Order Confirmed (confirmed_at)
            if order.confirmed_at:
                info = status_info.get('confirmed', {})
                histories_to_create.append({
                    'status': 'confirmed',
                    'title': info.get('title', 'Order Confirmed'),
                    'description': info.get('description', ''),
                    'created_at': order.confirmed_at,
                })

            # 3. Processing (if confirmed and not pending)
            if order.status not in ['pending', 'cancelled'] and order.confirmed_at:
                processing_time = order.confirmed_at + timezone.timedelta(hours=2)
                if processing_time < timezone.now():
                    info = status_info.get('processing', {})
                    histories_to_create.append({
                        'status': 'processing',
                        'title': info.get('title', 'Processing Order'),
                        'description': info.get('description', ''),
                        'created_at': processing_time,
                    })

            # 4. Shipped (shipped_at)
            if order.shipped_at:
                info = status_info.get('shipped', {})
                histories_to_create.append({
                    'status': 'shipped',
                    'title': info.get('title', 'Order Shipped'),
                    'description': info.get('description', ''),
                    'created_at': order.shipped_at,
                })

            # 5. Delivered (delivered_at)
            if order.delivered_at:
                info = status_info.get('delivered', {})
                histories_to_create.append({
                    'status': 'delivered',
                    'title': info.get('title', 'Delivered'),
                    'description': info.get('description', ''),
                    'created_at': order.delivered_at,
                })

            # 6. Current status if different from last added
            current_status_info = status_info.get(order.status, {})
            if not histories_to_create or histories_to_create[-1]['status'] != order.status:
                histories_to_create.append({
                    'status': order.status,
                    'title': current_status_info.get('title', order.get_status_display()),
                    'description': current_status_info.get('description', ''),
                    'created_at': order.updated_at,
                })

            # Create the status history entries
            for history_data in histories_to_create:
                OrderStatusHistory.objects.create(
                    order=order,
                    status=history_data['status'],
                    title=history_data['title'],
                    description=history_data['description'],
                    is_system_generated=True,
                    is_milestone=True,
                    is_customer_visible=True,
                    created_at=history_data['created_at']
                )

            created_count += len(histories_to_create)
            updated_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {len(histories_to_create)} status entries for order {order.order_number}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {updated_count} orders and created {created_count} status history entries.'
            )
        )
