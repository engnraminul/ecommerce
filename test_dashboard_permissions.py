#!/usr/bin/env python
"""
Test script for dashboard permissions
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import DashboardPermission

User = get_user_model()

def test_dashboard_permissions():
    print("Testing Dashboard Permissions System")
    print("=" * 50)
    
    # Test the promoted user
    try:
        user = User.objects.get(email='aminul3065@gmail.com')
        print(f"✓ Found user: {user.username} ({user.email})")
        print(f"  - Is superuser: {user.is_superuser}")
        print(f"  - Is staff: {user.is_staff}")
        print(f"  - Is active: {user.is_active}")
        
        # Test dashboard access method
        print(f"  - Has access to products: {user.has_dashboard_access('products')}")
        print(f"  - Has access to users: {user.has_dashboard_access('users')}")
        print(f"  - Has access to orders: {user.has_dashboard_access('orders')}")
        
        # Check permissions object
        try:
            perms = user.dashboard_permissions
            print(f"  - Dashboard permissions exist: Yes")
            print(f"  - Allowed tabs count: {len(perms.allowed_tabs)}")
            tab_names = perms.get_allowed_tab_names()
            print(f"  - First 5 tabs: {tab_names[:5]}")
        except DashboardPermission.DoesNotExist:
            print("  - Dashboard permissions: Not set")
        
    except User.DoesNotExist:
        print("✗ User aminul3065@gmail.com not found")
    
    print("\n" + "=" * 50)
    
    # Test a regular user
    regular_users = User.objects.filter(is_staff=False, is_superuser=False)[:1]
    if regular_users:
        user = regular_users[0]
        print(f"✓ Testing regular user: {user.username}")
        print(f"  - Has access to products: {user.has_dashboard_access('products')}")
        print(f"  - Has access to users: {user.has_dashboard_access('users')}")
        print(f"  - Has access to orders: {user.has_dashboard_access('orders')}")
        
        try:
            perms = user.dashboard_permissions
            print(f"  - Allowed tabs count: {len(perms.allowed_tabs)}")
        except DashboardPermission.DoesNotExist:
            print("  - No dashboard permissions set")
    
    print("\n" + "=" * 50)
    print("Dashboard Permissions Summary:")
    total_users = User.objects.count()
    superusers = User.objects.filter(is_superuser=True).count()
    staff_users = User.objects.filter(is_staff=True, is_superuser=False).count()
    regular_users = User.objects.filter(is_staff=False, is_superuser=False).count()
    with_perms = DashboardPermission.objects.count()
    
    print(f"  - Total users: {total_users}")
    print(f"  - Superusers: {superusers}")
    print(f"  - Staff users: {staff_users}")
    print(f"  - Regular users: {regular_users}")
    print(f"  - Users with dashboard permissions: {with_perms}")
    
    # Test available tabs
    print(f"\nAvailable Dashboard Tabs ({len(DashboardPermission.DASHBOARD_TABS)}):")
    for code, name in DashboardPermission.DASHBOARD_TABS:
        print(f"  - {code}: {name}")

if __name__ == "__main__":
    test_dashboard_permissions()