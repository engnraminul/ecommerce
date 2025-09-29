from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from products.models import Product, ProductVariant
from cart.models import Coupon
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()


class IncompleteOrder(models.Model):
    """Model for tracking incomplete/abandoned orders"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('abandoned', 'Abandoned'),
        ('payment_failed', 'Payment Failed'),
        ('payment_pending', 'Payment Pending'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Order'),
    ]
    
    # Order identification
    incomplete_order_id = models.CharField(max_length=50, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomplete_orders', null=True, blank=True)
    
    # Guest order information
    is_guest_order = models.BooleanField(default=False)
    guest_email = models.EmailField(blank=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Order status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Financial information
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    
    # Coupon information
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Customer information
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # Recovery tracking
    recovery_attempts = models.PositiveIntegerField(default=0)
    last_recovery_attempt = models.DateTimeField(null=True, blank=True)
    
    # Browser/Device information for analytics
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referrer_url = models.URLField(blank=True)
    
    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    abandonment_reason = models.CharField(max_length=100, blank=True)  # For tracking why order was abandoned
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    abandoned_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Conversion tracking
    converted_order_id = models.CharField(max_length=50, blank=True)  # Reference to completed order
    converted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['session_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Incomplete Order {self.incomplete_order_id} - {self.user.username}"
        return f"Guest Incomplete Order {self.incomplete_order_id} - {self.customer_email or self.session_id}"
    
    def save(self, *args, **kwargs):
        if not self.incomplete_order_id:
            # Generate unique incomplete order ID
            self.incomplete_order_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        
        # Set expiry date if not set (default 30 days)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        
        # Auto-set abandoned_at when status changes to abandoned
        if self.status == 'abandoned' and not self.abandoned_at:
            self.abandoned_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        """Total number of items in incomplete order"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def is_expired(self):
        """Check if incomplete order has expired"""
        return self.expires_at and timezone.now() > self.expires_at
    
    @property
    def days_since_created(self):
        """Days since order was created"""
        return (timezone.now() - self.created_at).days
    
    @property
    def can_convert(self):
        """Check if incomplete order can be converted to complete order"""
        return self.status in ['pending', 'payment_pending', 'abandoned'] and not self.is_expired
    
    def calculate_totals(self):
        """Recalculate order totals"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        shipping_cost = self.shipping_cost or 0
        tax_amount = self.tax_amount or 0
        discount_amount = self.discount_amount or 0
        coupon_discount = self.coupon_discount or 0
        
        self.total_amount = self.subtotal + shipping_cost + tax_amount - discount_amount - coupon_discount
        self.save()
    
    def mark_as_abandoned(self, reason=''):
        """Mark order as abandoned"""
        self.status = 'abandoned'
        self.abandoned_at = timezone.now()
        if reason:
            self.abandonment_reason = reason
        self.save()
    
    def increment_recovery_attempt(self):
        """Increment recovery attempt counter"""
        self.recovery_attempts += 1
        self.last_recovery_attempt = timezone.now()
        self.save()
    
    def convert_to_order(self):
        """Convert incomplete order to complete order"""
        from orders.models import Order, OrderItem, ShippingAddress
        
        if not self.can_convert:
            raise ValueError("Cannot convert this incomplete order")
        
        # Create the main order
        order = Order.objects.create(
            user=self.user,
            is_guest_order=self.is_guest_order,
            guest_email=self.guest_email,
            session_id=self.session_id,
            status='pending',
            payment_status='pending',
            subtotal=self.subtotal,
            shipping_cost=self.shipping_cost,
            tax_amount=self.tax_amount,
            discount_amount=self.discount_amount,
            total_amount=self.total_amount,
            coupon_code=self.coupon_code,
            coupon_discount=self.coupon_discount,
            customer_email=self.customer_email or self.guest_email,
            customer_phone=self.customer_phone,
            customer_notes=self.customer_notes,
        )
        
        # Copy order items
        for incomplete_item in self.items.all():
            OrderItem.objects.create(
                order=order,
                product=incomplete_item.product,
                variant=incomplete_item.variant,
                quantity=incomplete_item.quantity,
                unit_price=incomplete_item.unit_price,
            )
        
        # Copy shipping address if exists
        if hasattr(self, 'shipping_address'):
            ShippingAddress.objects.create(
                order=order,
                first_name=self.shipping_address.first_name,
                last_name=self.shipping_address.last_name,
                company=self.shipping_address.company,
                address_line_1=self.shipping_address.address_line_1,
                address_line_2=self.shipping_address.address_line_2,
                city=self.shipping_address.city,
                state=self.shipping_address.state,
                postal_code=self.shipping_address.postal_code,
                country=self.shipping_address.country,
                phone=self.shipping_address.phone,
                email=self.shipping_address.email,
                delivery_instructions=self.shipping_address.delivery_instructions,
            )
        
        # Update incomplete order status
        self.status = 'converted'
        self.converted_order_id = order.order_number
        self.converted_at = timezone.now()
        self.save()
        
        # Log the conversion
        IncompleteOrderHistory.objects.create(
            incomplete_order=self,
            action='converted',
            details=f'Converted to Order {order.order_number}',
            created_by_system=True
        )
        
        return order


class IncompleteOrderItem(models.Model):
    """Individual items in incomplete order"""
    incomplete_order = models.ForeignKey(IncompleteOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Product details at time of addition (for record keeping)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=100, blank=True)
    variant_name = models.CharField(max_length=100, blank=True)
    
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Track when item was added/modified
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        variant_info = f" ({self.variant_name})" if self.variant_name else ""
        return f"{self.quantity}x {self.product_name}{variant_info}"
    
    def save(self, *args, **kwargs):
        # Store product details at time of addition
        self.product_name = self.product.name
        self.product_sku = self.product.sku
        if self.variant:
            self.variant_name = self.variant.name
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        """Calculate total price for this item"""
        if self.unit_price is None or self.quantity is None:
            return 0
        return self.unit_price * self.quantity


class IncompleteShippingAddress(models.Model):
    """Shipping address for incomplete orders"""
    incomplete_order = models.OneToOneField(IncompleteOrder, on_delete=models.CASCADE, related_name='shipping_address')
    
    # Recipient information
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    
    # Address details
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Contact information
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    
    # Delivery instructions
    delivery_instructions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Shipping to {self.first_name} {self.last_name} for Incomplete Order {self.incomplete_order.incomplete_order_id}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
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
    
    @property
    def is_complete(self):
        """Check if address has minimum required fields"""
        return bool(self.first_name and self.address_line_1 and self.city and self.country)


class IncompleteOrderHistory(models.Model):
    """Track actions and changes on incomplete orders"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('abandoned', 'Abandoned'),
        ('recovery_sent', 'Recovery Email Sent'),
        ('recovered', 'Customer Returned'),
        ('converted', 'Converted to Order'),
        ('expired', 'Expired'),
        ('deleted', 'Deleted'),
    ]
    
    incomplete_order = models.ForeignKey(IncompleteOrder, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    
    # Who performed the action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_by_system = models.BooleanField(default=False)
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Incomplete Order Histories"
    
    def __str__(self):
        return f"Incomplete Order {self.incomplete_order.incomplete_order_id}: {self.get_action_display()}"


class RecoveryEmailLog(models.Model):
    """Track recovery emails sent to customers"""
    
    EMAIL_TYPE_CHOICES = [
        ('abandoned_cart', 'Abandoned Cart'),
        ('payment_reminder', 'Payment Reminder'),
        ('final_reminder', 'Final Reminder'),
        ('discount_offer', 'Discount Offer'),
    ]
    
    incomplete_order = models.ForeignKey(IncompleteOrder, on_delete=models.CASCADE, related_name='recovery_emails')
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES)
    
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    
    # Email delivery tracking
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    opened = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)
    
    # Response tracking
    responded = models.BooleanField(default=False)
    response_date = models.DateTimeField(null=True, blank=True)
    
    # Discount offered (if any)
    discount_code = models.CharField(max_length=50, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.get_email_type_display()} sent to {self.recipient_email} for {self.incomplete_order.incomplete_order_id}"


class IncompleteOrderAnalytics(models.Model):
    """Analytics model for tracking incomplete order patterns"""
    
    # Date for the analytics data
    date = models.DateField(unique=True)
    
    # Daily counts
    total_incomplete_orders = models.PositiveIntegerField(default=0)
    abandoned_orders = models.PositiveIntegerField(default=0)
    converted_orders = models.PositiveIntegerField(default=0)
    expired_orders = models.PositiveIntegerField(default=0)
    
    # Recovery metrics
    recovery_emails_sent = models.PositiveIntegerField(default=0)
    recovery_success_count = models.PositiveIntegerField(default=0)
    
    # Financial metrics
    total_lost_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recovered_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Calculated fields
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    recovery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)    # Percentage
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"
    
    def calculate_rates(self):
        """Calculate conversion and recovery rates"""
        if self.total_incomplete_orders > 0:
            self.conversion_rate = (self.converted_orders / self.total_incomplete_orders) * 100
        
        if self.recovery_emails_sent > 0:
            self.recovery_rate = (self.recovery_success_count / self.recovery_emails_sent) * 100
        
        self.save()
