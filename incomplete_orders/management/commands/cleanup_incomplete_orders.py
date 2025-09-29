from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from incomplete_orders.models import IncompleteOrder, IncompleteOrderHistory


class Command(BaseCommand):
    help = 'Clean up expired incomplete orders'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=10,
            help='Delete incomplete orders older than this many days (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find expired orders
        expired_orders = IncompleteOrder.objects.filter(
            expires_at__lt=cutoff_date
        )
        
        count = expired_orders.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} incomplete orders older than {days} days'
                )
            )
            
            # Show some examples
            for order in expired_orders[:10]:
                self.stdout.write(f'  - {order.incomplete_order_id} (created: {order.created_at})')
            
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            if count == 0:
                self.stdout.write(
                    self.style.SUCCESS('No expired incomplete orders to delete')
                )
            else:
                # Log deletion in history before deleting
                for order in expired_orders:
                    IncompleteOrderHistory.objects.create(
                        incomplete_order=order,
                        action='deleted',
                        details=f'Automatically deleted after {days} days',
                        created_by_system=True
                    )
                
                expired_orders.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deleted {count} expired incomplete orders'
                    )
                )