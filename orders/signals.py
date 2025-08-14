from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Order, OrderStatusHistory

# Store original status before save
@receiver(pre_save, sender=Order)
def store_original_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = Order.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Order.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=Order)
def track_status_change(sender, instance, created, **kwargs):
    """Automatically create status history when order status changes"""
    
    # Define status messages and descriptions
    status_info = {
        'pending': {
            'title': 'Order Placed',
            'description': 'Your order has been received and is being reviewed.',
        },
        'confirmed': {
            'title': 'Order Confirmed',
            'description': 'Your order has been confirmed and payment verified.',
        },
        'processing': {
            'title': 'Processing Order',
            'description': 'Your order is being prepared for shipment.',
        },
        'packed': {
            'title': 'Order Packed',
            'description': 'Your order has been packed and is ready for pickup.',
        },
        'shipped': {
            'title': 'Order Shipped',
            'description': 'Your order is on its way to you.',
        },
        'out_for_delivery': {
            'title': 'Out for Delivery',
            'description': 'Your order is out for delivery and will arrive soon.',
        },
        'delivered': {
            'title': 'Delivered',
            'description': 'Your order has been successfully delivered.',
        },
        'cancelled': {
            'title': 'Order Cancelled',
            'description': 'Your order has been cancelled.',
        },
        'refunded': {
            'title': 'Order Refunded',
            'description': 'Your order has been refunded.',
        },
    }
    
    if created:
        # New order created
        info = status_info.get(instance.status, {})
        OrderStatusHistory.objects.create(
            order=instance,
            old_status='',  # New order
            new_status=instance.status,
            status=instance.status,
            title=info.get('title', instance.get_status_display()),
            description=info.get('description', ''),
            notes=info.get('description', ''),  # For backward compatibility
            tracking_number='',  # Empty string for NOT NULL constraint
            carrier='',  # Empty string for NOT NULL constraint
            is_system_generated=True,
            is_milestone=True,
            is_customer_visible=True
        )
    else:
        # Check if status changed
        original_status = getattr(instance, '_original_status', None)
        if original_status and original_status != instance.status:
            info = status_info.get(instance.status, {})
            
            # Update timestamp fields based on status
            if instance.status == 'confirmed' and not instance.confirmed_at:
                instance.confirmed_at = timezone.now()
                Order.objects.filter(pk=instance.pk).update(confirmed_at=instance.confirmed_at)
            elif instance.status == 'shipped' and not instance.shipped_at:
                instance.shipped_at = timezone.now()
                Order.objects.filter(pk=instance.pk).update(shipped_at=instance.shipped_at)
            elif instance.status == 'delivered' and not instance.delivered_at:
                instance.delivered_at = timezone.now()
                Order.objects.filter(pk=instance.pk).update(delivered_at=instance.delivered_at)
            
            OrderStatusHistory.objects.create(
                order=instance,
                old_status=original_status,
                new_status=instance.status,
                status=instance.status,
                title=info.get('title', instance.get_status_display()),
                description=info.get('description', ''),
                notes=info.get('description', ''),  # For backward compatibility
                tracking_number='',  # Empty string for NOT NULL constraint
                carrier='',  # Empty string for NOT NULL constraint
                is_system_generated=True,
                is_milestone=True,
                is_customer_visible=True
            )

def add_tracking_update(order, title, description, tracking_number=None, carrier=None, 
                       carrier_url=None, location=None, estimated_delivery=None, 
                       changed_by=None, is_milestone=False):
    """Helper function to add custom tracking updates"""
    OrderStatusHistory.objects.create(
        order=order,
        old_status=order.status,  # Keep current status in old_status for compatibility
        new_status=order.status,  # Keep current status
        status=order.status,  # Keep current status
        title=title,
        description=description,
        notes=description,  # For backward compatibility
        tracking_number=tracking_number or '',  # Ensure empty string instead of None
        carrier=carrier or '',  # Ensure empty string instead of None
        carrier_url=carrier_url or '',
        location=location or '',
        estimated_delivery=estimated_delivery,
        changed_by=changed_by,
        is_system_generated=False,
        is_milestone=is_milestone,
        is_customer_visible=True
    )
