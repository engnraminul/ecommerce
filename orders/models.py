from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from products.models import Product, ProductVariant
from cart.models import Coupon
from .phone_utils import normalize_bangladeshi_phone
import uuid

User = get_user_model()


class Order(models.Model):
    """Main order model"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('partially_returned', 'Partially Returned'),
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    
    # Guest order information (for orders without user account)
    is_guest_order = models.BooleanField(default=False)
    guest_email = models.EmailField(blank=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)  # Track guest session
    
    # Order status
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Financial information
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Coupon information
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Payment method information
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
    ]
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_method_display_name = models.CharField(max_length=100, blank=True)  # Store the display name
    
    # Mobile wallet payment details
    bkash_transaction_id = models.CharField(max_length=100, blank=True)
    bkash_sender_number = models.CharField(max_length=15, blank=True)
    nagad_transaction_id = models.CharField(max_length=100, blank=True)
    nagad_sender_number = models.CharField(max_length=15, blank=True)
    
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

    #curier details
    curier_id = models.CharField(max_length=100, blank=True)
    curier_charge = models.DecimalField(max_digits=8, decimal_places=2, default=110, validators=[MinValueValidator(0)])
    curier_status = models.CharField(max_length=100, blank=True)
    curier_date = models.DateField(null=True, blank=True)  # Date when order was added to courier
    partially_ammount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Order {self.order_number} - {self.user.username}"
        return f"Guest Order {self.order_number} - {self.customer_email}"
    
    def save(self, *args, **kwargs):
        # Normalize phone numbers before saving
        if self.customer_phone:
            self.customer_phone = normalize_bangladeshi_phone(self.customer_phone)
        if self.bkash_sender_number:
            self.bkash_sender_number = normalize_bangladeshi_phone(self.bkash_sender_number)
        if self.nagad_sender_number:
            self.nagad_sender_number = normalize_bangladeshi_phone(self.nagad_sender_number)
            
        if not self.order_number:
            # Get the last order number to generate sequential number
            last_order = Order.objects.filter(
                order_number__startswith='MB'
            ).order_by('-id').first()
            
            if last_order and last_order.order_number.startswith('MB'):
                try:
                    # Extract number from last order (e.g., MB1002 -> 1002)
                    last_number = int(last_order.order_number[2:])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    # If there's an issue parsing, start from 1000
                    next_number = 1000
            else:
                # First order starts at 1000
                next_number = 1000
            
            self.order_number = f"MB{next_number}"
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
    last_name = models.CharField(max_length=100, blank=True)
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
    STATUS_CHOICES = [
        ('pending', 'Order Placed'),
        ('confirmed', 'Order Confirmed'),
        ('processing', 'Processing'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    
    # Original fields (keep for backward compatibility)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # New enhanced fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_system_generated = models.BooleanField(default=False)
    
    # Additional tracking information
    carrier_url = models.URLField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    
    # Status metadata
    is_milestone = models.BooleanField(default=True)
    is_customer_visible = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Order Status Histories"
    
    def __str__(self):
        if self.status:
            return f"Order {self.order.order_number}: {self.get_status_display()}"
        return f"Order {self.order.order_number}: {self.old_status} → {self.new_status}"
    
    def get_display_status(self):
        """Get the display status - use new status field if available, fallback to old"""
        if self.status:
            return self.get_status_display()
        return self.new_status.replace('_', ' ').title()
        
    def get_display_title(self):
        """Get display title"""
        if self.title:
            return self.title
        return self.get_display_status()
        
    def get_display_description(self):
        """Get display description"""
        if self.description:
            return self.description
        return self.notes
        
    def save(self, *args, **kwargs):
        # Auto-populate new fields from old ones for backward compatibility
        if not self.status and self.new_status:
            self.status = self.new_status
        if not self.title and self.status:
            self.title = self.get_status_display()
        if not self.description and self.notes:
            self.description = self.notes
        super().save(*args, **kwargs)


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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests', null=True, blank=True)
    
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
