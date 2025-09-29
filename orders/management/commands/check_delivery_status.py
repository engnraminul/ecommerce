from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Order
import requests
from datetime import timedelta


class Command(BaseCommand):
    help = 'Check delivery status for all shipped orders and update status if delivered'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-orders',
            type=int,
            default=50,
            help='Maximum number of orders to check in one run (default: 50)'
        )
        parser.add_argument(
            '--older-than-hours',
            type=int,
            default=1,
            help='Only check orders that were shipped more than X hours ago (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        max_orders = options['max_orders']
        older_than_hours = options['older_than_hours']
        dry_run = options['dry_run']
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timedelta(hours=older_than_hours)
        
        # Get shipped orders with courier IDs that haven't been checked recently
        shipped_orders = Order.objects.filter(
            status='shipped',
            curier_id__isnull=False,
            updated_at__lt=cutoff_time
        ).exclude(curier_id='')[:max_orders]
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {shipped_orders.count()} shipped orders to check')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        updated_count = 0
        error_count = 0
        
        for order in shipped_orders:
            try:
                self.stdout.write(f'Checking order {order.order_number} (Courier ID: {order.curier_id})')
                
                # Make API request to Packzy
                packzy_url = f"https://portal.packzy.com/api/v1/status_by_cid/{order.curier_id}"
                
                response = requests.get(packzy_url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    delivery_status = data.get('status', '').lower()
                    
                    self.stdout.write(f'  Packzy status: {delivery_status}')
                    
                    if delivery_status == 'delivered':
                        if not dry_run:
                            # Update order status
                            order.status = 'delivered'
                            order.curier_status = 'delivered'
                            order.save()
                            
                            # Log the automatic update
                            try:
                                from dashboard.models import AdminActivity
                                AdminActivity.objects.create(
                                    admin_user=None,  # System update
                                    action='auto_updated_to_delivered_from_packzy',
                                    target_model='Order',
                                    target_id=order.id,
                                    details=f'Automatically updated order {order.order_number} to delivered based on Packzy API response'
                                )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f'  Could not log activity: {e}')
                                )
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Order {order.order_number} marked as delivered')
                        )
                        updated_count += 1
                    else:
                        # Update courier status for tracking even if not delivered
                        if not dry_run and delivery_status:
                            order.curier_status = delivery_status
                            order.save()
                        
                        self.stdout.write(f'  - Order {order.order_number} not yet delivered ({delivery_status})')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Failed to get status from Packzy API (HTTP {response.status_code})')
                    )
                    error_count += 1
                    
            except requests.exceptions.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Network error for order {order.order_number}: {e}')
                )
                error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Unexpected error for order {order.order_number}: {e}')
                )
                error_count += 1
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('DELIVERY STATUS CHECK SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Orders checked: {shipped_orders.count()}')
        self.stdout.write(f'Orders updated to delivered: {updated_count}')
        self.stdout.write(f'Errors encountered: {error_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETED - No actual changes were made'))
        else:
            self.stdout.write(self.style.SUCCESS('DELIVERY STATUS CHECK COMPLETED'))