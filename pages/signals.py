from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Page, PageAnalytics, PageRevision


@receiver(post_save, sender=Page)
def create_page_analytics(sender, instance, created, **kwargs):
    """Create analytics entry for new pages"""
    if created and instance.status == 'published':
        PageAnalytics.objects.get_or_create(
            page=instance,
            date=timezone.now().date(),
            defaults={
                'views': 0,
                'unique_views': 0,
                'bounce_rate': 0.00
            }
        )


@receiver(post_save, sender=Page)
def create_initial_revision(sender, instance, created, **kwargs):
    """Create initial revision for new pages"""
    if created:
        PageRevision.objects.create(
            page=instance,
            title=instance.title,
            content=instance.content,
            excerpt=instance.excerpt,
            meta_title=instance.meta_title,
            meta_description=instance.meta_description,
            revision_note="Initial version",
            created_by=instance.author
        )


@receiver(pre_delete, sender=Page)
def cleanup_page_files(sender, instance, **kwargs):
    """Clean up associated files when page is deleted"""
    # Delete featured image
    if instance.featured_image:
        instance.featured_image.delete(save=False)
    
    # Delete media files
    for media in instance.media.all():
        if media.file:
            media.file.delete(save=False)