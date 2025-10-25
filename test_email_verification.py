#!/usr/bin/env python
"""
Test script for email verification system.
"""
import os
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from users.models import User
from django.utils import timezone
from dashboard.email_service import email_service

def test_email_verification():
    """Test the email verification system"""
    print("🧪 Testing Email Verification System")
    print("=" * 50)
    
    # Test user data
    test_email = "test.user@example.com"
    test_data = {
        'email': test_email,
        'first_name': 'Test',
        'last_name': 'User',
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
    
    print(f"\n📝 Creating test user: {test_email}")
    
    # Create user (similar to registration flow)
    try:
        user = User.objects.create_user(
            username=test_data['email'].split('@')[0],
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
    
    print(f"\n📧 Generating email verification token...")
    
    # Generate verification token
    try:
        user.generate_email_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_sent_at'])
        
        print(f"✅ Verification token generated: {user.email_verification_token}")
        print(f"   - Token expires: {user.is_email_verification_expired()}")
        
    except Exception as e:
        print(f"❌ Error generating token: {str(e)}")
        return
    
    print(f"\n📤 Testing email sending...")
    
    # Test email sending
    try:
        email_sent = email_service.send_activation_email(user)
        
        if email_sent:
            print(f"✅ Activation email sent successfully!")
        else:
            print(f"❌ Failed to send activation email")
            
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
    
    print(f"\n🔗 Verification URL:")
    print(f"   http://127.0.0.1:8000/verify-email/{user.email_verification_token}/")
    
    print(f"\n🧪 Testing email verification...")
    
    # Test email verification
    try:
        print(f"   - Before verification: verified={user.is_email_verified}, can_login={user.can_login()}")
        
        user.verify_email()
        
        print(f"   - After verification: verified={user.is_email_verified}, can_login={user.can_login()}")
        print(f"✅ Email verification successful!")
        
    except Exception as e:
        print(f"❌ Error verifying email: {str(e)}")
    
    print(f"\n🧹 Cleaning up test user...")
    try:
        user.delete()
        print(f"✅ Test user deleted successfully")
    except Exception as e:
        print(f"❌ Error deleting test user: {str(e)}")
    
    print(f"\n🎉 Email verification system test completed!")

if __name__ == '__main__':
    test_email_verification()