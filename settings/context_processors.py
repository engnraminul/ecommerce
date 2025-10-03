from .models import CheckoutCustomization

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