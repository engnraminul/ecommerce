#!/usr/bin/env python
"""
Debug script to identify why tab permissions are not working correctly
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import DashboardPermission

User = get_user_model()

def debug_user_permissions():
    """Debug specific user permissions"""
    print("=== Debugging User Permissions ===")
    
    # Check all users and their permissions
    users = User.objects.all()
    for user in users:
        print(f"\n--- User: {user.email} ---")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is active: {user.is_active}")
        
        # Check if they have dashboard permission object
        try:
            perm = DashboardPermission.objects.get(user=user)
            print(f"Has permission object: YES")
            print(f"Allowed tabs ({len(perm.allowed_tabs)}): {perm.allowed_tabs}")
        except DashboardPermission.DoesNotExist:
            print(f"Has permission object: NO")
        
        # Test specific tab access
        test_tabs = ['products', 'users', 'categories', 'settings']
        for tab in test_tabs:
            access = user.has_dashboard_access(tab)
            print(f"  {tab}: {access}")

def debug_template_filter():
    """Debug the template filter logic"""
    print("\n=== Debugging Template Filter ===")
    
    # Import the template filter
    from users.templatetags.dashboard_permissions import has_dashboard_access
    
    # Test with different users
    test_user = User.objects.filter(is_superuser=False, is_staff=False).first()
    if test_user:
        print(f"Testing with regular user: {test_user.email}")
        
        tabs = ['products', 'users', 'categories', 'settings']
        for tab in tabs:
            # Test the filter directly
            filter_result = has_dashboard_access(test_user, tab)
            method_result = test_user.has_dashboard_access(tab)
            
            print(f"  {tab}:")
            print(f"    Template filter: {filter_result}")
            print(f"    User method: {method_result}")
            print(f"    Match: {filter_result == method_result}")

def debug_model_method():
    """Debug the User model has_dashboard_access method"""
    print("\n=== Debugging User Model Method ===")
    
    # Check the User model method implementation
    test_user = User.objects.filter(is_superuser=False, is_staff=False).first()
    if test_user:
        print(f"Testing user: {test_user.email}")
        print(f"Is superuser: {test_user.is_superuser}")
        print(f"Is staff: {test_user.is_staff}")
        
        # Check if the method exists
        if hasattr(test_user, 'has_dashboard_access'):
            print("✓ has_dashboard_access method exists")
            
            # Test method with a tab the user shouldn't have access to
            try:
                result = test_user.has_dashboard_access('settings')
                print(f"Access to 'settings': {result}")
                
                # Check permission object
                try:
                    perm = test_user.dashboardpermission
                    print(f"Permission object found: {perm.allowed_tabs}")
                    
                    # Manual check
                    manual_check = 'settings' in perm.allowed_tabs
                    print(f"Manual check 'settings' in allowed_tabs: {manual_check}")
                    
                except DashboardPermission.DoesNotExist:
                    print("No permission object found")
                    
            except Exception as e:
                print(f"Error calling method: {e}")
        else:
            print("✗ has_dashboard_access method NOT found")

def debug_permission_logic():
    """Debug the permission checking logic step by step"""
    print("\n=== Debugging Permission Logic ===")
    
    # Find a user that should have limited permissions
    limited_users = User.objects.filter(is_superuser=False, is_staff=False)
    
    if limited_users.exists():
        user = limited_users.first()
        print(f"Testing limited user: {user.email}")
        
        # Step-by-step permission check
        print("\nStep-by-step permission check for 'settings' tab:")
        
        print(f"1. Is authenticated: {user.is_authenticated}")
        print(f"2. Is superuser: {user.is_superuser}")
        print(f"3. Is staff: {user.is_staff}")
        
        # Should stop here for regular users and check permissions
        if not user.is_superuser and not user.is_staff:
            print("4. User is regular user, checking permissions...")
            
            try:
                perm = DashboardPermission.objects.get(user=user)
                print(f"5. Permission object found")
                print(f"6. Allowed tabs: {perm.allowed_tabs}")
                print(f"7. 'settings' in allowed_tabs: {'settings' in perm.allowed_tabs}")
                
                # Call the actual method
                result = user.has_dashboard_access('settings')
                print(f"8. Final result: {result}")
                
            except DashboardPermission.DoesNotExist:
                print("5. No permission object found")
                print("6. Should return False")
                result = user.has_dashboard_access('settings')
                print(f"7. Final result: {result}")
    else:
        print("No limited users found for testing")

def main():
    """Run all debug functions"""
    print("Dashboard Permissions Debug - Identifying Issues")
    print("=" * 60)
    
    debug_user_permissions()
    debug_template_filter()
    debug_model_method()
    debug_permission_logic()
    
    print("\n" + "=" * 60)
    print("Debug analysis complete!")

if __name__ == "__main__":
    main()