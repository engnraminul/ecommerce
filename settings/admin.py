from django.contrib import admin
from .models import HeroContent, SiteSettings, Curier, CheckoutCustomization


@admin.register(HeroContent)
class HeroContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_order', 'is_active', 'has_images', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('title', 'subtitle')
    
    fieldsets = (
        ('Hero Content', {
            'fields': ('title', 'subtitle'),
            'description': 'Main text content displayed on the hero slide'
        }),
        ('Hero Images', {
            'fields': ('desktop_image', 'mobile_image'),
            'description': '''
            <strong>Image Guidelines:</strong><br>
            • Desktop Image: Recommended size 1920x600px (wide landscape)<br>
            • Mobile Image: Recommended size 800x600px (square/portrait oriented)<br>
            • Upload images to media/hero/ folder and enter the path here<br>
            • Example: media/hero/desktop-hero-1.jpg
            '''
        }),
        ('Call-to-Action Buttons', {
            'fields': (
                ('primary_button_text', 'primary_button_url'),
                ('secondary_button_text', 'secondary_button_url'),
            ),
            'description': 'Configure the action buttons displayed on the hero slide'
        }),
        ('Styling Options', {
            'fields': (
                ('text_color', 'text_shadow'),
                ('background_color', 'background_gradient'),
            ),
            'description': 'Visual styling options for text and background',
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active'),
            'description': 'Control when and in what order this slide appears'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_images(self, obj):
        """Display if the slide has images"""
        if obj.desktop_image and obj.mobile_image:
            return "✓ Both"
        elif obj.desktop_image:
            return "Desktop only"
        elif obj.mobile_image:
            return "Mobile only"
        return "No images"
    has_images.short_description = "Images"
    
    def get_queryset(self, request):
        """Order queryset by display_order"""
        return super().get_queryset(request).order_by('display_order', 'created_at')
    
    class Media:
        css = {
            'all': ('admin/css/hero_admin.css',)
        }


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Site Identity', {
            'fields': ('site_name', 'site_tagline', 'site_logo', 'site_favicon')
        }),
        ('Contact Information', {
            'fields': ('contact_phone', 'contact_email', 'contact_address')
        }),
        ('Footer Information', {
            'fields': ('footer_logo', 'footer_short_text', 'facebook_link', 'youtube_link')
        }),
        ('Quick Links Configuration', {
            'fields': (
                'quick_links_title', 'customer_service_title',
                ('home_text', 'home_url'),
                ('products_text', 'products_url'),
                ('categories_text', 'categories_url'),
                ('about_text', 'about_url'),
                ('contact_text', 'contact_url'),
            )
        }),
        ('Customer Service Links', {
            'fields': (
                ('track_order_text', 'track_order_url'),
                ('return_policy_text', 'return_policy_url'),
                ('shipping_info_text', 'shipping_info_url'),
                ('fraud_checker_text', 'fraud_checker_url'),
                ('faq_text', 'faq_url'),
            ),
            'classes': ('collapse',)
        }),
        ('Footer Copyright', {
            'fields': ('copyright_text',),
            'description': 'Use {year} to automatically display current year'
        }),
        ('Home Page Features', {
            'fields': (
                'why_shop_section_title',
                ('feature1_title', 'feature1_subtitle'),
                ('feature2_title', 'feature2_subtitle'),
                ('feature3_title', 'feature3_subtitle'),
                ('feature4_title', 'feature4_subtitle'),
            ),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # Deactivate all other site settings if this one is being activated
        if obj.is_active:
            SiteSettings.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(Curier)
class CurierAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_url_short', 'has_credentials', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'api_url')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Courier Information', {
            'fields': ('name', 'api_url', 'is_active'),
            'description': 'Basic courier service configuration'
        }),
        ('API Credentials', {
            'fields': ('api_key', 'secret_key'),
            'description': '''
            <strong>Fraud Checker API Integration:</strong><br>
            • These credentials are used for Packzy fraud checking API<br>
            • API endpoint: https://portal.packzy.com/api/v1/fraud_check/{phone_number}<br>
            • Headers required: api-key and secret-key<br>
            • For SteadFast courier integration, name should contain "steadfast" or "packzy"
            '''
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def api_url_short(self, obj):
        """Display shortened API URL"""
        if len(obj.api_url) > 50:
            return obj.api_url[:47] + '...'
        return obj.api_url
    api_url_short.short_description = 'API URL'
    
    def has_credentials(self, obj):
        """Check if courier has both API key and secret key"""
        return bool(obj.api_key and obj.secret_key)
    has_credentials.boolean = True
    has_credentials.short_description = 'Has Credentials'
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form to show help text for fraud checker integration"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add help text for API credentials
        if 'api_key' in form.base_fields:
            form.base_fields['api_key'].help_text = 'API Key for fraud checking service (e.g., Packzy/SteadFast API)'
        
        if 'secret_key' in form.base_fields:
            form.base_fields['secret_key'].help_text = 'Secret Key for fraud checking service (e.g., Packzy/SteadFast API)'
        
        if 'name' in form.base_fields:
            form.base_fields['name'].help_text = 'Courier name (use "SteadFast" or "Packzy" for fraud checker integration)'
        
        return form


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
