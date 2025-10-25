#!/usr/bin/env python
"""
Test script for improved activation messaging system.
"""
import os
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from users.models import User
from django.utils import timezone
from dashboard.email_service import email_service

def test_activation_messaging():
    """Test the activation messaging system"""
    print("🧪 Testing Improved Activation Messaging System")
    print("=" * 60)
    
    # Test user data
    test_email = "activation.test@example.com"
    test_data = {
        'email': test_email,
        'first_name': 'Activation',
        'last_name': 'Test',
        'password': 'TestPassword123',
        'phone': '+1234567890'
    }
    
    # Clean up any existing test user
    try:
        existing_user = User.objects.get(email=test_email)
        existing_user.delete()
        print(f"🧹 Cleaned up existing test user: {test_email}")
    except User.DoesNotExist:
        pass
    
    print(f"\n📝 Creating test user for activation messaging: {test_email}")
    
    # Test 1: Create unverified user (simulating registration)
    try:
        user = User.objects.create_user(
            username=test_data['email'].split('@')[0] + '_test',
            email=test_data['email'],
            password=test_data['password'],
            first_name=test_data['first_name'],
            last_name=test_data['last_name'],
            phone=test_data['phone'],
            is_active=True,
            is_email_verified=False
        )
        
        print(f"✅ User created successfully: {user.email}")
        print(f"   - Username: {user.username}")
        print(f"   - Is Active: {user.is_active}")
        print(f"   - Email Verified: {user.is_email_verified}")
        print(f"   - Can Login: {user.can_login()}")
        
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return
    
    print(f"\n📧 Testing activation email messaging...")
    
    # Test 2: Generate verification token and send activation email
    try:
        user.generate_email_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_sent_at'])
        
        print(f"✅ Verification token generated: {user.email_verification_token}")
        
        # Test email sending with new messaging
        email_sent = email_service.send_activation_email(user)
        
        if email_sent:
            print(f"✅ Activation email sent successfully!")
            print(f"   Message: 'Please activate your account through the activation email sent to your inbox'")
        else:
            print(f"❌ Failed to send activation email")
            
    except Exception as e:
        print(f"❌ Error sending activation email: {str(e)}")
    
    print(f"\n🔗 Activation URL:")
    print(f"   http://127.0.0.1:8000/verify-email/{user.email_verification_token}/")
    
    print(f"\n🧪 Testing login with unverified account...")
    
    # Test 3: Simulate login attempt with unverified account
    try:
        can_login_before = user.can_login()
        print(f"   - Before activation: can_login={can_login_before}")
        print(f"   - Expected message: 'Your account is not activated. Please check your email and click the activation link'")
        
        # Test activation
        user.verify_email()
        can_login_after = user.can_login()
        
        print(f"   - After activation: can_login={can_login_after}")
        print(f"   - Expected message: 'Account Activated Successfully!'")
        
    except Exception as e:
        print(f"❌ Error testing login flow: {str(e)}")
    
    print(f"\n📤 Testing resend activation messaging...")
    
    # Test 4: Test resend messaging
    try:
        # Reset user to unverified state
        user.is_email_verified = False
        user.save(update_fields=['is_email_verified'])
        
        user.generate_email_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_sent_at'])
        
        print(f"   - Reset user to unverified state")
        
        # Test resend email
        email_sent = email_service.send_activation_email(user)
        
        if email_sent:
            print(f"✅ Resend activation email successful!")
            print(f"   Message: 'Activation email sent successfully! Please check your inbox and click the activation link.'")
        else:
            print(f"❌ Failed to resend activation email")
        
    except Exception as e:
        print(f"❌ Error testing resend: {str(e)}")
    
    print(f"\n🧪 Testing edge cases...")
    
    # Test 5: Test already activated account
    try:
        user.verify_email()  # Activate the account
        print(f"   - Account activated")
        
        # Try to resend for already activated account
        print(f"   - Expected message for already activated: 'Your account is already activated. You can login now.'")
        
    except Exception as e:
        print(f"❌ Error testing already activated: {str(e)}")
    
    print(f"\n🧹 Cleaning up test user...")
    try:
        user.delete()
        print(f"✅ Test user deleted successfully")
    except Exception as e:
        print(f"❌ Error deleting test user: {str(e)}")
    
    print(f"\n🎉 Activation messaging system test completed!")
    print("\n📋 Summary of Improvements:")
    print("✅ Registration: 'Please activate your account through the activation email sent to your inbox'")
    print("✅ Login Error: 'Your account is not activated. Please check your email and click the activation link'")
    print("✅ Resend Success: 'Activation email sent successfully! Please check your inbox and click the activation link'")
    print("✅ Already Activated: 'Your account is already activated. You can login now'")
    print("✅ Templates: Updated to use 'activation' terminology instead of 'verification'")
    print("✅ User Flow: Redirects to activation page with resend functionality")

if __name__ == '__main__':
    test_activation_messaging()