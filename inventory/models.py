from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from decimal import Decimal

User = get_user_model()


class StockActivity(models.Model):
    """
    Professional stock activity tracking for all stock movements
    Tracks both product and variant stock changes with full audit trail
    """
    
    ACTIVITY_TYPES = [
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('adjustment', 'Stock Adjustment'),
        ('initial', 'Initial Stock'),
        ('transfer', 'Stock Transfer'),
        ('damaged', 'Damaged Stock'),
        ('expired', 'Expired Stock'),
        ('returned', 'Customer Return'),
        ('sold', 'Stock Sold'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    # Activity metadata
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    # Generic foreign key to handle both Product and ProductVariant
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Stock change details
    quantity_before = models.IntegerField(help_text="Stock quantity before the activity")
    quantity_changed = models.IntegerField(help_text="Amount added (positive) or removed (negative)")
    quantity_after = models.IntegerField(help_text="Stock quantity after the activity")
    
    # Cost information
    unit_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Cost per unit for this activity"
    )
    total_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total cost for this activity"
    )
    
    # Activity details
    reason = models.TextField(help_text="Reason for the stock activity")
    reference_number = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Reference number (PO, Invoice, etc.)"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # User and tracking
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='stock_activities'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_stock_activities'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activity_date = models.DateTimeField(
        help_text="When the stock activity actually occurred"
    )
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-activity_date', '-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['created_by']),
            models.Index(fields=['activity_date']),
            models.Index(fields=['status']),
        ]
        verbose_name = "Stock Activity"
        verbose_name_plural = "Stock Activities"
    
    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.content_object} ({self.quantity_changed:+d})"
    
    @property
    def item_name(self):
        """Get the name of the item (product or variant)"""
        if hasattr(self.content_object, 'name'):
            return self.content_object.name
        return str(self.content_object)
    
    @property
    def item_sku(self):
        """Get the SKU of the item"""
        if hasattr(self.content_object, 'sku'):
            return self.content_object.sku
        return None
    
    @property
    def is_product(self):
        """Check if this activity is for a product"""
        return self.content_type.model == 'product'
    
    @property
    def is_variant(self):
        """Check if this activity is for a variant"""
        return self.content_type.model == 'productvariant'
    
    @property
    def product_name(self):
        """Get the product name (for both products and variants)"""
        if self.is_product:
            return self.content_object.name
        elif self.is_variant and hasattr(self.content_object, 'product'):
            return self.content_object.product.name
        return "Unknown Product"
    
    @property
    def variant_name(self):
        """Get the variant name if applicable"""
        if self.is_variant:
            return self.content_object.name
        return None
    
    @property
    def is_stock_increase(self):
        """Check if this activity increases stock"""
        return self.quantity_changed > 0
    
    @property
    def is_stock_decrease(self):
        """Check if this activity decreases stock"""
        return self.quantity_changed < 0
    
    def save(self, *args, **kwargs):
        # Calculate total cost if unit cost is provided
        if self.unit_cost and not self.total_cost:
            self.total_cost = self.unit_cost * abs(self.quantity_changed)
        
        super().save(*args, **kwargs)


class StockActivityBatch(models.Model):
    """
    Batch operations for multiple stock activities
    Useful for bulk stock operations
    """
    
    BATCH_TYPES = [
        ('bulk_import', 'Bulk Import'),
        ('bulk_adjustment', 'Bulk Adjustment'),
        ('inventory_count', 'Inventory Count'),
        ('supplier_delivery', 'Supplier Delivery'),
        ('bulk_transfer', 'Bulk Transfer'),
    ]
    
    batch_type = models.CharField(max_length=20, choices=BATCH_TYPES)
    batch_number = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    # Batch metadata
    total_activities = models.PositiveIntegerField(default=0)
    completed_activities = models.PositiveIntegerField(default=0)
    failed_activities = models.PositiveIntegerField(default=0)
    
    # User and tracking
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Stock Activity Batch"
        verbose_name_plural = "Stock Activity Batches"
    
    def __str__(self):
        return f"{self.get_batch_type_display()}: {self.batch_number}"
    
    @property
    def success_rate(self):
        """Calculate the success rate of the batch"""
        if self.total_activities == 0:
            return 0
        return (self.completed_activities / self.total_activities) * 100


# Add this to the StockActivity model to link with batches
StockActivity.add_to_class(
    'batch',
    models.ForeignKey(
        StockActivityBatch, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='activities'
    )
)