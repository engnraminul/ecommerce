from django.http import JsonResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from .models import DashboardPermission


class DashboardPermissionMiddleware:
    """
    Middleware to check dashboard permissions for users accessing dashboard views
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Dashboard URL patterns that require permission checks
        self.dashboard_urls = {
            '/mb-admin/': 'home',
            '/mb-admin/products/': 'products',
            '/mb-admin/categories/': 'categories',
            '/mb-admin/media/': 'media',
            '/mb-admin/stock/': 'stock',
            '/mb-admin/orders/': 'orders',
            '/mb-admin/incomplete-orders/': 'incomplete_orders',
            '/mb-admin/reviews/': 'reviews',
            '/mb-admin/contacts/': 'contacts',
            '/mb-admin/pages/': 'pages',
            '/mb-admin/blocklist/': 'blocklist',
            '/mb-admin/users/': 'users',
            '/mb-admin/expenses/': 'expenses',
            '/mb-admin/statistics/': 'statistics',
            '/mb-admin/email-settings/': 'email_settings',
            '/mb-admin/settings/': 'settings',
            '/mb-admin/api-docs/': 'api_docs',
            '/mb-admin/backups/': 'backups',
        }
        
        # API endpoints that should also be checked
        self.api_patterns = {
            '/mb-admin/api/products/': 'products',
            '/mb-admin/api/categories/': 'categories',
            '/mb-admin/api/stock/': 'stock',
            '/mb-admin/api/orders/': 'orders',
            '/mb-admin/api/incomplete-orders/': 'incomplete_orders',
            '/mb-admin/api/users/': 'users',
            '/mb-admin/api/expenses/': 'expenses',
            '/mb-admin/api/statistics/': 'statistics',
            '/mb-admin/api/settings/': 'settings',
            '/mb-admin/api/blocklist/': 'blocklist',
            '/mb-admin/api/media/': 'media',
            '/backups/api/': 'backups',
        }

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check dashboard permissions before processing the view
        """
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return None
        
        # Skip permission check for superusers only
        if request.user.is_superuser:
            return None
        
        # Check if this is a dashboard URL
        path = request.path
        required_permission = None
        
        # Check exact matches first
        if path in self.dashboard_urls:
            required_permission = self.dashboard_urls[path]
        elif path in self.api_patterns:
            required_permission = self.api_patterns[path]
        else:
            # Check if path starts with any of our patterns
            for url_pattern, permission in {**self.dashboard_urls, **self.api_patterns}.items():
                if path.startswith(url_pattern):
                    required_permission = permission
                    break
        
        # If this is not a dashboard URL, allow access
        if not required_permission:
            return None
        
        # Check user's dashboard permissions
        if not request.user.has_dashboard_access(required_permission):
            # For API requests, return JSON error
            if path.startswith('/mb-admin/api/'):
                return JsonResponse({
                    'error': 'Permission denied',
                    'message': f'You do not have permission to access {required_permission} dashboard.'
                }, status=403)
            
            # For regular dashboard pages, redirect with error message
            messages.error(request, f'You do not have permission to access the {required_permission} dashboard.')
            return redirect(reverse('dashboard:home'))
        
        return None