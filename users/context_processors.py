"""
Context processors for dashboard permissions
"""

def dashboard_permissions(request):
    """
    Add dashboard permission checking function to template context
    """
    def check_dashboard_access(tab_code):
        """Check if current user has access to dashboard tab"""
        if not request.user.is_authenticated:
            return False
        return request.user.has_dashboard_access(tab_code)
    
    return {
        'check_dashboard_access': check_dashboard_access,
    }