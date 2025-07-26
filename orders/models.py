from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from products.models import Product, ProductVariant
from cart.models import Coupon
import uuid

User = get_user_model()


class Order(models.Model):
    """Main order model"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cod_confirmed', 'COD Confirmed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Order identification
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Order status
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Financial information
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Coupon information
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Customer information (stored for record keeping)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        """Total number of items in order"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed']
    
    @property
    def is_cod_order(self):
        """Check if this is a Cash on Delivery order"""
        return self.payment_status == 'cod_confirmed'
    
    def calculate_totals(self):
        """Recalculate order totals"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        # Add shipping, tax, discount calculations here
        shipping_cost = self.shipping_cost or 0
        tax_amount = self.tax_amount or 0
        discount_amount = self.discount_amount or 0
        coupon_discount = self.coupon_discount or 0
        
        self.total_amount = self.subtotal + shipping_cost + tax_amount - discount_amount - coupon_discount
        self.save()


class OrderItem(models.Model):
    """Individual order item"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Product details at time of order (for record keeping)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=100, blank=True)
    variant_name = models.CharField(max_length=100, blank=True)
    
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        variant_info = f" ({self.variant_name})" if self.variant_name else ""
        return f"{self.quantity}x {self.product_name}{variant_info}"
    
    def save(self, *args, **kwargs):
        # Store product details at time of order
        self.product_name = self.product.name
        self.product_sku = self.product.sku
        if self.variant:
            self.variant_name = self.variant.name
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        """Calculate total price for this order item"""
        if self.unit_price is None or self.quantity is None:
            return 0
        return self.unit_price * self.quantity


class ShippingAddress(models.Model):
    """Shipping address for orders"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipping_address')
    
    # Recipient information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    
    # Address details
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Contact information
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    
    # Delivery instructions
    delivery_instructions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Shipping to {self.first_name} {self.last_name} for Order {self.order.order_number}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])


class OrderStatusHistory(models.Model):
    """Track order status changes"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    
    # Who made the change
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Tracking information for shipped status
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Order Status Histories"
    
    def __str__(self):
        return f"Order {self.order.order_number}: {self.old_status} → {self.new_status}"


class Invoice(models.Model):
    """Invoice model for orders"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    invoice_date = models.DateTimeField(auto_now_add=True)
    
    # PDF file storage
    invoice_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    
    # Billing information (copied from order)
    billing_name = models.CharField(max_length=200)
    billing_email = models.EmailField()
    billing_address = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def generate_pdf(self):
        """Generate PDF invoice file"""
        # This would implement PDF generation using reportlab
        # Implementation depends on your PDF generation requirements
        pass


class RefundRequest(models.Model):
    """Refund request model"""
    REFUND_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]
    
    REFUND_REASON_CHOICES = [
        ('defective', 'Product Defective'),
        ('wrong_item', 'Wrong Item Received'),
        ('not_as_described', 'Not As Described'),
        ('damaged_shipping', 'Damaged During Shipping'),
        ('changed_mind', 'Changed Mind'),
        ('other', 'Other'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests')
    
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    reason = models.CharField(max_length=20, choices=REFUND_REASON_CHOICES)
    description = models.TextField()
    
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    
    # Admin response
    admin_response = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Refund Request for Order {self.order.order_number} - ${self.refund_amount}"
