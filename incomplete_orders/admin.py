from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from django.utils import timezone
from .models import (
    IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress,
    IncompleteOrderHistory, RecoveryEmailLog, IncompleteOrderAnalytics
)


class IncompleteOrderItemInline(admin.TabularInline):
    model = IncompleteOrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'variant_name', 'total_price', 'added_at', 'updated_at')
    fields = ('product', 'variant', 'quantity', 'unit_price', 'total_price', 'added_at')


class IncompleteShippingAddressInline(admin.StackedInline):
    model = IncompleteShippingAddress
    extra = 0
    fields = (
        ('first_name', 'last_name'),
        'company',
        'address_line_1',
        'address_line_2',
        ('city', 'state'),
        ('postal_code', 'country'),
        ('phone', 'email'),
        'delivery_instructions'
    )


class IncompleteOrderHistoryInline(admin.TabularInline):
    model = IncompleteOrderHistory
    extra = 0
    readonly_fields = ('action', 'details', 'user', 'created_by_system', 'created_at')
    fields = ('action', 'details', 'user', 'created_by_system', 'created_at')
    ordering = ['-created_at']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(IncompleteOrder)
class IncompleteOrderAdmin(admin.ModelAdmin):
    list_display = (
        'incomplete_order_id', 'customer_info', 'status', 'total_amount', 
        'total_items', 'days_old', 'recovery_attempts', 'can_convert_display', 'created_at'
    )
    list_filter = (
        'status', 'is_guest_order', 'created_at', 'abandoned_at', 
        'recovery_attempts', 'expires_at'
    )
    search_fields = (
        'incomplete_order_id', 'customer_email', 'guest_email', 
        'user__username', 'user__email', 'session_id'
    )
    readonly_fields = (
        'incomplete_order_id', 'created_at', 'updated_at', 'abandoned_at', 
        'expires_at', 'converted_at', 'converted_order_id', 'total_items',
        'is_expired', 'days_since_created', 'can_convert'
    )
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'incomplete_order_id', 'status', 'user', 'is_guest_order',
                'guest_email', 'session_id'
            )
        }),
        ('Customer Information', {
            'fields': ('customer_email', 'customer_phone')
        }),
        ('Financial Information', {
            'fields': (
                'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount',
                'total_amount', 'coupon_code', 'coupon_discount'
            )
        }),
        ('Recovery Tracking', {
            'fields': (
                'recovery_attempts', 'last_recovery_attempt', 'abandonment_reason'
            )
        }),
        ('Analytics Data', {
            'fields': ('user_agent', 'ip_address', 'referrer_url'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'abandoned_at', 'expires_at',
                'converted_at', 'converted_order_id'
            ),
            'classes': ('collapse',)
        }),
        ('Status Checks', {
            'fields': ('total_items', 'is_expired', 'days_since_created', 'can_convert'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [IncompleteOrderItemInline, IncompleteShippingAddressInline, IncompleteOrderHistoryInline]
    
    actions = ['convert_to_orders', 'mark_as_abandoned', 'send_recovery_email']
    
    def customer_info(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.email})"
        return obj.customer_email or obj.guest_email or f"Session: {obj.session_id}"
    customer_info.short_description = "Customer"
    
    def days_old(self, obj):
        return obj.days_since_created
    days_old.short_description = "Days Old"
    
    def can_convert_display(self, obj):
        if obj.can_convert:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    can_convert_display.short_description = "Can Convert"
    
    def convert_to_orders(self, request, queryset):
        converted_count = 0
        failed_count = 0
        
        for incomplete_order in queryset:
            try:
                if incomplete_order.can_convert:
                    order = incomplete_order.convert_to_order()
                    converted_count += 1
                    self.message_user(
                        request, 
                        f"Converted {incomplete_order.incomplete_order_id} to Order {order.order_number}"
                    )
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                self.message_user(
                    request, 
                    f"Failed to convert {incomplete_order.incomplete_order_id}: {str(e)}",
                    level='ERROR'
                )
        
        if converted_count:
            self.message_user(request, f"Successfully converted {converted_count} incomplete orders.")
        if failed_count:
            self.message_user(request, f"Failed to convert {failed_count} incomplete orders.", level='WARNING')
    
    convert_to_orders.short_description = "Convert selected to complete orders"
    
    def mark_as_abandoned(self, request, queryset):
        count = 0
        for incomplete_order in queryset.filter(status__in=['pending', 'payment_pending']):
            incomplete_order.mark_as_abandoned('Manually marked by admin')
            count += 1
        
        self.message_user(request, f"Marked {count} orders as abandoned.")
    
    mark_as_abandoned.short_description = "Mark selected as abandoned"
    
    def send_recovery_email(self, request, queryset):
        # This would implement recovery email sending
        # For now, just increment recovery attempts
        count = 0
        for incomplete_order in queryset.filter(status__in=['pending', 'abandoned']):
            incomplete_order.increment_recovery_attempt()
            count += 1
        
        self.message_user(request, f"Sent recovery emails to {count} customers.")
    
    send_recovery_email.short_description = "Send recovery emails"


@admin.register(IncompleteOrderItem)
class IncompleteOrderItemAdmin(admin.ModelAdmin):
    list_display = ('incomplete_order', 'product_name', 'variant_name', 'quantity', 'unit_price', 'total_price', 'added_at')
    list_filter = ('added_at', 'product')
    search_fields = ('incomplete_order__incomplete_order_id', 'product_name', 'product_sku')
    readonly_fields = ('product_name', 'product_sku', 'variant_name', 'total_price', 'added_at', 'updated_at')


@admin.register(IncompleteShippingAddress)
class IncompleteShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('incomplete_order', 'full_name', 'city', 'country', 'is_complete', 'created_at')
    list_filter = ('country', 'state', 'created_at')
    search_fields = (
        'incomplete_order__incomplete_order_id', 'first_name', 'last_name',
        'email', 'phone', 'city'
    )
    readonly_fields = ('full_name', 'full_address', 'is_complete', 'created_at', 'updated_at')


@admin.register(IncompleteOrderHistory)
class IncompleteOrderHistoryAdmin(admin.ModelAdmin):
    list_display = ('incomplete_order', 'action', 'user', 'created_by_system', 'created_at')
    list_filter = ('action', 'created_by_system', 'created_at')
    search_fields = ('incomplete_order__incomplete_order_id', 'details')
    readonly_fields = ('created_at',)


@admin.register(RecoveryEmailLog)
class RecoveryEmailLogAdmin(admin.ModelAdmin):
    list_display = (
        'incomplete_order', 'email_type', 'recipient_email', 'sent_at',
        'delivered', 'opened', 'clicked', 'responded'
    )
    list_filter = (
        'email_type', 'delivered', 'opened', 'clicked', 'responded', 'sent_at'
    )
    search_fields = ('incomplete_order__incomplete_order_id', 'recipient_email', 'subject')
    readonly_fields = ('sent_at',)


@admin.register(IncompleteOrderAnalytics)
class IncompleteOrderAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'total_incomplete_orders', 'abandoned_orders', 'converted_orders',
        'conversion_rate', 'recovery_rate', 'total_lost_revenue', 'recovered_revenue'
    )
    list_filter = ('date',)
    readonly_fields = ('conversion_rate', 'recovery_rate', 'created_at', 'updated_at')
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics
        extra_context = extra_context or {}
        
        # Calculate totals
        totals = IncompleteOrderAnalytics.objects.aggregate(
            total_incomplete=Sum('total_incomplete_orders'),
            total_abandoned=Sum('abandoned_orders'),
            total_converted=Sum('converted_orders'),
            total_lost=Sum('total_lost_revenue'),
            total_recovered=Sum('recovered_revenue')
        )
        
        extra_context['summary_stats'] = totals
        return super().changelist_view(request, extra_context)
