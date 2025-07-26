from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem, SavedItem, Coupon, CouponUsage


class CartItemInline(admin.TabularInline):
    """Inline for cart items"""
    model = CartItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Cart admin"""
    list_display = ('__str__', 'user', 'total_items', 'subtotal', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'session_id')
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'subtotal', 'total_weight')
    
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Cart Info', {
            'fields': ('user', 'session_id')
        }),
        ('Summary', {
            'fields': ('total_items', 'subtotal', 'total_weight'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Cart Item admin"""
    list_display = ('cart', 'product', 'variant', 'quantity', 'unit_price', 'total_price', 'is_available')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'cart__user__username')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    
    def is_available(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green;">✓ Available</span>')
        else:
            return format_html('<span style="color: red;">✗ Out of Stock</span>')
    is_available.short_description = "Availability"


@admin.register(SavedItem)
class SavedItemAdmin(admin.ModelAdmin):
    """Saved Item admin"""
    list_display = ('user', 'product', 'variant', 'quantity', 'unit_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at',)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Coupon admin"""
    list_display = (
        'code', 'name', 'discount_type', 'discount_value', 
        'usage_status', 'valid_from', 'valid_until', 'is_active'
    )
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'name')
    readonly_fields = ('used_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('code', 'name', 'description')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'maximum_discount_amount')
        }),
        ('Usage Limits', {
            'fields': ('minimum_order_amount', 'usage_limit', 'usage_limit_per_user', 'used_count')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_coupons', 'deactivate_coupons']
    
    def usage_status(self, obj):
        if obj.usage_limit:
            percentage = (obj.used_count / obj.usage_limit) * 100
            color = 'green' if percentage < 50 else 'orange' if percentage < 90 else 'red'
            return format_html(
                '<span style="color: {};">{}/{} ({}%)</span>',
                color, obj.used_count, obj.usage_limit, int(percentage)
            )
        return f"{obj.used_count} uses"
    usage_status.short_description = "Usage"
    
    def activate_coupons(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} coupons activated.")
    activate_coupons.short_description = "Activate selected coupons"
    
    def deactivate_coupons(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} coupons deactivated.")
    deactivate_coupons.short_description = "Deactivate selected coupons"


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    """Coupon Usage admin"""
    list_display = ('coupon', 'user', 'order_id', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('coupon__code', 'user__username', 'order_id')
    readonly_fields = ('used_at',)
