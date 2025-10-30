#!/usr/bin/env python
"""
Debug script to find the exact issue with staff user permissions
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import DashboardPermission

User = get_user_model()

def debug_specific_user():
    """Debug the specific user that's failing"""
    print("=== Debugging phonekobra@gmail.com ===")
    
    user = User.objects.get(email='phonekobra@gmail.com')
    print(f"User: {user.email}")
    print(f"Is superuser: {user.is_superuser}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is active: {user.is_active}")
    print(f"Is authenticated: {user.is_authenticated}")
    
    # Check permission object
    try:
        perm = DashboardPermission.objects.get(user=user)
        print(f"Permission object found")
        print(f"Allowed tabs: {perm.allowed_tabs}")
        print(f"Number of allowed tabs: {len(perm.allowed_tabs)}")
        
        # Test specific tab access step by step
        test_tab = 'categories'
        print(f"\nTesting access to '{test_tab}' tab:")
        
        print(f"1. Is superuser: {user.is_superuser}")
        if user.is_superuser:
            print("   -> Should return True (superuser bypass)")
        else:
            print("   -> Continue to permission check")
            print(f"2. Checking permission object...")
            print(f"3. '{test_tab}' in allowed_tabs: {test_tab in perm.allowed_tabs}")
            print(f"4. has_tab_access result: {perm.has_tab_access(test_tab)}")
        
        # Call the actual method
        result = user.has_dashboard_access(test_tab)
        print(f"5. Final result: {result}")
        
        # Check if there's some issue with the method
        print(f"\nMethod debug:")
        print(f"user.is_superuser: {user.is_superuser}")
        
        # Manual check without method
        if user.is_superuser:
            manual_result = True
        else:
            try:
                manual_result = user.dashboard_permissions.has_tab_access(test_tab)
            except DashboardPermission.DoesNotExist:
                manual_result = False
        
        print(f"Manual calculation: {manual_result}")
        print(f"Method result matches manual: {result == manual_result}")
        
    except DashboardPermission.DoesNotExist:
        print("No permission object found")

def debug_template_filter():
    """Debug the template filter directly"""
    print("\n=== Debugging Template Filter ===")
    
    from users.templatetags.dashboard_permissions import has_dashboard_access
    
    user = User.objects.get(email='phonekobra@gmail.com')
    test_tab = 'categories'
    
    print(f"Testing template filter for {user.email} and '{test_tab}'")
    
    # Step through the filter logic
    print(f"1. User authenticated: {user.is_authenticated}")
    print(f"2. User is superuser: {user.is_superuser}")
    
    if user.is_superuser:
        print("   -> Filter should return True (superuser)")
    else:
        print("   -> Filter should call user.has_dashboard_access()")
        method_result = user.has_dashboard_access(test_tab)
        print(f"   -> Method result: {method_result}")
    
    filter_result = has_dashboard_access(user, test_tab)
    print(f"3. Filter result: {filter_result}")

def check_all_staff_users():
    """Check all staff users"""
    print("\n=== Checking All Staff Users ===")
    
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    
    for user in staff_users:
        print(f"\n--- {user.email} ---")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Is staff: {user.is_staff}")
        
        try:
            perm = DashboardPermission.objects.get(user=user)
            print(f"Allowed tabs ({len(perm.allowed_tabs)}): {perm.allowed_tabs}")
            
            # Test access to a tab they shouldn't have
            all_tabs = ['categories', 'settings', 'users', 'api_docs']
            for tab in all_tabs:
                if tab not in perm.allowed_tabs:
                    access = user.has_dashboard_access(tab)
                    print(f"Access to '{tab}' (not in allowed): {access}")
                    if access:
                        print(f"  ⚠️  ERROR: User has access but shouldn't!")
                    break
                    
        except DashboardPermission.DoesNotExist:
            print("No permission object")

def main():
    """Run all debug functions"""
    print("Staff User Permission Debug")
    print("=" * 50)
    
    debug_specific_user()
    debug_template_filter() 
    check_all_staff_users()

if __name__ == "__main__":
    main()