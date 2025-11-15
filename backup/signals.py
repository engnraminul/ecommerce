from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import BackupRecord, BackupSchedule, BackupSettings
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BackupRecord)
def backup_record_post_save(sender, instance, created, **kwargs):
    """Handle backup record post-save actions"""
    if created:
        logger.info(f"New backup created: {instance.name} ({instance.backup_type})")
    
    # Log status changes
    if not created and instance.status:
        logger.info(f"Backup {instance.name} status changed to: {instance.status}")


@receiver(pre_delete, sender=BackupRecord)
def backup_record_pre_delete(sender, instance, **kwargs):
    """Handle backup record deletion"""
    try:
        # Delete associated files before deleting the record
        deleted_files = instance.delete_backup_files()
        if deleted_files:
            logger.info(f"Deleted backup files for {instance.name}: {deleted_files}")
    except Exception as e:
        logger.error(f"Error deleting backup files for {instance.name}: {str(e)}")


@receiver(post_save, sender=BackupSchedule)
def backup_schedule_post_save(sender, instance, created, **kwargs):
    """Handle backup schedule post-save actions"""
    if created:
        logger.info(f"New backup schedule created: {instance.name}")
        
        # Calculate initial next_run if not set
        if not instance.next_run:
            from datetime import datetime, timedelta
            
            now = timezone.now()
            next_run = now.replace(
                hour=instance.hour,
                minute=instance.minute,
                second=0,
                microsecond=0
            )
            
            # If the time has already passed today, schedule for tomorrow/next occurrence
            if next_run <= now:
                if instance.schedule_type == 'daily':
                    next_run += timedelta(days=1)
                elif instance.schedule_type == 'weekly':
                    days_ahead = instance.day_of_week - now.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    next_run += timedelta(days=days_ahead)
                elif instance.schedule_type == 'monthly':
                    # Simple approach: add 30 days
                    next_run += timedelta(days=30)
            
            instance.next_run = next_run
            # Use update to avoid recursion
            BackupSchedule.objects.filter(pk=instance.pk).update(next_run=next_run)


@receiver(post_save, sender=BackupSettings)
def backup_settings_post_save(sender, instance, created, **kwargs):
    """Handle backup settings changes"""
    if created:
        logger.info("Backup settings initialized")
    else:
        logger.info("Backup settings updated")
    
    # Ensure backup directory exists
    import os
    from django.conf import settings as django_settings
    
    backup_dir = os.path.join(django_settings.MEDIA_ROOT, instance.backup_directory)
    try:
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Backup directory ensured: {backup_dir}")
    except Exception as e:
        logger.error(f"Failed to create backup directory {backup_dir}: {str(e)}")