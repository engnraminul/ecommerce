from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product, ProductImage, ProductVariant, Review, Wishlist


class ProductImageInline(admin.TabularInline):
    """Inline for product images"""
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Preview"


class ProductVariantInline(admin.TabularInline):
    """Inline for product variants"""
    model = ProductVariant
    extra = 0
    fields = ('name', 'sku', 'size', 'color', 'price', 'stock_quantity', 'is_active', 'image')
    readonly_fields = ('sku',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin"""
    list_display = ('name', 'parent', 'is_active', 'product_count', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin with enhanced features"""
    list_display = (
        'name', 'sku', 'category', 'price', 'stock_quantity', 
        'is_active', 'is_featured', 'stock_status', 'created_at'
    )
    list_filter = (
        'is_active', 'is_featured', 'is_digital', 'category', 
        'created_at', 'track_inventory'
    )
    search_fields = ('name', 'sku', 'description', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('sku', 'created_at', 'updated_at', 'average_rating', 'review_count')
    
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'sku', 'category', 'description', 'short_description')
        }),
        ('Identification', {
            'fields': ('barcode',),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'low_stock_threshold', 'track_inventory')
        }),
        ('Physical Attributes', {
            'fields': ('weight', 'dimensions', 'is_digital'),
            'classes': ('collapse',)
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('average_rating', 'review_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_featured', 'mark_as_not_featured', 'mark_as_active', 'mark_as_inactive']
    
    def stock_status(self, obj):
        if not obj.track_inventory:
            return format_html('<span style="color: blue;">Not Tracked</span>')
        elif obj.stock_quantity == 0:
            return format_html('<span style="color: red;">Out of Stock</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange;">Low Stock</span>')
        else:
            return format_html('<span style="color: green;">In Stock</span>')
    stock_status.short_description = "Stock Status"
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} products marked as featured.")
    mark_as_featured.short_description = "Mark selected products as featured"
    
    def mark_as_not_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} products marked as not featured.")
    mark_as_not_featured.short_description = "Mark selected products as not featured"
    
    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} products marked as active.")
    mark_as_active.short_description = "Mark selected products as active"
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} products marked as inactive.")
    mark_as_inactive.short_description = "Mark selected products as inactive"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Product Image admin"""
    list_display = ('product', 'alt_text', 'is_primary', 'image_preview', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__name', 'alt_text')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Product Variant admin"""
    list_display = ('product', 'name', 'sku', 'size', 'color', 'price', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'size', 'color', 'material')
    search_fields = ('product__name', 'name', 'sku')
    readonly_fields = ('sku', 'created_at', 'updated_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Product Review admin"""
    list_display = ('product', 'user', 'rating', 'is_approved', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_verified_purchase', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} reviews approved.")
    approve_reviews.short_description = "Approve selected reviews"
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} reviews disapproved.")
    disapprove_reviews.short_description = "Disapprove selected reviews"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Wishlist admin"""
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')
