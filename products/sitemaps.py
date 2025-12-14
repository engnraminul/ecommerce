"""
Professional XML Sitemap Generation for Products and Categories

This module provides comprehensive sitemap support for SEO optimization,
following Google's sitemap guidelines and best practices.

Features:
- Product sitemap with images
- Category sitemap with hierarchy support
- Static pages sitemap
- Automatic priority calculation
- Change frequency optimization
- Last modification tracking

Usage:
    Add to urls.py:
    from django.contrib.sitemaps.views import sitemap
    from products.sitemaps import sitemaps
    
    urlpatterns = [
        path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    ]
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category


class ProductSitemap(Sitemap):
    """
    Sitemap for all active products.
    
    Features:
    - Dynamic priority based on product featured status
    - Change frequency based on update patterns
    - Image information for Google Image Sitemap
    - Last modification tracking
    """
    protocol = 'https'
    limit = 1000  # Products per sitemap page
    
    def items(self):
        """Return all active products ordered by most recently updated."""
        return Product.objects.filter(
            is_active=True
        ).select_related('category').prefetch_related('images').order_by('-updated_at')
    
    def lastmod(self, obj):
        """Return the last modification date of the product."""
        return obj.updated_at
    
    def location(self, obj):
        """Return the URL path for the product."""
        return f'/products/{obj.slug}/'
    
    def priority(self, obj):
        """
        Calculate priority based on product attributes.
        
        Priority scale:
        - 1.0: Featured products
        - 0.9: In stock products with reviews
        - 0.8: Regular in-stock products
        - 0.6: Out of stock products
        - 0.5: Default
        """
        if obj.is_featured:
            return 1.0
        if obj.in_stock:
            # Higher priority for products with reviews
            if hasattr(obj, 'reviews') and obj.reviews.filter(is_approved=True).exists():
                return 0.9
            return 0.8
        return 0.6
    
    def changefreq(self, obj):
        """
        Determine change frequency based on update patterns.
        
        - Recently updated (within 7 days): daily
        - Updated within 30 days: weekly
        - Older products: monthly
        """
        if obj.updated_at:
            days_since_update = (timezone.now() - obj.updated_at).days
            if days_since_update <= 7:
                return 'daily'
            elif days_since_update <= 30:
                return 'weekly'
        return 'monthly'


class CategorySitemap(Sitemap):
    """
    Sitemap for all active categories.
    
    Features:
    - Hierarchical category support
    - Priority based on product count
    - Parent categories have higher priority
    """
    protocol = 'https'
    changefreq = 'weekly'
    limit = 500
    
    def items(self):
        """Return all active categories."""
        return Category.objects.filter(
            is_active=True
        ).prefetch_related('products', 'subcategories').order_by('name')
    
    def lastmod(self, obj):
        """Return the last modification date of the category."""
        return obj.updated_at
    
    def location(self, obj):
        """Return the URL path for the category."""
        return f'/category/{obj.slug}/'
    
    def priority(self, obj):
        """
        Calculate priority based on category attributes.
        
        Priority scale:
        - 1.0: Parent categories with many products
        - 0.9: Parent categories
        - 0.8: Categories with products
        - 0.7: Subcategories with products
        - 0.6: Empty categories
        """
        product_count = obj.products.filter(is_active=True).count()
        is_parent = obj.parent is None
        has_subcategories = obj.subcategories.exists()
        
        if is_parent:
            if product_count > 20 or has_subcategories:
                return 1.0
            elif product_count > 0:
                return 0.9
            return 0.8
        else:
            if product_count > 0:
                return 0.7
        return 0.6
    
    def changefreq(self, obj):
        """
        Determine change frequency.
        Categories with more products may change more frequently.
        """
        product_count = obj.products.filter(is_active=True).count()
        if product_count > 50:
            return 'daily'
        elif product_count > 10:
            return 'weekly'
        return 'monthly'


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static pages like home, about, contact, etc.
    """
    protocol = 'https'
    priority = 0.8
    changefreq = 'weekly'
    
    def items(self):
        """Return list of static page names."""
        return [
            'frontend:home',
            'frontend:products',
            'frontend:categories',
            'frontend:about',
            'frontend:reviews',
            'frontend:order_tracking',
        ]
    
    def location(self, item):
        """Return the URL for each static page."""
        return reverse(item)


class ProductImageSitemap(Sitemap):
    """
    Extended sitemap for product images (Google Image Sitemap extension).
    
    Note: This sitemap provides image information that can be used
    with the image sitemap extension for better image SEO.
    """
    protocol = 'https'
    limit = 1000
    
    def items(self):
        """Return products that have images."""
        return Product.objects.filter(
            is_active=True,
            images__isnull=False
        ).select_related('category').prefetch_related('images').distinct().order_by('-updated_at')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/products/{obj.slug}/'
    
    def priority(self, obj):
        """Products with images get higher priority."""
        image_count = obj.images.count()
        if image_count >= 5:
            return 1.0
        elif image_count >= 3:
            return 0.9
        elif image_count >= 1:
            return 0.8
        return 0.7
    
    def changefreq(self, obj):
        return 'weekly'


# Dictionary of all sitemaps for easy registration
sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

# Extended sitemaps including images (optional)
extended_sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
    'product-images': ProductImageSitemap,
}
