# Cache utility functions for eCommerce project
from django.core.cache import caches, cache
from django.conf import settings
from django.db.models import QuerySet
from django.utils.cache import get_cache_key
from django.http import HttpRequest
import hashlib
import json
from typing import Any, Optional, Union


class CacheManager:
    """Central cache management utility for eCommerce project"""
    
    def __init__(self):
        try:
            # Try to initialize default cache
            self.default_cache = cache
            # Test if cache is working
            self.default_cache.set('test_key', 'test_value', 1)
            self.default_cache.delete('test_key')
        except Exception as e:
            # If cache fails, create a dummy cache
            from django.core.cache.backends.dummy import DummyCache
            self.default_cache = DummyCache('dummy', {})
            
        try:
            self.product_cache = caches['products']
            # Test product cache
            self.product_cache.set('test_key', 'test_value', 1)
            self.product_cache.delete('test_key')
        except Exception:
            self.product_cache = self.default_cache  # Fallback to default
            
        try:
            self.session_cache = caches['sessions']
            # Test session cache
            self.session_cache.set('test_key', 'test_value', 1)
            self.session_cache.delete('test_key')
        except Exception:
            self.session_cache = self.default_cache  # Fallback to default
        
    def get_cache_key(self, key_name: str, **kwargs) -> str:
        """Generate cache key with proper formatting"""
        if key_name in settings.CACHE_KEYS:
            base_key = settings.CACHE_KEYS[key_name]
            if kwargs:
                return base_key.format(**kwargs)
            return base_key
        return key_name
    
    def get_timeout(self, content_type: str) -> int:
        """Get cache timeout for specific content type"""
        return settings.CACHE_TIMEOUTS.get(content_type, 300)
    
    def set_product_cache(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set product-specific cache"""
        try:
            if timeout is None:
                timeout = self.get_timeout('product_detail')
            return self.product_cache.set(key, value, timeout)
        except Exception:
            return False
    
    def get_product_cache(self, key: str, default: Any = None) -> Any:
        """Get product-specific cache"""
        try:
            return self.product_cache.get(key, default)
        except Exception:
            return default
    
    def delete_product_cache(self, key: str) -> bool:
        """Delete product-specific cache"""
        try:
            return self.product_cache.delete(key)
        except Exception:
            return False
    
    def set_page_cache(self, key: str, value: Any, content_type: str = 'home_page') -> bool:
        """Set page-level cache"""
        try:
            timeout = self.get_timeout(content_type)
            return self.default_cache.set(key, value, timeout)
        except Exception:
            return False
    
    def get_page_cache(self, key: str, default: Any = None) -> Any:
        """Get page-level cache"""
        try:
            return self.default_cache.get(key, default)
        except Exception:
            return default
    
    def invalidate_product_caches(self, product_id: int) -> None:
        """Invalidate all caches related to a specific product"""
        keys_to_delete = [
            f'product_detail_{product_id}',
            f'product_reviews_{product_id}',
            f'related_products_{product_id}',
            'featured_products',
            'popular_products',
        ]
        
        for key in keys_to_delete:
            self.default_cache.delete(key)
            self.product_cache.delete(key)
    
    def invalidate_category_caches(self, category_id: int = None) -> None:
        """Invalidate all category-related caches"""
        keys_to_delete = [
            'categories_list',
            'featured_products',
            'home_page_data',
        ]
        
        if category_id:
            keys_to_delete.extend([
                f'category_products_{category_id}',
                f'popular_products_{category_id}',
            ])
        
        for key in keys_to_delete:
            self.default_cache.delete(key)
            self.product_cache.delete(key)
    
    def cache_queryset(self, queryset: QuerySet, cache_key: str, timeout: int = 300) -> QuerySet:
        """Cache a Django QuerySet"""
        cached_data = self.default_cache.get(cache_key)
        
        if cached_data is None:
            # Convert queryset to list to cache it
            cached_data = list(queryset)
            self.default_cache.set(cache_key, cached_data, timeout)
        
        return cached_data
    
    def get_or_set_cache(self, key: str, callable_obj, timeout: int = 300, cache_type: str = 'default') -> Any:
        """Get from cache or set if not exists"""
        target_cache = self.default_cache
        
        if cache_type == 'products':
            target_cache = self.product_cache
        elif cache_type == 'sessions':
            target_cache = self.session_cache
            
        cached_value = target_cache.get(key)
        
        if cached_value is None:
            cached_value = callable_obj()
            target_cache.set(key, cached_value, timeout)
        
        return cached_value
    
    def clear_all_caches(self) -> None:
        """Clear all caches (use with caution)"""
        self.default_cache.clear()
        self.product_cache.clear()
        # Don't clear session cache to avoid logging out users
    
    def get_user_cart_key(self, user_id: Union[int, str]) -> str:
        """Generate cache key for user's cart"""
        return f'user_cart_{user_id}'
    
    def get_user_wishlist_key(self, user_id: Union[int, str]) -> str:
        """Generate cache key for user's wishlist"""
        return f'user_wishlist_{user_id}'
    
    def cache_view_result(self, request: HttpRequest, view_name: str, 
                         result: Any, timeout: int = 300) -> str:
        """Cache view result with request-specific key"""
        cache_key = self._generate_view_cache_key(request, view_name)
        self.default_cache.set(cache_key, result, timeout)
        return cache_key
    
    def get_cached_view_result(self, request: HttpRequest, view_name: str) -> Optional[Any]:
        """Get cached view result"""
        cache_key = self._generate_view_cache_key(request, view_name)
        return self.default_cache.get(cache_key)
    
    def _generate_view_cache_key(self, request: HttpRequest, view_name: str) -> str:
        """Generate cache key for view based on request parameters"""
        # Include relevant request parameters in cache key
        key_data = {
            'view': view_name,
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', 0) if request.user.is_authenticated else 0,
        }
        
        # Add query parameters for GET requests
        if request.method == 'GET' and request.GET:
            key_data['params'] = dict(request.GET)
        
        # Create hash from key data
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f'view_{view_name}_{key_hash}'


# Initialize cache manager (will be initialized after Django setup)
cache_manager = None

def get_cache_manager():
    """Get cache manager instance (lazy loading)"""
    global cache_manager
    if cache_manager is None:
        try:
            cache_manager = CacheManager()
        except Exception as e:
            # If cache initialization fails, create a minimal cache manager
            from django.core.cache.backends.dummy import DummyCache
            dummy_cache = DummyCache('dummy', {})
            
            class DummyCacheManager:
                def __init__(self):
                    self.default_cache = dummy_cache
                    self.product_cache = dummy_cache
                    self.session_cache = dummy_cache
                    
                def get_timeout(self, content_type):
                    return 300  # Default 5 minutes
                    
                def set_page_cache(self, key, value, content_type='home_page'):
                    return False
                    
                def get_page_cache(self, key, default=None):
                    return default
                    
                def set_product_cache(self, key, value, timeout=None):
                    return False
                    
                def get_product_cache(self, key, default=None):
                    return default
                    
                def invalidate_product_caches(self, product_id):
                    pass
                    
                def invalidate_category_caches(self, category_id=None):
                    pass
            
            cache_manager = DummyCacheManager()
    return cache_manager


# Decorator for caching view functions
def cache_view(timeout: int = 300, cache_type: str = 'default', 
               vary_on_user: bool = False, vary_on_params: bool = True):
    """
    Decorator to cache view results
    
    Args:
        timeout: Cache timeout in seconds
        cache_type: Type of cache to use ('default', 'products', 'sessions')
        vary_on_user: Whether to include user in cache key
        vary_on_params: Whether to include request parameters in cache key
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            key_parts = [view_func.__name__]
            
            if vary_on_user and request.user.is_authenticated:
                key_parts.append(f'user_{request.user.id}')
            
            if vary_on_params and request.GET:
                params_hash = hashlib.md5(
                    json.dumps(dict(request.GET), sort_keys=True).encode()
                ).hexdigest()[:8]
                key_parts.append(f'params_{params_hash}')
            
            # Add args and kwargs to key
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f'{k}_{v}' for k, v in kwargs.items()])
            
            cache_key = '_'.join(key_parts)
            
            # Try to get from cache
            manager = get_cache_manager()
            target_cache = manager.default_cache
            if cache_type == 'products':
                target_cache = manager.product_cache
            elif cache_type == 'sessions':
                target_cache = manager.session_cache
            
            cached_result = target_cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute view and cache result
            result = view_func(request, *args, **kwargs)
            target_cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


# Template tag for cache busting
def get_cache_buster():
    """Generate cache buster string for static files"""
    import time
    return str(int(time.time()))


# Cache warming functions
def warm_homepage_cache():
    """Pre-warm homepage cache"""
    from products.models import Product
    from pages.models import Category
    
    # Cache featured products
    featured_products = Product.objects.filter(
        is_featured=True, is_active=True
    ).select_related('category').prefetch_related('images')[:8]
    
    manager = get_cache_manager()
    manager.set_page_cache(
        'featured_products', 
        list(featured_products), 
        'home_page'
    )
    
    # Cache categories
    categories = Category.objects.filter(is_active=True)[:10]
    manager.set_page_cache(
        'categories_list', 
        list(categories), 
        'category_list'
    )


def warm_product_caches():
    """Pre-warm product caches"""
    from products.models import Product
    
    # Cache popular products
    popular_products = Product.objects.filter(
        is_active=True
    ).order_by('-view_count')[:20]
    
    manager = get_cache_manager()
    manager.set_product_cache(
        'popular_products', 
        list(popular_products), 
        manager.get_timeout('product_list')
    )