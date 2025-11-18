"""
Django signals for backup file cleanup
"""
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from .models import Backup
import os
import logging

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Backup)
def delete_backup_files_on_record_delete(sender, instance, **kwargs):
    """
    Signal handler to delete backup files when a Backup record is deleted.
    This handles both individual and bulk deletions.
    """
    try:
        files_deleted = instance.delete_backup_files()
        if files_deleted:
            logger.info(f"Deleted backup files for '{instance.name}': {', '.join(files_deleted)}")
        else:
            logger.info(f"No files to delete for backup '{instance.name}'")
    except Exception as e:
        logger.error(f"Error deleting backup files for '{instance.name}': {str(e)}")


# For bulk deletions, we need to handle each instance individually
@receiver(pre_delete, sender=Backup)
def log_backup_deletion(sender, instance, **kwargs):
    """
    Log backup deletion for audit purposes
    """
    logger.info(f"Deleting backup record: {instance.name} (ID: {instance.id})")