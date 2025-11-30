from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from products.models import Product, Category
from utils.cache_utils import get_cache_manager


@receiver(post_save, sender=Product)
def invalidate_product_cache(sender, instance, created, **kwargs):
    """Invalidate product-related caches when a product is saved"""
    cache_manager = get_cache_manager()
    
    # Clear product-specific caches
    cache_manager.invalidate_product_caches(instance.id)
    
    # Clear homepage cache if it's a featured product
    if instance.is_featured:
        cache_manager.default_cache.delete('homepage_data')
    
    # Clear category-specific caches
    if instance.category:
        cache_manager.invalidate_category_caches(instance.category.id)


@receiver(post_delete, sender=Product)
def clear_product_cache_on_delete(sender, instance, **kwargs):
    """Clear caches when a product is deleted"""
    cache_manager = get_cache_manager()
    cache_manager.invalidate_product_caches(instance.id)
    
    # Clear homepage cache
    cache_manager.default_cache.delete('homepage_data')
    
    # Clear category caches
    if instance.category:
        cache_manager.invalidate_category_caches(instance.category.id)


@receiver(post_save, sender=Category)
def invalidate_category_cache(sender, instance, created, **kwargs):
    """Invalidate category-related caches when a category is saved"""
    cache_manager = get_cache_manager()
    cache_manager.invalidate_category_caches(instance.id)
    
    # Clear all categories cache
    cache_manager.default_cache.delete('all_categories')
    cache_manager.default_cache.delete('categories_list')


@receiver(post_delete, sender=Category)
def clear_category_cache_on_delete(sender, instance, **kwargs):
    """Clear caches when a category is deleted"""
    cache_manager = get_cache_manager()
    cache_manager.invalidate_category_caches(instance.id)
    cache_manager.default_cache.delete('all_categories')
    cache_manager.default_cache.delete('categories_list')