from django.db import models

class HeroContent(models.Model):
    """Model for storing hero carousel content with desktop and mobile images"""
    
    # Basic Content
    title = models.CharField(
        max_length=200, 
        default="Welcome to Our Store",
        help_text="Main headline for the hero slide"
    )
    subtitle = models.CharField(
        max_length=300, 
        default="Discover amazing products at unbeatable prices",
        help_text="Supporting text below the main headline"
    )
    
    # Desktop Image
    desktop_image = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Path to desktop hero image (e.g., media/hero/desktop-hero-1.jpg) - Recommended size: 1920x600px"
    )
    
    # Mobile Image  
    mobile_image = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Path to mobile hero image (e.g., media/hero/mobile-hero-1.jpg) - Recommended size: 800x600px"
    )
    
    # Call-to-Action Buttons
    primary_button_text = models.CharField(
        max_length=100, 
        default="Shop Now",
        help_text="Text for the primary action button"
    )
    primary_button_url = models.CharField(
        max_length=200, 
        default="/products/",
        help_text="URL for the primary button (e.g., /products/ or external URL)"
    )
    
    secondary_button_text = models.CharField(
        max_length=100, 
        default="Browse Categories",
        help_text="Text for the secondary action button"
    )
    secondary_button_url = models.CharField(
        max_length=200, 
        default="/categories/",
        help_text="URL for the secondary button (e.g., /categories/ or external URL)"
    )
    
    # Display Settings
    text_color = models.CharField(
        max_length=7, 
        default="#ffffff",
        help_text="Text color for title and subtitle (hex color code)"
    )
    text_shadow = models.BooleanField(
        default=True,
        help_text="Add text shadow for better readability over images"
    )
    
    # Background Settings (used when no image is provided)
    background_color = models.CharField(
        max_length=7, 
        default="#930000",
        help_text="Background color when no image is available (hex color code)"
    )
    background_gradient = models.CharField(
        max_length=200, 
        default="linear-gradient(135deg, #930000, #7a0000)",
        help_text="CSS gradient for background (overrides background_color)"
    )
    
    # Order and Status
    display_order = models.PositiveIntegerField(
        default=1,
        help_text="Order in which this slide appears (1 = first, 2 = second, etc.)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this hero slide is active and should be displayed"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Hero Content"
        verbose_name_plural = "Hero Content"
        ordering = ['display_order', 'created_at']
    
    def __str__(self):
        return f"Hero Slide: {self.title} (Order: {self.display_order})"
    
    @classmethod
    def get_active_slides(cls):
        """Get all active hero slides ordered by display_order"""
        return cls.objects.filter(is_active=True).order_by('display_order')
    
    def get_desktop_image_url(self):
        """Get the full URL for desktop image"""
        if self.desktop_image:
            if self.desktop_image.startswith('http'):
                return self.desktop_image
            return f"/{self.desktop_image.lstrip('/')}"
        return None
    
    def get_mobile_image_url(self):
        """Get the full URL for mobile image"""
        if self.mobile_image:
            if self.mobile_image.startswith('http'):
                return self.mobile_image
            return f"/{self.mobile_image.lstrip('/')}"
        return None
    
    def has_images(self):
        """Check if this slide has at least one image"""
        return bool(self.desktop_image or self.mobile_image)


class SiteSettings(models.Model):
    """Model for storing general site settings and content"""
    
    # Site Identity
    site_name = models.CharField(max_length=200, default="My Brand Store")
    site_tagline = models.CharField(max_length=300, default="Your one-stop shop for quality products")
    site_logo = models.CharField(max_length=500, blank=True, null=True, help_text="Path to site logo image (e.g., media/logos/site-logo.png)")
    site_favicon = models.CharField(max_length=500, blank=True, null=True, help_text="Path to favicon image (e.g., media/icons/favicon.ico)")
    
    # Contact Information
    contact_phone = models.CharField(max_length=20, default="+1 123-456-7890")
    contact_email = models.EmailField(default="contact@mybrandstore.com")
    contact_address = models.TextField(default="123 Main Street, City, State 12345, Country")
    
    # Footer Information
    footer_logo = models.CharField(max_length=500, blank=True, null=True, help_text="Path to footer logo image (e.g., media/logos/footer-logo.png)")
    footer_short_text = models.TextField(default="Brief description about your store that appears in the footer")
    facebook_link = models.URLField(blank=True, null=True, help_text="Facebook page URL")
    youtube_link = models.URLField(blank=True, null=True, help_text="YouTube channel URL")
    
    # Quick Links Configuration
    quick_links_title = models.CharField(max_length=100, default="Quick Links")
    customer_service_title = models.CharField(max_length=100, default="Customer Service")
    
    # Quick Links - Text and URLs
    home_text = models.CharField(max_length=50, default="Home")
    home_url = models.CharField(max_length=200, default="/")
    
    products_text = models.CharField(max_length=50, default="Products")
    products_url = models.CharField(max_length=200, default="/products")
    
    categories_text = models.CharField(max_length=50, default="Categories")
    categories_url = models.CharField(max_length=200, default="/categories")
    
    about_text = models.CharField(max_length=50, default="About Us")
    about_url = models.CharField(max_length=200, default="/about")
    
    contact_text = models.CharField(max_length=50, default="Contact")
    contact_url = models.CharField(max_length=200, default="/contact")
    
    # Customer Service Links
    track_order_text = models.CharField(max_length=50, default="Track Order")
    track_order_url = models.CharField(max_length=200, default="/track-order")
    
    return_policy_text = models.CharField(max_length=50, default="Return Policy")
    return_policy_url = models.CharField(max_length=200, default="/return-policy")
    
    shipping_info_text = models.CharField(max_length=50, default="Shipping Info")
    shipping_info_url = models.CharField(max_length=200, default="/shipping-info")
    
    fraud_checker_text = models.CharField(max_length=50, default="Fraud Checker")
    fraud_checker_url = models.CharField(max_length=200, default="/fraud-checker")
    
    faq_text = models.CharField(max_length=50, default="FAQ")
    faq_url = models.CharField(max_length=200, default="/faq")
    
    # Footer Copyright
    copyright_text = models.CharField(max_length=200, default="© 2024 My Brand Store. All rights reserved.")
    
    # Home Page - Why Shop With Us Section
    why_shop_section_title = models.CharField(max_length=200, default="Why Shop With Us?")
    
    # Feature 1
    feature1_title = models.CharField(max_length=100, default="Fast Delivery")
    feature1_subtitle = models.CharField(max_length=200, default="Quick & reliable shipping")
    
    # Feature 2
    feature2_title = models.CharField(max_length=100, default="Quality Products")
    feature2_subtitle = models.CharField(max_length=200, default="Premium quality guaranteed")
    
    # Feature 3
    feature3_title = models.CharField(max_length=100, default="24/7 Support")
    feature3_subtitle = models.CharField(max_length=200, default="Round the clock assistance")
    
    # Feature 4
    feature4_title = models.CharField(max_length=100, default="Secure Payment")
    feature4_subtitle = models.CharField(max_length=200, default="Safe & secure transactions")
    
    # Shipping & Returns Content Management
    shipping_info_title = models.CharField(
        max_length=200, 
        default="Shipping Information",
        help_text="Title for shipping information section"
    )
    shipping_info_content = models.TextField(
        default="""• Free standard shipping on orders over $50
• Express shipping available for $9.99
• Orders processed within 1-2 business days
• Delivery time: 3-7 business days
• Free shipping on all orders within Bangladesh
• International shipping available to select countries""",
        help_text="Shipping information content (supports HTML and line breaks)"
    )
    
    return_policy_title = models.CharField(
        max_length=200, 
        default="Return Policy",
        help_text="Title for return policy section"
    )
    return_policy_content = models.TextField(
        default="""• 30-day return window from delivery date
• Items must be in original condition
• Free return shipping on defective items
• Refunds processed within 5-10 business days
• Original packaging required for returns
• Contact customer service to initiate returns""",
        help_text="Return policy content (supports HTML and line breaks)"
    )
    
    # Estimated Delivery Settings
    custom_today_date = models.DateField(
        blank=True,
        null=True,
        help_text="Custom date to use as 'today' for delivery calculations. Leave empty to use current date."
    )
    delivery_cutoff_time = models.TimeField(
        default="16:00",  # 4 PM
        help_text="Orders placed after this time will be processed the next day (24-hour format)"
    )
    dhaka_delivery_days_min = models.PositiveIntegerField(
        default=1,
        help_text="Minimum delivery days for Dhaka City (days added to processing date)"
    )
    dhaka_delivery_days_max = models.PositiveIntegerField(
        default=2,
        help_text="Maximum delivery days for Dhaka City (days added to processing date)"
    )
    outside_dhaka_delivery_days_min = models.PositiveIntegerField(
        default=1,
        help_text="Minimum delivery days for Outside Dhaka (days added to processing date)"
    )
    outside_dhaka_delivery_days_max = models.PositiveIntegerField(
        default=3,
        help_text="Maximum delivery days for Outside Dhaka (days added to processing date)"
    )
    delivery_area_dhaka_label = models.CharField(
        max_length=100,
        default="Inside Dhaka City",
        help_text="Label for Dhaka city delivery area"
    )
    delivery_area_outside_label = models.CharField(
        max_length=100,
        default="Outside Dhaka City", 
        help_text="Label for outside Dhaka delivery area"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        if self.updated_at:
            return f"Site Settings - {self.site_name} (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
        else:
            return f"Site Settings - {self.site_name} (New)"

    @classmethod
    def get_active_settings(cls):
        """Get the active site settings"""
        active_settings = cls.objects.filter(is_active=True).first()
        if active_settings is None:
            # Return default settings if none exist
            return cls()
        return active_settings

    def get_current_year(self):
        """Get current year for copyright text"""
        from datetime import datetime
        return datetime.now().year

    def get_copyright_text_with_year(self):
        """Replace {year} placeholder with current year"""
        return self.copyright_text.replace('{year}', str(self.get_current_year()))


class Curier(models.Model):
    """Model for storing courier API credentials"""
    name = models.CharField(max_length=100, default="Default")
    api_url = models.URLField(max_length=255)
    api_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curier"
        verbose_name_plural = "Curiers"

    def __str__(self):
        return f"{self.name} ({self.api_url})"


class CheckoutCustomization(models.Model):
    """Model for storing checkout page customization settings"""
    
    # Page Title & Headers
    page_title = models.CharField(max_length=200, default="Checkout")
    page_subtitle = models.CharField(max_length=300, default="Complete your order")
    
    # Customer Information Section
    customer_section_title = models.CharField(max_length=200, default="Customer Information")
    
    # Field Labels
    full_name_label = models.CharField(max_length=100, default="Full Name")
    full_name_placeholder = models.CharField(max_length=200, default="Enter your full name", blank=True)
    full_name_default = models.CharField(max_length=200, blank=True)
    
    email_label = models.CharField(max_length=100, default="Email Address *")
    email_placeholder = models.CharField(max_length=200, default="Enter your email address", blank=True)
    email_default = models.CharField(max_length=200, blank=True)
    
    phone_label = models.CharField(max_length=100, default="Phone Number *")
    phone_placeholder = models.CharField(max_length=200, default="Enter your phone number", blank=True)
    phone_default = models.CharField(max_length=200, blank=True)
    
    # Shipping Address Section
    shipping_section_title = models.CharField(max_length=200, default="Shipping Address")
    
    address_label = models.CharField(max_length=100, default="Street Address")
    address_placeholder = models.CharField(max_length=500, default="Enter your complete address", blank=True)
    address_default = models.TextField(blank=True)
    
    # Order Instructions Section
    instructions_section_title = models.CharField(max_length=200, default="Order Instructions")
    
    instructions_label = models.CharField(max_length=100, default="Special Instructions (Optional)")
    instructions_placeholder = models.CharField(max_length=500, default="Any special delivery instructions, gift messages, or notes for your order...", blank=True)
    instructions_help_text = models.CharField(max_length=200, default="Maximum 500 characters", blank=True)
    
    # Shipping Method Section
    shipping_method_section_title = models.CharField(max_length=200, default="Shipping Method")
    delivery_location_label = models.CharField(max_length=100, default="Delivery Location *")
    
    dhaka_location_label = models.CharField(max_length=100, default="Dhaka City")
    outside_location_label = models.CharField(max_length=100, default="Outside Dhaka")
    
    # Payment Method Section
    payment_section_title = models.CharField(max_length=200, default="Payment Method")
    
    cod_label = models.CharField(max_length=100, default="Cash on Delivery")
    bkash_label = models.CharField(max_length=100, default="bKash")
    nagad_label = models.CharField(max_length=100, default="Nagad")
    
    # Payment Instructions
    bkash_merchant_number = models.CharField(max_length=20, default="01XXXXXXXXX")
    nagad_merchant_number = models.CharField(max_length=20, default="01XXXXXXXXX")
    
    bkash_instructions = models.TextField(default="""Follow these steps:
1. Go to your bKash Mobile Menu by dialing *247#
2. Choose "Send Money"
3. Enter Merchant bKash Account Number: {merchant_number}
4. Enter the total amount: {amount}
5. Enter a reference: Your phone number
6. Now enter your bKash Mobile Menu PIN and confirm""")
    
    nagad_instructions = models.TextField(default="""Follow these steps:
1. Go to your Nagad Mobile Menu by dialing *167#
2. Choose "Send Money"
3. Enter Merchant Nagad Account Number: {merchant_number}
4. Enter the total amount: {amount}
5. Enter a reference: Your phone number
6. Now enter your Nagad PIN and confirm""")
    
    cod_instructions = models.TextField(default="""Payment Information:
• Pay cash when you receive your order
• Make sure to have exact amount ready
• Our delivery person will collect the payment
• You can inspect the product before payment""")
    
    # Form Field Labels for Payment Methods
    bkash_transaction_label = models.CharField(max_length=100, default="bKash Transaction ID *")
    bkash_transaction_placeholder = models.CharField(max_length=200, default="Enter transaction ID after payment", blank=True)
    
    bkash_sender_label = models.CharField(max_length=100, default="Sender Mobile Number *")
    bkash_sender_placeholder = models.CharField(max_length=200, default="01XXXXXXXXX", blank=True)
    
    nagad_transaction_label = models.CharField(max_length=100, default="Nagad Transaction ID *")
    nagad_transaction_placeholder = models.CharField(max_length=200, default="Enter transaction ID after payment", blank=True)
    
    nagad_sender_label = models.CharField(max_length=100, default="Sender Mobile Number *")
    nagad_sender_placeholder = models.CharField(max_length=200, default="01XXXXXXXXX", blank=True)
    
    # Order Summary Section
    order_summary_title = models.CharField(max_length=200, default="Order Summary")
    
    subtotal_label = models.CharField(max_length=100, default="Subtotal:")
    shipping_label = models.CharField(max_length=100, default="Shipping:")
    tax_label = models.CharField(max_length=100, default="Tax:")
    total_label = models.CharField(max_length=100, default="Total:")
    
    # Action Buttons
    place_order_button_text = models.CharField(max_length=100, default="Place Order")
    
    # Trust/Security Elements
    security_ssl_text = models.CharField(max_length=100, default="SSL Secured")
    security_safe_text = models.CharField(max_length=100, default="Safe Checkout")
    
    trust_section_title = models.CharField(max_length=200, default="Why shop with us?")
    
    fast_shipping_title = models.CharField(max_length=100, default="Fast Shipping")
    fast_shipping_description = models.CharField(max_length=200, default="Free shipping on orders over $50")
    
    easy_returns_title = models.CharField(max_length=100, default="Easy Returns")
    easy_returns_description = models.CharField(max_length=200, default="30-day return policy")
    
    support_title = models.CharField(max_length=100, default="24/7 Support")
    support_description = models.CharField(max_length=200, default="Customer service available")
    
    # Breadcrumb
    breadcrumb_home = models.CharField(max_length=50, default="Home")
    breadcrumb_cart = models.CharField(max_length=50, default="Cart")
    breadcrumb_checkout = models.CharField(max_length=50, default="Checkout")
    
    # Display Options
    show_breadcrumb = models.BooleanField(default=True)
    show_trust_badges = models.BooleanField(default=True)
    show_security_badges = models.BooleanField(default=True)
    show_order_summary = models.BooleanField(default=True)
    
    # Theme Customization
    primary_color = models.CharField(max_length=7, default="#930000", help_text="Hex color code (e.g., #930000)")
    button_color = models.CharField(max_length=7, default="#930000", help_text="Hex color code for buttons")
    background_color = models.CharField(max_length=7, default="#f8fafc", help_text="Background color for sections")
    
    # Loading Messages
    loading_cart_message = models.CharField(max_length=200, default="Loading order items...")
    loading_shipping_message = models.CharField(max_length=200, default="Loading shipping options...")
    processing_order_message = models.CharField(max_length=200, default="Processing...")
    
    # Success/Error Messages
    order_success_message = models.CharField(max_length=200, default="Order placed successfully!")
    order_error_message = models.CharField(max_length=200, default="Error processing order. Please try again.")
    validation_error_message = models.CharField(max_length=200, default="Please check your information and try again.")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Checkout Customization"
        verbose_name_plural = "Checkout Customizations"

    def __str__(self):
        if self.updated_at:
            return f"Checkout Customization (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
        else:
            return "Checkout Customization (New)"

    @classmethod
    def get_active_settings(cls):
        """Get the active checkout customization settings"""
        active_settings = cls.objects.filter(is_active=True).first()
        if active_settings is None:
            # Return default settings if none exist
            return cls()
        return active_settings


class IntegrationSettings(models.Model):
    """Model for storing third-party integration codes and settings"""
    
    # Meta Pixel Integration
    meta_pixel_code = models.TextField(
        blank=True, 
        null=True,
        help_text="Meta Pixel code for Facebook advertising and analytics (Legacy)"
    )
    meta_pixel_id = models.CharField(
        max_length=50,
        blank=True, 
        null=True,
        help_text="Meta Pixel ID (e.g., 123456789012345)"
    )
    meta_access_token = models.CharField(
        max_length=500,
        blank=True, 
        null=True,
        help_text="Meta Access Token for Conversions API"
    )
    meta_pixel_enabled = models.BooleanField(default=False)
    
    # Meta Pixel Advanced Tracking Options
    meta_scroll_tracking = models.BooleanField(default=False, help_text="Enable scroll depth tracking")
    meta_time_tracking = models.BooleanField(default=False, help_text="Enable time on page tracking")
    meta_hover_tracking = models.BooleanField(default=False, help_text="Enable element hover tracking")
    meta_section_tracking = models.BooleanField(default=False, help_text="Enable section view tracking")
    meta_cart_tracking = models.BooleanField(default=False, help_text="Enable advanced cart tracking")
    meta_checkout_tracking = models.BooleanField(default=False, help_text="Enable checkout funnel tracking")
    meta_capi_enabled = models.BooleanField(default=False, help_text="Enable Conversions API")
    
    # Google Analytics Integration
    google_analytics_code = models.TextField(
        blank=True, 
        null=True,
        help_text="Google Analytics tracking code (GA4 or Universal Analytics)"
    )
    google_analytics_measurement_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Google Analytics Measurement ID (e.g., G-XXXXXXXXXX)"
    )
    google_analytics_enabled = models.BooleanField(default=False)
    
    # Search Engine Verification
    google_search_console_code = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Google Search Console verification meta tag content"
    )
    google_search_console_enabled = models.BooleanField(default=False)
    
    bing_webmaster_code = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Bing Webmaster Tools verification meta tag content"
    )
    bing_webmaster_enabled = models.BooleanField(default=False)
    
    yandex_verification_code = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Yandex Webmaster verification meta tag content"
    )
    yandex_verification_enabled = models.BooleanField(default=False)
    
    # Additional Tracking Scripts
    header_scripts = models.TextField(
        blank=True, 
        null=True,
        help_text="Custom scripts to be added in the <head> section"
    )
    footer_scripts = models.TextField(
        blank=True, 
        null=True,
        help_text="Custom scripts to be added before closing </body> tag"
    )
    
    # Google Tag Manager
    gtm_container_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Google Tag Manager Container ID (e.g., GTM-XXXXXXX)"
    )
    gtm_enabled = models.BooleanField(default=False)
    
    # Hotjar Integration
    hotjar_site_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Hotjar Site ID for heatmaps and user behavior analytics"
    )
    hotjar_enabled = models.BooleanField(default=False)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Integration Settings"
        verbose_name_plural = "Integration Settings"
    
    def __str__(self):
        if self.updated_at:
            return f"Integration Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
        else:
            return "Integration Settings (New)"
    
    @classmethod
    def get_active_settings(cls):
        """Get the active integration settings"""
        active_settings = cls.objects.filter(is_active=True).first()
        if active_settings is None:
            # Create and save default settings if none exist
            try:
                active_settings = cls.objects.create(is_active=True)
                print(f"Created default IntegrationSettings with ID: {active_settings.pk}")
            except Exception as e:
                print(f"Error creating default integration settings: {e}")
                # Return unsaved default settings as fallback
                return cls()
        return active_settings
    
    def get_meta_pixel_script(self):
        """Generate Meta Pixel script tag with advanced tracking"""
        if not self.meta_pixel_enabled:
            return ""
        
        scripts = []
        
        # Base Meta Pixel Code
        if self.meta_pixel_id:
            # Modern approach using Pixel ID
            scripts.append(f"""
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '{self.meta_pixel_id}');
fbq('track', 'PageView');
</script>
<!-- End Meta Pixel Code -->""".strip())
        elif self.meta_pixel_code:
            # Legacy approach using full code
            if '<script>' in self.meta_pixel_code.lower():
                scripts.append(self.meta_pixel_code)
            else:
                scripts.append(f"""
<!-- Meta Pixel Code (Legacy) -->
<script>
{self.meta_pixel_code}
</script>
<!-- End Meta Pixel Code (Legacy) -->""".strip())
        else:
            return ""
        
        # Add advanced tracking scripts if enabled
        if any([self.meta_scroll_tracking, self.meta_time_tracking, self.meta_hover_tracking, 
                self.meta_section_tracking, self.meta_cart_tracking, self.meta_checkout_tracking]):
            
            advanced_script = """
<!-- Meta Pixel Advanced Tracking -->
<script>
// Advanced Meta Pixel Tracking Implementation
window.MetaPixelAdvanced = {
    scrollTracked: false,
    timeTracked: {15: false, 30: false, 60: false, 120: false},
    sectionsTracked: new Set(),
    
    init: function() {"""
            
            if self.meta_scroll_tracking:
                advanced_script += """
        this.initScrollTracking();"""
            
            if self.meta_time_tracking:
                advanced_script += """
        this.initTimeTracking();"""
            
            if self.meta_hover_tracking:
                advanced_script += """
        this.initHoverTracking();"""
            
            if self.meta_section_tracking:
                advanced_script += """
        this.initSectionTracking();"""
            
            if self.meta_cart_tracking:
                advanced_script += """
        this.initCartTracking();"""
            
            if self.meta_checkout_tracking:
                advanced_script += """
        this.initCheckoutTracking();"""
            
            advanced_script += """
    },"""
            
            # Scroll Depth Tracking
            if self.meta_scroll_tracking:
                advanced_script += """
    
    initScrollTracking: function() {
        let scrollThresholds = [25, 50, 75, 100];
        let trackedThresholds = new Set();
        
        window.addEventListener('scroll', function() {
            let scrollPercent = Math.round(
                ((window.scrollY + window.innerHeight) / document.body.scrollHeight) * 100
            );
            
            scrollThresholds.forEach(threshold => {
                if (scrollPercent >= threshold && !trackedThresholds.has(threshold)) {
                    trackedThresholds.add(threshold);
                    fbq('trackCustom', 'ScrollDepth', {
                        scroll_percent: threshold,
                        page_url: window.location.href
                    });
                }
            });
        });
    },"""
            
            # Time on Page Tracking
            if self.meta_time_tracking:
                advanced_script += """
    
    initTimeTracking: function() {
        [15, 30, 60, 120].forEach(seconds => {
            setTimeout(() => {
                if (!this.timeTracked[seconds]) {
                    this.timeTracked[seconds] = true;
                    fbq('trackCustom', 'TimeOnPage', {
                        time_seconds: seconds,
                        page_url: window.location.href
                    });
                }
            }, seconds * 1000);
        });
    },"""
            
            # Hover Tracking
            if self.meta_hover_tracking:
                advanced_script += """
    
    initHoverTracking: function() {
        document.addEventListener('DOMContentLoaded', function() {
            const hoverElements = '.btn, .product-card, .add-to-cart, .product-item, .cta-button';
            document.querySelectorAll(hoverElements).forEach(el => {
                let hoverTracked = false;
                el.addEventListener('mouseover', function() {
                    if (!hoverTracked) {
                        hoverTracked = true;
                        fbq('trackCustom', 'HoverIntent', {
                            element_type: this.className,
                            element_id: this.id || null,
                            product_id: this.dataset.productId || null,
                            page_url: window.location.href
                        });
                    }
                });
            });
        });
    },"""
            
            # Section View Tracking
            if self.meta_section_tracking:
                advanced_script += """
    
    initSectionTracking: function() {
        const sections = document.querySelectorAll('.section, .hero-section, .products-section, .about-section');
        const options = { threshold: 0.5 };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.sectionsTracked.has(entry.target.id)) {
                    this.sectionsTracked.add(entry.target.id);
                    fbq('trackCustom', 'ViewSection', {
                        section_id: entry.target.id,
                        section_class: entry.target.className,
                        page_url: window.location.href
                    });
                }
            });
        }, options);
        
        sections.forEach(section => {
            if (section.id) observer.observe(section);
        });
    },"""
            
            # Cart Tracking
            if self.meta_cart_tracking:
                advanced_script += """
    
    initCartTracking: function() {
        // Track Add to Cart events
        document.addEventListener('click', function(e) {
            if (e.target.matches('.add-to-cart, .btn-add-cart')) {
                const productId = e.target.dataset.productId;
                const productName = e.target.dataset.productName;
                
                fbq('trackCustom', 'AddToCart', {
                    product_id: productId,
                    product_name: productName,
                    timestamp: Date.now()
                });
                
                // Set flag for cart abandonment tracking
                localStorage.setItem('meta_cart_action', JSON.stringify({
                    action: 'add_to_cart',
                    timestamp: Date.now(),
                    product_id: productId
                }));
            }
        });
        
        // Track cart abandonment
        window.addEventListener('beforeunload', function() {
            const cartAction = localStorage.getItem('meta_cart_action');
            if (cartAction && !window.location.pathname.includes('/checkout')) {
                const actionData = JSON.parse(cartAction);
                if (Date.now() - actionData.timestamp < 300000) { // 5 minutes
                    fbq('trackCustom', 'CartAbandon', {
                        product_id: actionData.product_id,
                        time_on_page: Date.now() - actionData.timestamp
                    });
                }
            }
        });
    },"""
            
            # Checkout Funnel Tracking
            if self.meta_checkout_tracking:
                advanced_script += """
    
    initCheckoutTracking: function() {
        // Track checkout steps based on URL patterns
        const currentPath = window.location.pathname;
        
        if (currentPath.includes('/checkout')) {
            fbq('trackCustom', 'InitiateCheckout', {
                page_url: window.location.href
            });
            
            // Clear cart abandonment flag
            localStorage.removeItem('meta_cart_action');
        }
        
        if (currentPath.includes('/shipping') || currentPath.includes('/delivery')) {
            fbq('trackCustom', 'CheckoutShipping', {
                page_url: window.location.href
            });
        }
        
        if (currentPath.includes('/payment')) {
            fbq('trackCustom', 'CheckoutPayment', {
                page_url: window.location.href
            });
            
            // Track payment abandonment
            window.addEventListener('beforeunload', function() {
                if (!window.location.pathname.includes('/success')) {
                    fbq('trackCustom', 'PaymentAbandon', {
                        page_url: window.location.href
                    });
                }
            });
        }
        
        if (currentPath.includes('/success') || currentPath.includes('/complete')) {
            fbq('trackCustom', 'CheckoutComplete', {
                page_url: window.location.href
            });
        }
    }"""
            
            advanced_script += """
};

// Initialize advanced tracking when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => MetaPixelAdvanced.init());
} else {
    MetaPixelAdvanced.init();
}
</script>
<!-- End Meta Pixel Advanced Tracking -->"""
            
            scripts.append(advanced_script.strip())
        
        return '\n\n'.join(scripts)
    
    def get_google_analytics_script(self):
        """Generate Google Analytics script tag"""
        if not self.google_analytics_enabled:
            return ""
        
        scripts = []
        
        # Add GA4 script if measurement ID is provided
        if self.google_analytics_measurement_id:
            scripts.append(f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={self.google_analytics_measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{self.google_analytics_measurement_id}');
</script>
<!-- End Google Analytics -->""".strip())
        
        # Add custom analytics code if provided
        if self.google_analytics_code:
            if '<script>' in self.google_analytics_code.lower():
                scripts.append(self.google_analytics_code)
            else:
                scripts.append(f"""
<!-- Custom Google Analytics Code -->
<script>
{self.google_analytics_code}
</script>
<!-- End Custom Google Analytics Code -->""".strip())
        
        return '\n\n'.join(scripts)
    
    def get_gtm_script(self):
        """Generate Google Tag Manager script"""
        if not self.gtm_enabled or not self.gtm_container_id:
            return ""
        
        return f"""
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{self.gtm_container_id}');</script>
<!-- End Google Tag Manager -->
        """.strip()
    
    def get_gtm_noscript(self):
        """Generate Google Tag Manager noscript tag"""
        if not self.gtm_enabled or not self.gtm_container_id:
            return ""
        
        return f"""
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={self.gtm_container_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
        """.strip()
    
    def get_hotjar_script(self):
        """Generate Hotjar script tag"""
        if not self.hotjar_enabled or not self.hotjar_site_id:
            return ""
        
        return f"""
<!-- Hotjar Tracking Code -->
<script>
    (function(h,o,t,j,a,r){{
        h.hj=h.hj||function(){{(h.hj.q=h.hj.q||[]).push(arguments)}};
        h._hjSettings={{hjid:{self.hotjar_site_id},hjsv:6}};
        a=o.getElementsByTagName('head')[0];
        r=o.createElement('script');r.async=1;
        r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
        a.appendChild(r);
    }})(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
</script>
<!-- End Hotjar Tracking Code -->
        """.strip()
    
    def get_verification_meta_tags(self):
        """Generate search engine verification meta tags"""
        meta_tags = []
        
        if self.google_search_console_enabled and self.google_search_console_code:
            meta_tags.append(f'<meta name="google-site-verification" content="{self.google_search_console_code}" />')
        
        if self.bing_webmaster_enabled and self.bing_webmaster_code:
            meta_tags.append(f'<meta name="msvalidate.01" content="{self.bing_webmaster_code}" />')
        
        if self.yandex_verification_enabled and self.yandex_verification_code:
            meta_tags.append(f'<meta name="yandex-verification" content="{self.yandex_verification_code}" />')
        
        return '\n'.join(meta_tags)
    
    def get_all_header_scripts(self):
        """Get all scripts that should be placed in the <head> section"""
        scripts = []
        
        # Google Tag Manager (must be in head)
        gtm = self.get_gtm_script()
        if gtm:
            scripts.append(gtm)
        
        # Google Analytics
        ga = self.get_google_analytics_script()
        if ga:
            scripts.append(ga)
        
        # Meta Pixel
        meta_pixel = self.get_meta_pixel_script()
        if meta_pixel:
            scripts.append(meta_pixel)
        
        # Hotjar
        hotjar = self.get_hotjar_script()
        if hotjar:
            scripts.append(hotjar)
        
        # Custom header scripts
        if self.header_scripts:
            scripts.append(self.header_scripts)
        
        return '\n\n'.join(scripts)
    
    def get_all_body_scripts(self):
        """Get all scripts that should be placed immediately after opening <body> tag"""
        scripts = []
        
        # GTM noscript (should be immediately after opening body tag)
        gtm_noscript = self.get_gtm_noscript()
        if gtm_noscript:
            scripts.append(gtm_noscript)
        
        return '\n\n'.join(scripts)
    
    def get_footer_scripts(self):
        """Get all scripts that should be placed before closing </body> tag"""
        scripts = []
        
        # Custom footer scripts
        if self.footer_scripts:
            scripts.append(self.footer_scripts)
        
        return '\n\n'.join(scripts)
