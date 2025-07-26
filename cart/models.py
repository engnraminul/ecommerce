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
    """Discount coupon model"""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
    ]
    
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Usage limitations
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    maximum_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    usage_limit = models.PositiveIntegerField(null=True, blank=True)  # Total usage limit
    usage_limit_per_user = models.PositiveIntegerField(default=1)  # Per user limit
    used_count = models.PositiveIntegerField(default=0)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def is_valid(self, user=None, cart_total=0):
        """Check if coupon is valid for use"""
        from django.utils import timezone
        
        if not self.is_active:
            return False, "Coupon is not active"
        
        if timezone.now() < self.valid_from:
            return False, "Coupon is not yet valid"
        
        if timezone.now() > self.valid_until:
            return False, "Coupon has expired"
        
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Coupon usage limit reached"
        
        if cart_total < self.minimum_order_amount:
            return False, f"Minimum order amount is ${self.minimum_order_amount}"
        
        if user:
            user_usage = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_usage >= self.usage_limit_per_user:
                return False, "You have already used this coupon"
        
        return True, "Valid"
    
    def calculate_discount(self, cart_total):
        """Calculate discount amount"""
        if self.discount_type == 'percentage':
            discount = (self.discount_value / 100) * cart_total
        elif self.discount_type == 'fixed_amount':
            discount = self.discount_value
        else:  # free_shipping
            discount = 0  # Shipping discount handled separately
        
        # Apply maximum discount limit if set
        if self.maximum_discount_amount:
            discount = min(discount, self.maximum_discount_amount)
        
        return min(discount, cart_total)  # Don't discount more than cart total


class CouponUsage(models.Model):
    """Track coupon usage by users"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usage_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usage')
    order_id = models.CharField(max_length=100, blank=True)  # Link to order when used
    
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['coupon', 'user', 'order_id']
    
    def __str__(self):
        return f"{self.user.username} used {self.coupon.code}"
