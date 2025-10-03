from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant

User = get_user_model()


class StockMovement(models.Model):
    """Track all stock movements for audit purposes"""
    MOVEMENT_TYPES = [
        ('adjustment_increase', 'Manual Increase'),
        ('adjustment_decrease', 'Manual Decrease'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('restock', 'Restock'),
        ('damage', 'Damage/Loss'),
        ('transfer', 'Transfer'),
        ('initial', 'Initial Stock'),
    ]
    
    # Related item (either product or variant)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_movements')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='stock_movements')
    
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField(help_text="Positive for increase, negative for decrease")
    
    # Stock levels
    previous_stock = models.PositiveIntegerField()
    new_stock = models.PositiveIntegerField()
    
    # Movement details
    reason = models.TextField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Order number, batch number, etc.")
    
    # User and timestamp
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'created_at']),
            models.Index(fields=['variant', 'created_at']),
            models.Index(fields=['movement_type']),
        ]
    
    def __str__(self):
        item_name = self.variant.name if self.variant else self.product.name
        return f"{item_name}: {self.movement_type} ({self.quantity_change:+d})"
    
    @property
    def item_name(self):
        """Get the name of the item (product or variant)"""
        if self.variant:
            return f"{self.variant.product.name} - {self.variant.name}"
        return self.product.name
    
    @property
    def item_sku(self):
        """Get the SKU of the item (product or variant)"""
        if self.variant:
            return self.variant.sku or f"{self.variant.product.sku}-{self.variant.name}"
        return self.product.sku


class StockAlert(models.Model):
    """Stock alert settings and history"""
    ALERT_TYPES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('overstocked', 'Overstocked'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    threshold = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    
    # Alert history
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'alert_type']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_alert_type_display()}"


class StockAdjustmentBatch(models.Model):
    """Batch operations for stock adjustments"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Batch details
    total_items = models.PositiveIntegerField(default=0)
    processed_items = models.PositiveIntegerField(default=0)
    failed_items = models.PositiveIntegerField(default=0)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # User and timestamps
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Batch: {self.name} ({self.status})"


class StockAdjustmentBatchItem(models.Model):
    """Individual items in a stock adjustment batch"""
    batch = models.ForeignKey(StockAdjustmentBatch, on_delete=models.CASCADE, related_name='items')
    
    # Item details
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    
    # Adjustment details
    adjustment_type = models.CharField(max_length=20, choices=[('increase', 'Increase'), ('decrease', 'Decrease')])
    quantity = models.PositiveIntegerField()
    reason = models.TextField(blank=True)
    
    # Processing status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Results
    previous_stock = models.PositiveIntegerField(null=True, blank=True)
    new_stock = models.PositiveIntegerField(null=True, blank=True)
    
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        item_name = self.variant.name if self.variant else self.product.name
        return f"{self.batch.name}: {item_name} ({self.status})"