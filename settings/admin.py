from django.contrib import admin
from .models import Curier, CheckoutCustomization

@admin.register(Curier)
class CurierAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_url', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'api_url')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CheckoutCustomization)
class CheckoutCustomizationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Page Header', {
            'fields': ('page_title', 'page_subtitle', 'show_breadcrumb')
        }),
        ('Customer Information', {
            'fields': (
                'customer_section_title',
                ('full_name_label', 'full_name_placeholder', 'full_name_default'),
                ('email_label', 'email_placeholder', 'email_default'),
                ('phone_label', 'phone_placeholder', 'phone_default'),
            )
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_section_title',
                'address_label', 'address_placeholder', 'address_default',
            )
        }),
        ('Order Instructions', {
            'fields': (
                'instructions_section_title',
                'instructions_label', 'instructions_placeholder', 'instructions_help_text',
            )
        }),
        ('Shipping Method', {
            'fields': (
                'shipping_method_section_title',
                'delivery_location_label',
                'dhaka_location_label', 'outside_location_label',
            )
        }),
        ('Payment Methods', {
            'fields': (
                'payment_section_title',
                'cod_label', 'bkash_label', 'nagad_label',
                'bkash_merchant_number', 'nagad_merchant_number',
            )
        }),
        ('Payment Instructions', {
            'fields': ('bkash_instructions', 'nagad_instructions', 'cod_instructions'),
            'classes': ('collapse',)
        }),
        ('Payment Form Fields', {
            'fields': (
                ('bkash_transaction_label', 'bkash_transaction_placeholder'),
                ('bkash_sender_label', 'bkash_sender_placeholder'),
                ('nagad_transaction_label', 'nagad_transaction_placeholder'),
                ('nagad_sender_label', 'nagad_sender_placeholder'),
            ),
            'classes': ('collapse',)
        }),
        ('Order Summary', {
            'fields': (
                'order_summary_title', 'show_order_summary',
                'subtotal_label', 'shipping_label', 'tax_label', 'total_label',
                'place_order_button_text',
            )
        }),
        ('Trust & Security', {
            'fields': (
                'show_security_badges', 'show_trust_badges',
                'security_ssl_text', 'security_safe_text',
                'trust_section_title',
                ('fast_shipping_title', 'fast_shipping_description'),
                ('easy_returns_title', 'easy_returns_description'),
                ('support_title', 'support_description'),
            ),
            'classes': ('collapse',)
        }),
        ('Breadcrumb', {
            'fields': ('breadcrumb_home', 'breadcrumb_cart', 'breadcrumb_checkout'),
            'classes': ('collapse',)
        }),
        ('Theme Colors', {
            'fields': ('primary_color', 'button_color', 'background_color'),
            'classes': ('collapse',)
        }),
        ('Messages', {
            'fields': (
                'loading_cart_message', 'loading_shipping_message', 'processing_order_message',
                'order_success_message', 'order_error_message', 'validation_error_message',
            ),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # Deactivate all other customizations if this one is being activated
        if obj.is_active:
            CheckoutCustomization.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)
