from django.db import models

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
        return f"Checkout Customization (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"

    @classmethod
    def get_active_settings(cls):
        """Get the active checkout customization settings"""
        try:
            return cls.objects.filter(is_active=True).first()
        except cls.DoesNotExist:
            # Return default settings if none exist
            return cls()
