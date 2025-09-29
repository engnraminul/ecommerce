from django.core.management.base import BaseCommand
from django.utils import timezone
from incomplete_orders.signals import update_daily_analytics


class Command(BaseCommand):
    help = 'Update daily analytics for incomplete orders'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Update analytics for specific date (YYYY-MM-DD format)'
        )
    
    def handle(self, *args, **options):
        target_date = options.get('date')
        
        if target_date:
            try:
                from datetime import datetime
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                self.stdout.write(f'Updating analytics for {target_date}')
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            target_date = timezone.now().date()
            self.stdout.write(f'Updating analytics for today ({target_date})')
        
        try:
            analytics = update_daily_analytics()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated analytics for {analytics.date}'
                )
            )
            
            # Display summary
            self.stdout.write(f'Total Incomplete Orders: {analytics.total_incomplete_orders}')
            self.stdout.write(f'Abandoned Orders: {analytics.abandoned_orders}')
            self.stdout.write(f'Converted Orders: {analytics.converted_orders}')
            self.stdout.write(f'Conversion Rate: {analytics.conversion_rate}%')
            self.stdout.write(f'Recovery Rate: {analytics.recovery_rate}%')
            self.stdout.write(f'Lost Revenue: ${analytics.total_lost_revenue}')
            self.stdout.write(f'Recovered Revenue: ${analytics.recovered_revenue}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to update analytics: {str(e)}')
            )