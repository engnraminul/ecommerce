from django import template

register = template.Library()


@register.filter
def has_dashboard_access(user, tab_code):
    """
    Template filter to check if user has access to a specific dashboard tab
    Usage: {% if user|has_dashboard_access:'products' %}
    """
    if not user or not user.is_authenticated:
        return False
    
    # Only superusers get automatic access to all tabs
    if user.is_superuser:
        return True
    
    # Staff and regular users must have explicit permissions
    return user.has_dashboard_access(tab_code)