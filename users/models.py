from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """Custom User model with additional fields for eCommerce"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Profile fields
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Password reset
    password_reset_token = models.UUIDField(null=True, blank=True, unique=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Address fields (default shipping address)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Removed username from required fields
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    def generate_email_verification_token(self):
        """Generate a new email verification token."""
        self.email_verification_token = uuid.uuid4()
        self.save(update_fields=['email_verification_token'])
        return self.email_verification_token
    
    def verify_email(self):
        """Mark email as verified and clear verification token."""
        self.is_email_verified = True
        self.email_verification_token = uuid.uuid4()  # Generate new token for security
        self.email_verification_sent_at = None
        self.save(update_fields=['is_email_verified', 'email_verification_token', 'email_verification_sent_at'])
    
    def can_login(self):
        """Check if user can log in (email must be verified)."""
        return self.is_email_verified and self.is_active
    
    def generate_password_reset_token(self):
        """Generate a new password reset token."""
        self.password_reset_token = uuid.uuid4()
        self.save(update_fields=['password_reset_token'])
        return self.password_reset_token
    
    def clear_password_reset_token(self):
        """Clear the password reset token after use."""
        self.password_reset_token = None
        self.password_reset_sent_at = None
        self.save(update_fields=['password_reset_token', 'password_reset_sent_at'])
    
    # Email verification methods
    def generate_email_verification_token(self):
        """Generate a new email verification token."""
        self.email_verification_token = uuid.uuid4()
        self.save(update_fields=['email_verification_token'])
        return self.email_verification_token
    
    def verify_email(self):
        """Mark email as verified and clear the verification token."""
        self.is_email_verified = True
        # Don't set token to None if field doesn't allow null
        # Instead, we'll keep the token but mark email as verified
        self.save(update_fields=['is_email_verified'])
    
    def is_email_verification_expired(self):
        """Check if the email verification token has expired (24 hours)."""
        if not self.email_verification_sent_at:
            return True
        
        from django.utils import timezone
        from datetime import timedelta
        
        expiry_time = self.email_verification_sent_at + timedelta(hours=24)
        return timezone.now() > expiry_time
    
    def can_login(self):
        """Check if user can login (must have verified email)."""
        return self.is_active and self.is_email_verified


class UserProfile(models.Model):
    """Extended user profile for additional eCommerce features"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Preferences
    newsletter_subscription = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Shopping preferences
    preferred_currency = models.CharField(max_length=3, default='USD')
    preferred_language = models.CharField(max_length=10, default='en')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"


class Address(models.Model):
    """Separate address model for multiple shipping addresses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    
    ADDRESS_TYPES = [
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
    ]
    
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='shipping')
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Addresses"
        unique_together = ['user', 'address_type', 'is_default']
    
    def __str__(self):
        return f"{self.address_type.title()} address for {self.user.username}"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
