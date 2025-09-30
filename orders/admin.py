from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem, ShippingAddress, OrderStatusHistory, Invoice, RefundRequest


class OrderItemInline(admin.TabularInline):
    """Inline for order items"""
    model = OrderItem
    extra = 0
    fields = ('product', 'variant', 'product_name', 'variant_name', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('product_name', 'variant_name', 'total_price')


class ShippingAddressInline(admin.StackedInline):
    """Inline for shipping address"""
    model = ShippingAddress
    extra = 0
    fields = (
        ('first_name', 'last_name'),
        'company',
        'address_line_1',
        'address_line_2',
        ('city', 'state', 'postal_code'),
        'country',
        ('phone', 'email'),
        'delivery_instructions'
    )


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline for order status history"""
    model = OrderStatusHistory
    extra = 0
    fields = ('status', 'title', 'description', 'changed_by', 'tracking_number', 'carrier', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order admin with comprehensive features"""
    list_display = (
        'order_number', 'user', 'status', 'payment_status', 
        'total_amount', 'total_items', 'created_at'
    )
    list_filter = (
        'status', 'payment_status', 'created_at', 
        'confirmed_at', 'shipped_at', 'delivered_at'
    )
    search_fields = (
        'order_number', 'user__username', 'user__email', 
        'customer_email', 'coupon_code'
    )
    readonly_fields = (
        'order_number', 'created_at', 'updated_at', 
        'confirmed_at', 'shipped_at', 'delivered_at',
        'total_items', 'can_cancel'
    )
    
    inlines = [OrderItemInline, ShippingAddressInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'shipping_cost', 'tax_amount', 
                'discount_amount', 'coupon_code', 'coupon_discount', 'total_amount', 'cost_price'
            )
        }),
        ('Customer Info', {
            'fields': ('customer_email', 'customer_phone')
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Order Status', {
            'fields': ('can_cancel',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'confirmed_at', 
                'shipped_at', 'delivered_at'
            ),
            'classes': ('collapse',)
        }),
        ('Courier Details', {
            'fields': ('curier_id', 'curier_charge', 'curier_status', 'partially_ammount', 'curier_date'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = "Items"
    
    def mark_as_confirmed(self, request, queryset):
        from django.utils import timezone
        count = 0
        for order in queryset.filter(status='pending'):
            order.status = 'confirmed'
            order.confirmed_at = timezone.now()
            order.save()
            # Status history will be created automatically by signals
            count += 1
        self.message_user(request, f"{count} orders marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected orders as confirmed"
    
    def mark_as_shipped(self, request, queryset):
        from django.utils import timezone
        count = 0
        for order in queryset.filter(status__in=['confirmed', 'processing']):
            order.status = 'shipped'
            order.shipped_at = timezone.now()
            order.save()
            count += 1
        self.message_user(request, f"{count} orders marked as shipped.")
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        from django.utils import timezone
        count = 0
        for order in queryset.filter(status='shipped'):
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.save()
            count += 1
        self.message_user(request, f"{count} orders marked as delivered.")
    mark_as_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_as_cancelled(self, request, queryset):
        count = 0
        for order in queryset:
            if order.can_cancel:
                order.status = 'cancelled'
                order.save()
                count += 1
        self.message_user(request, f"{count} orders cancelled.")
    mark_as_cancelled.short_description = "Cancel selected orders"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Order Item admin"""
    list_display = ('order', 'product_name', 'variant_name', 'quantity', 'unit_price', 'total_price')
    list_filter = ('created_at',)
    search_fields = ('order__order_number', 'product_name', 'product__name')
    readonly_fields = ('total_price', 'created_at')


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    """Shipping Address admin"""
    list_display = ('order', 'full_name', 'city', 'state', 'country', 'phone')
    list_filter = ('country', 'state')
    search_fields = ('first_name', 'last_name', 'city', 'order__order_number')
    readonly_fields = ('created_at', 'full_name', 'full_address')
    
    fieldsets = (
        ('Order', {
            'fields': ('order',)
        }),
        ('Recipient Info', {
            'fields': ('first_name', 'last_name', 'company', 'full_name')
        }),
        ('Address', {
            'fields': (
                'address_line_1', 'address_line_2', 
                'city', 'state', 'postal_code', 'country', 'full_address'
            )
        }),
        ('Contact', {
            'fields': ('phone', 'email')
        }),
        ('Delivery', {
            'fields': ('delivery_instructions',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Order Status History admin"""
    list_display = ('order', 'status', 'title', 'changed_by', 'tracking_number', 'created_at')
    list_filter = ('status', 'created_at', 'carrier', 'is_milestone', 'is_customer_visible')
    search_fields = ('order__order_number', 'description', 'tracking_number', 'title')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Order & Status', {
            'fields': ('order', 'status', 'title', 'description')
        }),
        ('Change Info', {
            'fields': ('changed_by', 'is_system_generated')
        }),
        ('Tracking Details', {
            'fields': ('tracking_number', 'carrier', 'carrier_url', 'location', 'estimated_delivery')
        }),
        ('Visibility', {
            'fields': ('is_milestone', 'is_customer_visible')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Invoice admin"""
    list_display = ('invoice_number', 'order', 'billing_name', 'billing_email', 'invoice_date')
    search_fields = ('invoice_number', 'order__order_number', 'billing_name', 'billing_email')
    readonly_fields = ('invoice_number', 'invoice_date', 'created_at')
    
    fieldsets = (
        ('Invoice Info', {
            'fields': ('invoice_number', 'order', 'invoice_date')
        }),
        ('Billing Info', {
            'fields': ('billing_name', 'billing_email', 'billing_address')
        }),
        ('Files', {
            'fields': ('invoice_file',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    """Refund Request admin"""
    list_display = (
        'order', 'user', 'refund_amount', 'reason', 
        'status', 'created_at', 'processed_by'
    )
    list_filter = ('status', 'reason', 'created_at', 'processed_at')
    search_fields = ('order__order_number', 'user__username', 'description', 'admin_response')
    readonly_fields = ('created_at', 'updated_at', 'processed_at')
    
    fieldsets = (
        ('Request Info', {
            'fields': ('order', 'user', 'refund_amount', 'reason')
        }),
        ('Request Details', {
            'fields': ('description',)
        }),
        ('Admin Response', {
            'fields': ('status', 'admin_response', 'processed_by', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_refunds', 'reject_refunds']
    
    def approve_refunds(self, request, queryset):
        from django.utils import timezone
        count = 0
        for refund in queryset.filter(status='pending'):
            refund.status = 'approved'
            refund.processed_by = request.user
            refund.processed_at = timezone.now()
            if not refund.admin_response:
                refund.admin_response = f"Approved by {request.user.username}"
            refund.save()
            count += 1
        self.message_user(request, f"{count} refund requests approved.")
    approve_refunds.short_description = "Approve selected refund requests"
    
    def reject_refunds(self, request, queryset):
        from django.utils import timezone
        count = 0
        for refund in queryset.filter(status='pending'):
            refund.status = 'rejected'
            refund.processed_by = request.user
            refund.processed_at = timezone.now()
            if not refund.admin_response:
                refund.admin_response = f"Rejected by {request.user.username}"
            refund.save()
            count += 1
        self.message_user(request, f"{count} refund requests rejected.")
    reject_refunds.short_description = "Reject selected refund requests"
