from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    PageCategory, PageTemplate, Page, PageRevision, 
    PageMedia, PageAnalytics
)


@admin.register(PageCategory)
class PageCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'pages_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']

    def pages_count(self, obj):
        return obj.pages.count()
    pages_count.short_description = 'Pages Count'


@admin.register(PageTemplate)
class PageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'template_file', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


class PageMediaInline(admin.TabularInline):
    model = PageMedia
    extra = 0
    fields = ['title', 'media_type', 'file', 'alt_text', 'order', 'is_featured']
    readonly_fields = ['uploaded_by', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


class PageRevisionInline(admin.TabularInline):
    model = PageRevision
    extra = 0
    fields = ['title', 'revision_note', 'created_by', 'created_at']
    readonly_fields = ['created_by', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'status', 'category', 'author', 'is_featured', 
        'show_in_menu', 'view_count', 'publish_date', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'is_featured', 'show_in_menu', 
        'require_login', 'created_at', 'publish_date'
    ]
    search_fields = ['title', 'content', 'meta_title', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'template', 'status')
        }),
        ('Content', {
            'fields': ('content', 'excerpt')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt'),
            'classes': ('collapse',)
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        ('Page Settings', {
            'fields': (
                'is_featured', 'show_in_menu', 'menu_order', 
                'require_login'
            ),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('publish_date', 'expiry_date')
        }),
        ('Analytics', {
            'fields': ('view_count', 'share_count'),
            'classes': ('collapse',)
        }),
        ('Management', {
            'fields': ('author', 'last_modified_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['view_count', 'share_count', 'created_at', 'updated_at', 'last_modified_by']
    inlines = [PageMediaInline, PageRevisionInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.author = request.user
        else:  # If updating existing object
            obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'author', 'template')

    actions = ['publish_pages', 'unpublish_pages', 'feature_pages', 'unfeature_pages']

    def publish_pages(self, request, queryset):
        updated = queryset.update(status='published', publish_date=timezone.now())
        self.message_user(request, f'{updated} pages were successfully published.')
    publish_pages.short_description = "Publish selected pages"

    def unpublish_pages(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} pages were unpublished.')
    unpublish_pages.short_description = "Unpublish selected pages"

    def feature_pages(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} pages were featured.')
    feature_pages.short_description = "Feature selected pages"

    def unfeature_pages(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} pages were unfeatured.')
    unfeature_pages.short_description = "Unfeature selected pages"


@admin.register(PageRevision)
class PageRevisionAdmin(admin.ModelAdmin):
    list_display = ['page', 'title', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['page__title', 'title', 'content']
    readonly_fields = ['created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PageMedia)
class PageMediaAdmin(admin.ModelAdmin):
    list_display = ['title', 'page', 'media_type', 'file_size_display', 'is_featured', 'uploaded_by', 'created_at']
    list_filter = ['media_type', 'is_featured', 'created_at']
    search_fields = ['title', 'page__title', 'alt_text']
    readonly_fields = ['uploaded_by', 'created_at', 'file_size_display']

    def file_size_display(self, obj):
        return obj.file_size
    file_size_display.short_description = 'File Size'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PageAnalytics)
class PageAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['page', 'date', 'views', 'unique_views', 'bounce_rate']
    list_filter = ['date', 'page']
    search_fields = ['page__title']
    readonly_fields = ['page', 'date', 'views', 'unique_views', 'bounce_rate', 'avg_time_on_page']
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
