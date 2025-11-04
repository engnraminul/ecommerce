from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from products.models import Product, ProductVariant
import uuid

User = get_user_model()


class Cart(models.Model):
    """Shopping cart model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)  # For anonymous users
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous cart {self.session_id}"
    
    @property
    def total_items(self):
        """Total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate cart subtotal"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_weight(self):
        """Calculate total weight of cart items"""
        total = 0
        for item in self.items.all():
            if item.product.weight:
                total += item.product.weight * item.quantity
        return total
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """Individual cart item model"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Store price at time of adding to cart (for price consistency)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'product', 'variant']
    
    def __str__(self):
        variant_info = f" ({self.variant.name})" if self.variant else ""
        return f"{self.quantity}x {self.product.name}{variant_info}"
    
    def save(self, *args, **kwargs):
        # Set unit price based on variant or product price
        if self.variant:
            self.unit_price = self.variant.effective_price
        else:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        return self.unit_price * self.quantity
    
    @property
    def is_available(self):
        """Check if item is still available in stock"""
        if self.variant:
            return self.variant.stock_quantity >= self.quantity
        return self.product.stock_quantity >= self.quantity if self.product.track_inventory else True


class SavedItem(models.Model):
    """Saved for later items (moved from cart)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Store original cart price
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product', 'variant']
    
    def __str__(self):
        variant_info = f" ({self.variant.name})" if self.variant else ""
        return f"Saved: {self.quantity}x {self.product.name}{variant_info}"
    
    def move_to_cart(self):
        """Move saved item back to cart"""
        cart, created = Cart.objects.get_or_create(user=self.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=self.product,
            variant=self.variant,
            defaults={
                'quantity': self.quantity,
                'unit_price': self.product.price if not self.variant else self.variant.effective_price
            }
        )
        
        if not created:
            cart_item.quantity += self.quantity
            cart_item.save()
        
        self.delete()
        return cart_item


class Coupon(models.Model):
    """Discount coupon model with flat and percentage discount support"""
    code = models.CharField(max_length=50, unique=True, help_text="Unique coupon code (auto-generated or manual)")
    name = models.CharField(max_length=100, help_text="Display name for the coupon")
    description = models.TextField(blank=True, help_text="Description of the coupon and its benefits")
    
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage Discount'),
        ('flat', 'Flat Amount Discount'),
        ('free_shipping', 'Free Shipping'),
    ]
    
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPES, help_text="Type of discount to apply")
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Discount value (percentage or flat amount depending on type)"
    )
    
    # Usage limitations
    minimum_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(0)],
        help_text="Minimum order amount required to use this coupon"
    )
    maximum_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, 
        validators=[MinValueValidator(0)],
        help_text="Maximum discount amount (useful for percentage coupons)"
    )
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Total number of times this coupon can be used (leave blank for unlimited)"
    )
    usage_limit_per_user = models.PositiveIntegerField(
        default=1, 
        help_text="Maximum number of times a single user can use this coupon"
    )
    used_count = models.PositiveIntegerField(default=0, help_text="Number of times this coupon has been used")
    
    # Validity dates
    valid_from = models.DateTimeField(help_text="Date and time from which this coupon becomes valid")
    valid_until = models.DateTimeField(help_text="Date and time until which this coupon remains valid")
    is_active = models.BooleanField(default=True, help_text="Whether this coupon is currently active")
    
    # Admin fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_coupons')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate code if not provided
        if not self.code:
            self.code = self.generate_coupon_code()
        # Convert code to uppercase for consistency
        self.code = self.code.upper()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_coupon_code():
        """Generate a unique coupon code"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Coupon.objects.filter(code=code).exists():
                return code
    
    def is_valid(self, user=None, cart_total=0):
        """Check if coupon is valid for use"""
        from django.utils import timezone
        
        if not self.is_active:
            return False, "Coupon is not active"
        
        now = timezone.now()
        if now < self.valid_from:
            return False, "Coupon is not yet valid"
        
        if now > self.valid_until:
            return False, "Coupon has expired"
        
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Coupon usage limit reached"
        
        if cart_total < self.minimum_order_amount:
            return False, f"Minimum order amount is ৳{self.minimum_order_amount}"
        
        if user:
            user_usage = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_usage >= self.usage_limit_per_user:
                return False, "You have already used this coupon"
        
        return True, "Valid"
    
    def calculate_discount(self, cart_total):
        """Calculate discount amount"""
        if self.discount_type == 'percentage':
            discount = (self.discount_value / 100) * cart_total
        elif self.discount_type == 'flat':  # Changed from 'fixed_amount' to 'flat'
            discount = self.discount_value
        else:  # free_shipping
            discount = 0  # Shipping discount handled separately
        
        # Apply maximum discount limit if set
        if self.maximum_discount_amount:
            discount = min(discount, self.maximum_discount_amount)
        
        return min(discount, cart_total)  # Don't discount more than cart total
    
    @property
    def discount_display(self):
        """Get a user-friendly display of the discount"""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}% off"
        elif self.discount_type == 'flat':
            return f"৳{self.discount_value} off"
        else:
            return "Free shipping"
    
    @property
    def is_expired(self):
        """Check if coupon has expired"""
        from django.utils import timezone
        return timezone.now() > self.valid_until
    
    @property
    def days_until_expiry(self):
        """Get number of days until expiry"""
        from django.utils import timezone
        if self.is_expired:
            return 0
        delta = self.valid_until - timezone.now()
        return delta.days
    
    @property
    def usage_percentage(self):
        """Get usage percentage for analytics"""
        if not self.usage_limit:
            return 0
        return min((self.used_count / self.usage_limit) * 100, 100)


class CouponUsage(models.Model):
    """Track coupon usage by users and guests"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usage_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usage', null=True, blank=True)
    order_id = models.CharField(max_length=100, blank=True)  # Link to order when used
    
    # For guest users, we can track additional info
    guest_email = models.EmailField(blank=True, help_text="Email for guest coupon usage")
    guest_phone = models.CharField(max_length=20, blank=True, help_text="Phone for guest coupon usage")
    
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Remove unique_together constraint as it doesn't work well with nullable fields
        indexes = [
            models.Index(fields=['coupon', 'user', 'order_id']),
            models.Index(fields=['coupon', 'guest_email', 'order_id']),
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} used {self.coupon.code}"
        else:
            return f"Guest ({self.guest_email}) used {self.coupon.code}"
