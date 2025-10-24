"""
Authentication views for password reset and email activation.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.http import Http404
from django.contrib.auth.forms import SetPasswordForm
from django import forms
from django.core.exceptions import ValidationError

from dashboard.email_service import email_service

User = get_user_model()


class ForgotPasswordForm(forms.Form):
    """Form for requesting password reset."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text="Enter the email address associated with your account."
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No account found with this email address.")
        return email


class UserRegistrationForm(forms.ModelForm):
    """User registration form with email verification."""
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Your password must contain at least 8 characters."
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Enter the same password as before, for verification."
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False  # User needs to verify email first
        user.is_email_verified = False
        if commit:
            user.save()
        return user


def forgot_password(request):
    """Handle forgot password requests."""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            
            # Generate password reset token
            user.generate_password_reset_token()
            user.password_reset_sent_at = timezone.now()
            user.save()
            
            # Send password reset email
            success = email_service.send_password_reset_email(user)
            
            if success:
                messages.success(
                    request, 
                    f'Password reset instructions have been sent to {email}. '
                    'Please check your email and follow the instructions.'
                )
            else:
                messages.error(
                    request,
                    'There was an error sending the password reset email. '
                    'Please try again later or contact support.'
                )
            
            return redirect('users:forgot_password')
    else:
        form = ForgotPasswordForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'users/forgot_password.html', context)


def reset_password(request, token):
    """Handle password reset with token."""
    try:
        user = User.objects.get(password_reset_token=token)
        
        # Check if token is still valid (24 hours)
        if user.password_reset_sent_at:
            expiry_time = user.password_reset_sent_at + timedelta(hours=24)
            if timezone.now() > expiry_time:
                messages.error(request, 'Password reset link has expired. Please request a new one.')
                return redirect('users:forgot_password')
        else:
            messages.error(request, 'Invalid password reset link.')
            return redirect('users:forgot_password')
        
    except User.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('users:forgot_password')
    
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            
            # Clear the reset token
            user.clear_password_reset_token()
            
            messages.success(
                request,
                'Your password has been reset successfully. You can now log in with your new password.'
            )
            
            return redirect('users:login')
    else:
        form = SetPasswordForm(user)
    
    context = {
        'form': form,
        'token': token,
    }
    
    return render(request, 'users/reset_password.html', context)


def register(request):
    """User registration with email verification."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Send activation email
            success = email_service.send_activation_email(user)
            
            if success:
                messages.success(
                    request,
                    f'Account created successfully! We\'ve sent an activation email to {user.email}. '
                    'Please check your email and click the activation link to complete your registration.'
                )
            else:
                messages.warning(
                    request,
                    'Account created successfully, but there was an error sending the activation email. '
                    'Please contact support to activate your account.'
                )
            
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'users/register.html', context)


def activate_account(request, token):
    """Activate user account with email verification token."""
    try:
        user = User.objects.get(email_verification_token=token, is_email_verified=False)
        
        # Check if activation was sent recently (7 days max)
        if user.email_verification_sent_at:
            expiry_time = user.email_verification_sent_at + timedelta(days=7)
            if timezone.now() > expiry_time:
                messages.error(
                    request, 
                    'Activation link has expired. Please contact support or register again.'
                )
                return redirect('users:register')
        
        # Activate the user
        user.is_active = True
        user.is_email_verified = True
        user.save()
        
        # Send welcome email
        email_service.send_welcome_email(user)
        
        messages.success(
            request,
            f'Welcome, {user.first_name or user.username}! Your account has been activated successfully. '
            'You can now log in and start shopping.'
        )
        
        # Automatically log in the user
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        
        return redirect('frontend:home')
        
    except User.DoesNotExist:
        messages.error(request, 'Invalid activation link or account already activated.')
        return redirect('users:login')


def resend_activation(request):
    """Resend activation email."""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                user = User.objects.get(email=email, is_email_verified=False, is_active=False)
                
                # Generate new token and send email
                user.generate_email_verification_token()
                user.email_verification_sent_at = timezone.now()
                user.save()
                
                success = email_service.send_activation_email(user)
                
                if success:
                    messages.success(
                        request,
                        f'Activation email has been resent to {email}. Please check your email.'
                    )
                else:
                    messages.error(
                        request,
                        'Error sending activation email. Please try again later.'
                    )
                    
            except User.DoesNotExist:
                messages.error(request, 'No unactivated account found with this email address.')
        
        return redirect('users:login')
    
    return render(request, 'users/resend_activation.html')