from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import IncompleteOrder, IncompleteOrderHistory, IncompleteOrderAnalytics


@receiver(post_save, sender=IncompleteOrder)
def track_incomplete_order_changes(sender, instance, created, **kwargs):
    """Track changes to incomplete orders"""
    if created:
        # Log creation
        IncompleteOrderHistory.objects.create(
            incomplete_order=instance,
            action='created',
            details='Incomplete order created',
            created_by_system=True
        )
    else:
        # Track status changes
        if instance._state.adding is False:  # Only for updates
            try:
                old_instance = IncompleteOrder.objects.get(pk=instance.pk)
                if old_instance.status != instance.status:
                    IncompleteOrderHistory.objects.create(
                        incomplete_order=instance,
                        action='updated',
                        details=f'Status changed from {old_instance.status} to {instance.status}',
                        created_by_system=True
                    )
            except IncompleteOrder.DoesNotExist:
                pass


@receiver(pre_delete, sender=IncompleteOrder)
def track_incomplete_order_deletion(sender, instance, **kwargs):
    """Track when incomplete orders are deleted"""
    IncompleteOrderHistory.objects.create(
        incomplete_order=instance,
        action='deleted',
        details='Incomplete order deleted',
        created_by_system=True
    )


def update_daily_analytics():
    """
    Update daily analytics for incomplete orders
    This function should be called by a daily scheduled task (e.g., Celery)
    """
    today = timezone.now().date()
    
    # Get or create analytics record for today
    analytics, created = IncompleteOrderAnalytics.objects.get_or_create(
        date=today,
        defaults={
            'total_incomplete_orders': 0,
            'abandoned_orders': 0,
            'converted_orders': 0,
            'expired_orders': 0,
            'recovery_emails_sent': 0,
            'recovery_success_count': 0,
            'total_lost_revenue': 0,
            'recovered_revenue': 0,
        }
    )
    
    # Count incomplete orders created today
    todays_orders = IncompleteOrder.objects.filter(created_at__date=today)
    
    analytics.total_incomplete_orders = todays_orders.count()
    analytics.abandoned_orders = todays_orders.filter(status='abandoned').count()
    analytics.converted_orders = todays_orders.filter(status='converted').count()
    analytics.expired_orders = todays_orders.filter(expires_at__lt=timezone.now()).count()
    
    # Calculate financial metrics
    analytics.total_lost_revenue = todays_orders.filter(
        status='abandoned'
    ).aggregate(total=models.Sum('total_amount'))['total'] or 0
    
    analytics.recovered_revenue = todays_orders.filter(
        status='converted'
    ).aggregate(total=models.Sum('total_amount'))['total'] or 0
    
    # Count recovery emails sent today
    from .models import RecoveryEmailLog
    analytics.recovery_emails_sent = RecoveryEmailLog.objects.filter(
        sent_at__date=today
    ).count()
    
    analytics.recovery_success_count = RecoveryEmailLog.objects.filter(
        sent_at__date=today,
        responded=True
    ).count()
    
    # Calculate rates
    analytics.calculate_rates()
    
    return analytics