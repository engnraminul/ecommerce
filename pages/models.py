from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import F
from ckeditor_uploader.fields import RichTextUploadingField
import os
from uuid import uuid4

User = get_user_model()

def page_image_upload_path(instance, filename):
    """Generate upload path for page images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}.{ext}"
    return os.path.join('pages', 'images', filename)


class PageCategory(models.Model):
    """Category model for organizing pages"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page Category"
        verbose_name_plural = "Page Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PageTemplate(models.Model):
    """Template model for page layouts"""
    TEMPLATE_TYPES = [
        ('default', 'Default'),
        ('landing', 'Landing Page'),
        ('article', 'Article'),
        ('contact', 'Contact'),
        ('about', 'About'),
        ('faq', 'FAQ'),
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms of Service'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='default')
    template_file = models.CharField(max_length=200, help_text="Template file path relative to templates/pages/")
    description = models.TextField(blank=True)
    preview_image = models.ImageField(upload_to='pages/templates/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page Template"
        verbose_name_plural = "Page Templates"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Page(models.Model):
    """Main page model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(PageCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='pages')
    template = models.ForeignKey(PageTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Content
    content = RichTextUploadingField(config_name='pages', blank=True, help_text="Main page content with rich text editor")
    excerpt = models.TextField(max_length=500, blank=True, help_text="Short description for meta tags and previews")
    
    # Media
    featured_image = models.ImageField(upload_to=page_image_upload_path, blank=True, null=True)
    featured_image_alt = models.CharField(max_length=200, blank=True, help_text="Alt text for featured image")
    
    # SEO Fields
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (max 60 characters)")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO description (max 160 characters)")
    meta_keywords = models.CharField(max_length=200, blank=True, help_text="SEO keywords, comma separated")
    canonical_url = models.URLField(blank=True, help_text="Canonical URL for SEO")
    
    # Settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text="Show in featured pages section")
    show_in_menu = models.BooleanField(default=False, help_text="Display in main navigation menu")
    menu_order = models.PositiveIntegerField(default=0, help_text="Order in menu (0 = first)")
    allow_comments = models.BooleanField(default=False)
    require_login = models.BooleanField(default=False, help_text="Require user login to view")
    
    # Publishing
    publish_date = models.DateTimeField(default=timezone.now, help_text="Date to publish the page")
    expiry_date = models.DateTimeField(blank=True, null=True, help_text="Date when page expires (optional)")
    
    # User Management
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_pages')
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_pages')
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['publish_date']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['show_in_menu']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-generate meta fields if not provided
        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
            
        super().save(*args, **kwargs)

    def clean(self):
        # Validate publish date
        if self.publish_date and self.expiry_date:
            if self.publish_date >= self.expiry_date:
                raise ValidationError("Expiry date must be after publish date.")
        
        # Validate slug uniqueness
        if Page.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            raise ValidationError(f"A page with slug '{self.slug}' already exists.")

    def get_absolute_url(self):
        return reverse('pages_app:page_detail', kwargs={'slug': self.slug})

    @property
    def is_published(self):
        return (
            self.status == 'published' and 
            self.publish_date <= timezone.now() and
            (self.expiry_date is None or self.expiry_date > timezone.now())
        )

    @property
    def reading_time(self):
        """Estimate reading time in minutes"""
        word_count = len(self.content.split())
        return max(1, word_count // 200)  # Assuming 200 words per minute

    def increment_view_count(self):
        """Increment page view count"""
        self.view_count = F('view_count') + 1
        self.save(update_fields=['view_count'])


class PageRevision(models.Model):
    """Model to store page revisions for version control"""
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='revisions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    revision_note = models.CharField(max_length=200, blank=True, help_text="Note about this revision")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Page Revision"
        verbose_name_plural = "Page Revisions"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.page.title} - Revision {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class PageMedia(models.Model):
    """Model for page media attachments"""
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('audio', 'Audio'),
    ]

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='media')
    title = models.CharField(max_length=200)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='pages/media/')
    alt_text = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Page Media"
        verbose_name_plural = "Page Media"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.page.title} - {self.title}"

    @property
    def file_size(self):
        """Get file size in human readable format"""
        if self.file:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        return "0 B"


class PageComment(models.Model):
    """Model for page comments"""
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page Comment"
        verbose_name_plural = "Page Comments"
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.page.title}"

    @property
    def is_reply(self):
        return self.parent is not None


class PageAnalytics(models.Model):
    """Model for tracking page analytics"""
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    avg_time_on_page = models.DurationField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Page Analytics"
        verbose_name_plural = "Page Analytics"
        unique_together = ['page', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.page.title} - {self.date}"
