from .models import SiteSettings, CheckoutCustomization

def site_settings(request):
    """
    Context processor to make site settings available in all templates
    """
    try:
        site_settings = SiteSettings.get_active_settings()
        return {
            'site_settings': site_settings
        }
    except Exception as e:
        # Return empty dict if there's an error
        print(f"Error loading site settings: {e}")
        return {
            'site_settings': SiteSettings()  # Default instance
        }

def checkout_customization(request):
    """
    Context processor to make checkout customization settings available in templates
    """
    try:
        customization = CheckoutCustomization.get_active_settings()
        return {
            'checkout_customization': customization
        }
    except Exception as e:
        # Return empty dict if there's an error
        print(f"Error loading checkout customization: {e}")
        return {
            'checkout_customization': CheckoutCustomization()  # Default instance
        }