from django.core.management.base import BaseCommand
from django.core.cache import caches, cache
from utils.cache_utils import get_cache_manager, warm_homepage_cache, warm_product_caches


class Command(BaseCommand):
    help = 'Manage Redis cache operations'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['clear', 'warm', 'status', 'clear_products', 'clear_sessions'],
            help='Cache action to perform'
        )
        parser.add_argument(
            '--cache',
            type=str,
            default='all',
            choices=['all', 'default', 'products', 'sessions'],
            help='Which cache to operate on'
        )

    def handle(self, *args, **options):
        action = options['action']
        cache_type = options['cache']

        if action == 'clear':
            self.clear_cache(cache_type)
        elif action == 'warm':
            self.warm_cache()
        elif action == 'status':
            self.show_status()
        elif action == 'clear_products':
            self.clear_product_cache()
        elif action == 'clear_sessions':
            self.clear_session_cache()

    def clear_cache(self, cache_type):
        """Clear specified cache"""
        cache_manager = get_cache_manager()
        
        if cache_type == 'all':
            try:
                cache_manager.clear_all_caches()
                self.stdout.write(
                    self.style.SUCCESS('Successfully cleared all caches')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error clearing all caches: {str(e)}')
                )
        else:
            try:
                target_cache = caches[cache_type]
                target_cache.clear()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully cleared {cache_type} cache')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error clearing {cache_type} cache: {str(e)}')
                )

    def warm_cache(self):
        """Warm up cache with common data"""
        try:
            self.stdout.write('Warming up homepage cache...')
            warm_homepage_cache()
            
            self.stdout.write('Warming up product caches...')
            warm_product_caches()
            
            self.stdout.write(
                self.style.SUCCESS('Successfully warmed up caches')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error warming cache: {str(e)}')
            )

    def show_status(self):
        """Show cache status"""
        try:
            # Test default cache
            cache.set('test_key', 'test_value', 10)
            if cache.get('test_key') == 'test_value':
                self.stdout.write('✓ Default cache: Working (Database)')
                cache.delete('test_key')
            else:
                self.stdout.write('✗ Default cache: Not working')

            # Test product cache
            try:
                product_cache = caches['products']
                product_cache.set('test_key', 'test_value', 10)
                if product_cache.get('test_key') == 'test_value':
                    self.stdout.write('✓ Product cache: Working (Database)')
                    product_cache.delete('test_key')
                else:
                    self.stdout.write('✗ Product cache: Not working')
            except Exception as e:
                self.stdout.write(f'⚠ Product cache: {str(e)}')

            # Test session cache
            try:
                session_cache = caches['sessions']
                session_cache.set('test_key', 'test_value', 10)
                if session_cache.get('test_key') == 'test_value':
                    self.stdout.write('✓ Session cache: Working (Database)')
                    session_cache.delete('test_key')
                else:
                    self.stdout.write('✗ Session cache: Not working')
            except Exception as e:
                self.stdout.write(f'⚠ Session cache: Using database sessions (OK)')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking cache status: {str(e)}')
            )

    def clear_product_cache(self):
        """Clear only product-related caches"""
        product_cache = caches['products']
        product_cache.clear()
        
        # Also clear product keys from default cache
        product_keys = [
            'featured_products',
            'popular_products',
            'homepage_data',
        ]
        
        for key in product_keys:
            cache.delete(key)
            
        self.stdout.write(
            self.style.SUCCESS('Successfully cleared product caches')
        )

    def clear_session_cache(self):
        """Clear session cache"""
        session_cache = caches['sessions']
        session_cache.clear()
        self.stdout.write(
            self.style.SUCCESS('Successfully cleared session cache')
        )