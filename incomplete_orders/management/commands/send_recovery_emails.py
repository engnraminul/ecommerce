from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from incomplete_orders.models import IncompleteOrder, RecoveryEmailLog, IncompleteOrderHistory


class Command(BaseCommand):
    help = 'Send recovery emails to customers with abandoned carts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours-after',
            type=int,
            default=2,
            help='Send emails to orders abandoned X hours ago (default: 2)'
        )
        parser.add_argument(
            '--max-attempts',
            type=int,
            default=3,
            help='Maximum recovery attempts per order (default: 3)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what emails would be sent without actually sending'
        )
    
    def handle(self, *args, **options):
        hours_after = options['hours_after']
        max_attempts = options['max_attempts']
        dry_run = options['dry_run']
        
        cutoff_time = timezone.now() - timedelta(hours=hours_after)
        
        # Find orders that need recovery emails
        orders_to_recover = IncompleteOrder.objects.filter(
            status__in=['pending', 'abandoned'],
            created_at__lte=cutoff_time,
            recovery_attempts__lt=max_attempts,
            expires_at__gt=timezone.now()
        ).exclude(
            customer_email='',
            guest_email=''
        )
        
        count = orders_to_recover.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would send recovery emails to {count} customers'
                )
            )
            
            for order in orders_to_recover[:10]:
                email = order.customer_email or order.guest_email
                self.stdout.write(
                    f'  - {order.incomplete_order_id} to {email} '
                    f'(attempt {order.recovery_attempts + 1})'
                )
            
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            if count == 0:
                self.stdout.write(
                    self.style.SUCCESS('No orders need recovery emails')
                )
            else:
                sent_count = 0
                
                for order in orders_to_recover:
                    try:
                        # Determine email type based on attempts
                        if order.recovery_attempts == 0:
                            email_type = 'abandoned_cart'
                            subject = 'You left something in your cart!'
                        elif order.recovery_attempts == 1:
                            email_type = 'payment_reminder'
                            subject = 'Complete your purchase'
                        else:
                            email_type = 'final_reminder'
                            subject = 'Last chance - Complete your order'
                        
                        email = order.customer_email or order.guest_email
                        
                        # Log the recovery email
                        RecoveryEmailLog.objects.create(
                            incomplete_order=order,
                            email_type=email_type,
                            recipient_email=email,
                            subject=subject
                        )
                        
                        # Increment recovery attempts
                        order.increment_recovery_attempt()
                        
                        # Log in history
                        IncompleteOrderHistory.objects.create(
                            incomplete_order=order,
                            action='recovery_sent',
                            details=f'Recovery email sent: {email_type}',
                            created_by_system=True
                        )
                        
                        sent_count += 1
                        
                        self.stdout.write(
                            f'Sent {email_type} email to {email} for order {order.incomplete_order_id}'
                        )
                        
                        # Here you would integrate with your actual email sending service
                        # For example: send_recovery_email(order, email_type)
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to send email for order {order.incomplete_order_id}: {str(e)}'
                            )
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully sent {sent_count} recovery emails'
                    )
                )