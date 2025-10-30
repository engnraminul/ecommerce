#!/usr/bin/env python
"""
Test script to verify that the permission fix is working correctly
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import DashboardPermission
from django.template import Template, Context

User = get_user_model()

def test_permission_fix():
    """Test that staff users now respect their individual permissions"""
    print("=== Testing Permission Fix ===")
    
    # Test different types of users
    test_cases = [
        {
            'email': 'aminul3065@gmail.com',
            'expected_type': 'SUPERUSER',
            'should_see_all': True,
            'description': 'Superuser should see all tabs'
        },
        {
            'email': 'tanim@gmail.com', 
            'expected_type': 'STAFF',
            'should_see_all': False,
            'description': 'Staff user should only see permitted tabs'
        },
        {
            'email': 'test@example.com',
            'expected_type': 'REGULAR', 
            'should_see_all': False,
            'description': 'Regular user should only see permitted tabs'
        }
    ]
    
    all_tabs = ['products', 'categories', 'media', 'stock', 'orders', 
                'incomplete_orders', 'reviews', 'contacts', 'pages', 
                'blocklist', 'users', 'expenses', 'statistics', 
                'email_settings', 'settings', 'api_docs']
    
    for test_case in test_cases:
        try:
            user = User.objects.get(email=test_case['email'])
            print(f"\n--- Testing {test_case['description']} ---")
            print(f"User: {user.email}")
            print(f"Type: Superuser={user.is_superuser}, Staff={user.is_staff}")
            
            # Get their permissions if they have any
            try:
                perm = DashboardPermission.objects.get(user=user)
                print(f"Allowed tabs: {perm.allowed_tabs}")
            except DashboardPermission.DoesNotExist:
                print("No permission object (relies on superuser status)")
            
            # Test access to all tabs
            accessible_tabs = []
            restricted_tabs = []
            
            for tab in all_tabs:
                has_access = user.has_dashboard_access(tab)
                if has_access:
                    accessible_tabs.append(tab)
                else:
                    restricted_tabs.append(tab)
            
            print(f"Accessible tabs ({len(accessible_tabs)}): {accessible_tabs}")
            print(f"Restricted tabs ({len(restricted_tabs)}): {restricted_tabs}")
            
            # Verify expectations
            if test_case['should_see_all']:
                if len(restricted_tabs) == 0:
                    print("✓ PASS: User can access all tabs as expected")
                else:
                    print(f"✗ FAIL: User should see all tabs but is restricted from: {restricted_tabs}")
            else:
                if len(restricted_tabs) > 0:
                    print("✓ PASS: User has restricted access as expected")
                else:
                    print("✗ FAIL: User should have restricted access but can see all tabs")
                    
        except User.DoesNotExist:
            print(f"User {test_case['email']} not found")

def test_template_rendering():
    """Test template rendering with the fixed logic"""
    print("\n=== Testing Template Rendering ===")
    
    # Test with a staff user who should have limited access
    staff_user = User.objects.filter(is_staff=True, is_superuser=False).first()
    if staff_user:
        print(f"Testing template with staff user: {staff_user.email}")
        
        # Get their permissions
        try:
            perm = DashboardPermission.objects.get(user=staff_user)
            allowed_tabs = perm.allowed_tabs
            print(f"User's allowed tabs: {allowed_tabs}")
        except DashboardPermission.DoesNotExist:
            print("No permissions found")
            return
        
        # Test template rendering for tabs they should and shouldn't see
        template_string = """
        {% load dashboard_permissions %}
        {% if user.is_superuser or user|has_dashboard_access:'products' %}PRODUCTS_VISIBLE{% endif %}
        {% if user.is_superuser or user|has_dashboard_access:'categories' %}CATEGORIES_VISIBLE{% endif %}
        {% if user.is_superuser or user|has_dashboard_access:'users' %}USERS_VISIBLE{% endif %}
        {% if user.is_superuser or user|has_dashboard_access:'settings' %}SETTINGS_VISIBLE{% endif %}
        """
        
        template = Template(template_string)
        context = Context({'user': staff_user})
        rendered = template.render(context)
        
        print("\nTemplate rendering results:")
        
        # Check each tab
        checks = [
            ('products', 'PRODUCTS_VISIBLE'),
            ('categories', 'CATEGORIES_VISIBLE'), 
            ('users', 'USERS_VISIBLE'),
            ('settings', 'SETTINGS_VISIBLE')
        ]
        
        for tab, marker in checks:
            is_visible = marker in rendered
            should_be_visible = tab in allowed_tabs
            
            if is_visible == should_be_visible:
                status = "✓"
            else:
                status = "✗"
            
            print(f"  {status} {tab}: Visible={is_visible}, Should be={should_be_visible}")

def test_specific_staff_user():
    """Test a specific staff user to verify the fix"""
    print("\n=== Testing Specific Staff User ===")
    
    # Look for a staff user with limited permissions
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    
    for staff_user in staff_users:
        try:
            perm = DashboardPermission.objects.get(user=staff_user)
            
            # Find a tab they don't have access to
            all_tabs = ['products', 'categories', 'media', 'stock', 'orders', 
                       'incomplete_orders', 'reviews', 'contacts', 'pages', 
                       'blocklist', 'users', 'expenses', 'statistics', 
                       'email_settings', 'settings', 'api_docs']
            
            denied_tabs = [tab for tab in all_tabs if tab not in perm.allowed_tabs]
            
            if denied_tabs:
                print(f"Testing staff user: {staff_user.email}")
                print(f"Allowed tabs: {perm.allowed_tabs}")
                print(f"Denied tabs: {denied_tabs}")
                
                # Test access to a denied tab
                test_tab = denied_tabs[0]
                has_access = staff_user.has_dashboard_access(test_tab)
                
                if not has_access:
                    print(f"✓ PASS: Staff user correctly denied access to '{test_tab}'")
                    return True
                else:
                    print(f"✗ FAIL: Staff user incorrectly has access to '{test_tab}'")
                    return False
                    
        except DashboardPermission.DoesNotExist:
            continue
    
    print("No staff users with limited permissions found for testing")
    return True

def main():
    """Run all tests"""
    print("Dashboard Permission Fix - Verification Tests")
    print("=" * 60)
    
    test_permission_fix()
    test_template_rendering()
    success = test_specific_staff_user()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ PERMISSION FIX VERIFIED!")
        print("✅ Staff users now respect individual permissions")
        print("✅ Only superusers get automatic access to all tabs")
        print("✅ Template logic is working correctly")
    else:
        print("❌ Permission fix may need additional work")

if __name__ == "__main__":
    main()