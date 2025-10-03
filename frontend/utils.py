from settings.models import CheckoutCustomization

def checkout_customization_context(request):
    """Context processor to add checkout customization to all templates"""
    try:
        checkout_customization = CheckoutCustomization.get_active_settings()
        return {
            'checkout_customization': checkout_customization
        }
    except Exception as e:
        # Fallback to prevent template errors
        return {
            'checkout_customization': None
        }