from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid

User = get_user_model()


class Category(models.Model):
    """Product category model"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    
    # Hierarchy support
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subcategories')
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def get_absolute_url(self):
        return f"/category/{self.slug}/"


class Product(models.Model):
    """Main product model"""
    # Basic information
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    
    # Product identification
    sku = models.CharField(max_length=100, unique=True, blank=True)
    barcode = models.CharField(max_length=50, blank=True)
    
    # Category and relationships
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    track_inventory = models.BooleanField(default=True)
    
    # Product status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_digital = models.BooleanField(default=False)
    
    # Physical attributes
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=100, blank=True, help_text="Length x Width x Height")
    
    # Shipping options
    SHIPPING_TYPE_CHOICES = [
        ('free', 'Free Shipping'),
        ('standard', 'Shipping with Charge (Dhaka: 70 Tk, Outside: 120 Tk)'),
    ]
    
    # Main shipping option (Free OR Paid)
    shipping_type = models.CharField(
        max_length=20, 
        choices=SHIPPING_TYPE_CHOICES, 
        default='standard',
        help_text="Select main shipping option: Free OR Shipping with Charge"
    )
    
    # Express shipping checkbox (additional option)
    has_express_shipping = models.BooleanField(
        default=False,
        help_text="Check to enable Express Shipping"
    )
    
    # Custom shipping costs (optional overrides)
    custom_shipping_dhaka = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Custom shipping cost for Dhaka (leave blank to use default 70 Tk)"
    )
    custom_shipping_outside = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Custom shipping cost outside Dhaka (leave blank to use default 120 Tk)"
    )
    custom_express_shipping = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Custom express shipping cost for Dhaka (leave blank to use default 150 Tk)"
    )
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"PROD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def is_available(self):
        """Check if product is available (active and in stock)"""
        return self.is_active and self.is_in_stock
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if product is low in stock"""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if compare_price is set"""
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
        return 0
    
    @property
    def review_count(self):
        """Count of approved reviews"""
        return self.reviews.filter(is_approved=True).count()
    
    def get_shipping_cost(self, location='dhaka', shipping_type=None):
        """
        Calculate shipping cost based on product shipping type and location
        location: 'dhaka' or 'outside'
        shipping_type: 'free', 'standard', or 'express' (if None, uses product default)
        """
        if shipping_type is None:
            shipping_type = self.shipping_type
            
        if shipping_type == 'free':
            return 0
        
        elif shipping_type == 'standard':
            if location == 'dhaka':
                return self.custom_shipping_dhaka or 70
            else:  # outside dhaka
                return self.custom_shipping_outside or 120
        
        elif shipping_type == 'express':
            if location == 'dhaka':
                return self.custom_express_shipping or 150
            else:  # express only available in Dhaka
                return None  # Express not available outside Dhaka
        
        return 0
    
    def is_express_available(self, location='dhaka'):
        """Check if express shipping is available for this product and location"""
        return self.has_express_shipping and location == 'dhaka'
    
    def get_available_shipping_options(self, location='dhaka'):
        """Get all available shipping options for this product and location"""
        options = []
        
        # Add main shipping option (free or standard)
        if self.shipping_type == 'free':
            estimated_days = '1-2 days' if location == 'dhaka' else '2-4 days'
            options.append({
                'type': 'free',
                'name': 'Free Shipping',
                'cost': 0,
                'description': 'Free delivery',
                'estimated_days': estimated_days
            })
        
        elif self.shipping_type == 'standard':
            cost = self.get_shipping_cost(location, 'standard')
            location_name = 'Dhaka City' if location == 'dhaka' else 'Outside Dhaka'
            estimated_days = '1-2 days' if location == 'dhaka' else '2-4 days'
            options.append({
                'type': 'standard',
                'name': f'Standard Shipping ({location_name})',
                'cost': cost,
                'description': f'Regular delivery - {cost} ৳',
                'estimated_days': estimated_days
            })
        
        # Add express shipping option if enabled and location is Dhaka
        if self.has_express_shipping and location == 'dhaka':
            cost = self.get_shipping_cost(location, 'express')
            options.append({
                'type': 'express',
                'name': 'Express Shipping (Same Day)',
                'cost': cost,
                'description': f'Same day delivery - {cost} ৳',
                'estimated_days': 'Same day'
            })
        
        return options
    
    @property
    def default_variant(self):
        """Get the default variant for this product"""
        try:
            return self.variants.filter(is_default=True, is_active=True).first()
        except:
            return None
    
    def get_default_variant_or_first(self):
        """Get default variant, or first active variant if no default is set"""
        default = self.default_variant
        if default:
            return default
        return self.variants.filter(is_active=True).first()


class ProductImage(models.Model):
    """Product image model for multiple images per product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'created_at']
    
    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    """Product variants (size, color, etc.)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    # Variant details
    name = models.CharField(max_length=100)  # e.g., "Red - Large"
    sku = models.CharField(max_length=100, unique=True, blank=True)
    
    # Pricing (can override main product price)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    
    # Inventory for this variant
    stock_quantity = models.PositiveIntegerField(default=0)
    
    # Variant attributes
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=50, blank=True)
    
    # Variant image (for color swatches, size variations, etc.)
    image = models.ImageField(upload_to='variants/', blank=True, null=True)
    
    # Default variant for this product
    is_default = models.BooleanField(default=False, help_text="Mark this as the default variant for the product")
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"{self.product.sku}-{uuid.uuid4().hex[:4].upper()}"
        
        # Ensure only one default variant per product
        if self.is_default:
            # Unset any existing default for this product
            ProductVariant.objects.filter(
                product=self.product, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    @property
    def effective_price(self):
        """Return variant price or fall back to product price"""
        return self.price or self.product.price
    
    @property
    def color_name(self):
        """Extract color name from variant name (first word) or return color code"""
        if self.name:
            # Try to extract color name from the first word of variant name
            words = self.name.split()
            if words:
                return words[0]
        # Fall back to color field if no name or name parsing fails
        return self.color if self.color else None
    
    @property
    def is_in_stock(self):
        """Check if variant is in stock"""
        return self.stock_quantity > 0


class Review(models.Model):
    """Product review model"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    
    is_approved = models.BooleanField(default=False)
    is_verified_purchase = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user']  # One review per user per product
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"


class Wishlist(models.Model):
    """User wishlist model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
