from .models import SiteSettings, CheckoutCustomization, IntegrationSettings
from products.models import Category

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

def navbar_categories(request):
    """
    Context processor to make parent categories available in the navbar
    """
    try:
        parent_categories = Category.objects.filter(
            is_active=True,
            parent=None
        ).order_by('name')[:8]  # Limit to 8 categories for navbar
        return {
            'navbar_categories': parent_categories
        }
    except Exception as e:
        # Return empty list if there's an error
        print(f"Error loading navbar categories: {e}")
        return {
            'navbar_categories': []
        }

def integration_settings(request):
    """
    Context processor to make integration settings available in all templates
    """
    try:
        settings = IntegrationSettings.get_active_settings()
        
        # Return all integration data and helper methods
        return {
            'integration_settings': settings,
            'integration_meta_tags': settings.get_verification_meta_tags() if settings else '',
            'integration_header_scripts': settings.get_all_header_scripts() if settings else '',
            'integration_body_scripts': settings.get_all_body_scripts() if settings else '',
        }
    except Exception as e:
        # Return empty values if there's an error to prevent template crashes
        print(f"Error loading integration settings: {e}")
        return {
            'integration_settings': None,
            'integration_meta_tags': '',
            'integration_header_scripts': '',
            'integration_body_scripts': '',
        }