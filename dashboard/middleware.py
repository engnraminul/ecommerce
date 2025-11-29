"""
Professional Dashboard Security Middleware
Handles session security, timeout, and activity tracking for admin dashboard
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse, resolve
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class DashboardSecurityMiddleware:
    """
    Middleware for enhanced dashboard security features:
    - Session timeout based on inactivity
    - IP address validation (optional)
    - User agent validation (optional)
    - Activity tracking
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Session timeout in minutes (default: 30 minutes)
        self.session_timeout = getattr(settings, 'DASHBOARD_SESSION_TIMEOUT', 30)
        # IP validation enabled (set to True for production)
        self.validate_ip = getattr(settings, 'DASHBOARD_VALIDATE_IP', False)
        # User agent validation enabled
        self.validate_user_agent = getattr(settings, 'DASHBOARD_VALIDATE_USER_AGENT', False)

    def __call__(self, request):
        # Only apply to dashboard URLs
        if self.is_dashboard_url(request.path):
            # Check if user should be processed for security
            if self.should_check_security(request):
                security_result = self.check_security(request)
                if security_result:
                    return security_result
        
        response = self.get_response(request)
        
        # Update last activity for authenticated dashboard users
        if (self.is_dashboard_url(request.path) and 
            request.user.is_authenticated and 
            request.user.is_staff):
            self.update_activity(request)
        
        return response

    def is_dashboard_url(self, path):
        """Check if the current path is a dashboard URL"""
        return path.startswith('/mb-admin/') or path.startswith('/dashboard/')

    def should_check_security(self, request):
        """Determine if security checks should be applied"""
        # Skip security checks for login/logout pages
        try:
            resolved = resolve(request.path)
            if resolved.url_name in ['login', 'logout']:
                return False
        except:
            pass
        
        return (request.user.is_authenticated and 
                request.user.is_staff)

    def check_security(self, request):
        """Perform comprehensive security checks"""
        # Check session timeout
        timeout_result = self.check_session_timeout(request)
        if timeout_result:
            return timeout_result
        
        # Check IP address validation
        if self.validate_ip:
            ip_result = self.check_ip_address(request)
            if ip_result:
                return ip_result
        
        # Check user agent validation
        if self.validate_user_agent:
            ua_result = self.check_user_agent(request)
            if ua_result:
                return ua_result
        
        return None

    def check_session_timeout(self, request):
        """Check for session timeout based on last activity"""
        last_activity_str = request.session.get('last_activity')
        
        if last_activity_str:
            try:
                last_activity = timezone.datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
                
                # Make timezone aware if needed
                if timezone.is_naive(last_activity):
                    last_activity = timezone.make_aware(last_activity)
                
                # Calculate time since last activity
                time_since_activity = timezone.now() - last_activity
                timeout_duration = timedelta(minutes=self.session_timeout)
                
                if time_since_activity > timeout_duration:
                    # Session has timed out
                    logger.info(f"Session timeout for user {request.user.username}")
                    logout(request)
                    messages.warning(request, 
                        f'Your session has expired due to inactivity. '
                        f'Please log in again.')
                    return redirect('dashboard:login')
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid last_activity format: {e}")
                # Reset activity timestamp
                request.session['last_activity'] = timezone.now().isoformat()
        
        return None

    def check_ip_address(self, request):
        """Validate IP address consistency"""
        current_ip = self.get_client_ip(request)
        session_ip = request.session.get('login_ip')
        
        if session_ip and session_ip != current_ip:
            logger.warning(f"IP address mismatch for user {request.user.username}: "
                          f"Session IP: {session_ip}, Current IP: {current_ip}")
            logout(request)
            messages.error(request, 
                'Security alert: Your IP address has changed. '
                'Please log in again.')
            return redirect('dashboard:login')
        
        # Store IP address in session if not present
        if not session_ip:
            request.session['login_ip'] = current_ip
        
        return None

    def check_user_agent(self, request):
        """Validate user agent consistency"""
        current_ua = request.META.get('HTTP_USER_AGENT', '')
        session_ua = request.session.get('login_user_agent')
        
        if session_ua and session_ua != current_ua:
            logger.warning(f"User agent mismatch for user {request.user.username}")
            logout(request)
            messages.error(request, 
                'Security alert: Your browser signature has changed. '
                'Please log in again.')
            return redirect('dashboard:login')
        
        # Store user agent in session if not present
        if not session_ua:
            request.session['login_user_agent'] = current_ua
        
        return None

    def update_activity(self, request):
        """Update last activity timestamp"""
        request.session['last_activity'] = timezone.now().isoformat()

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DashboardCSRFMiddleware:
    """
    Enhanced CSRF protection specifically for dashboard
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers for dashboard requests
        if self.is_dashboard_url(request.path):
            # Prevent clickjacking
            response['X-Frame-Options'] = 'DENY'
            # Prevent content type sniffing
            response['X-Content-Type-Options'] = 'nosniff'
            # Enable XSS protection
            response['X-XSS-Protection'] = '1; mode=block'
            # Referrer policy
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            # Content Security Policy (basic)
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data:; "
            )
        
        return response

    def is_dashboard_url(self, path):
        """Check if the current path is a dashboard URL"""
        return path.startswith('/mb-admin/') or path.startswith('/dashboard/')