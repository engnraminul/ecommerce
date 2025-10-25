"""
Custom authentication backend for email verification enforcement.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailVerificationBackend(ModelBackend):
    """
    Custom authentication backend that requires email verification.
    
    This backend extends Django's default ModelBackend to add email verification
    checking during authentication. Users must have verified their email address
    before they can successfully authenticate.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user with email verification check.
        
        Args:
            request: The HTTP request object
            username: The username (email in our case)
            password: The user's password
            **kwargs: Additional keyword arguments
            
        Returns:
            User object if authentication successful and email verified, None otherwise
        """
        # First, try the default authentication
        user = super().authenticate(request, username, password, **kwargs)
        
        if user is None:
            # User doesn't exist or password is wrong
            return None
        
        # Check if email is verified
        if not user.is_email_verified:
            # User exists and password is correct, but email is not verified
            return None
        
        return user
    
    def get_user(self, user_id):
        """
        Get a user by ID.
        
        Args:
            user_id: The user's primary key
            
        Returns:
            User object if exists and email verified, None otherwise
        """
        try:
            user = User.objects.get(pk=user_id)
            # Only return the user if their email is verified
            if user.is_email_verified:
                return user
            return None
        except User.DoesNotExist:
            return None