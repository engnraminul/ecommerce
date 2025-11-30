from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup cache tables for database cache backend'

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_REDIS', False):
            self.stdout.write('Setting up database cache tables...')
            
            try:
                # Create cache tables
                call_command('createcachetable', 'cache_table')
                call_command('createcachetable', 'session_cache_table') 
                call_command('createcachetable', 'product_cache_table')
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully created cache tables')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating cache tables: {str(e)}')
                )
        else:
            self.stdout.write(
                self.style.WARNING('Redis is enabled. Database cache tables not needed.')
            )