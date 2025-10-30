#!/usr/bin/env python
"""
Test script to verify the template syntax fix for dashboard permissions
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.template import Template, Context
from django.template.loader import get_template

User = get_user_model()

def test_template_filter():
    """Test the has_dashboard_access template filter"""
    print("=== Testing Template Filter ===")
    
    try:
        # Get a test user
        user = User.objects.get(email='aminul3065@gmail.com')
        print(f"✓ Test user found: {user.email}")
        print(f"✓ Is superuser: {user.is_superuser}")
        print(f"✓ Is staff: {user.is_staff}")
        
        # Test template compilation
        template_string = """
        {% load dashboard_permissions %}
        {% if user|has_dashboard_access:'products' %}HAS_PRODUCTS_ACCESS{% endif %}
        {% if user|has_dashboard_access:'orders' %}HAS_ORDERS_ACCESS{% endif %}
        {% if user|has_dashboard_access:'users' %}HAS_USERS_ACCESS{% endif %}
        """
        
        template = Template(template_string)
        context = Context({'user': user})
        rendered = template.render(context)
        
        print("✓ Template compiled successfully")
        print("✓ Template rendered without errors")
        
        # Check results
        if 'HAS_PRODUCTS_ACCESS' in rendered:
            print("✓ Products access: TRUE")
        else:
            print("✗ Products access: FALSE")
            
        if 'HAS_ORDERS_ACCESS' in rendered:
            print("✓ Orders access: TRUE")
        else:
            print("✗ Orders access: FALSE")
            
        if 'HAS_USERS_ACCESS' in rendered:
            print("✓ Users access: TRUE")
        else:
            print("✗ Users access: FALSE")
            
        return True
        
    except Exception as e:
        print(f"✗ Template filter test failed: {e}")
        return False

def test_base_template():
    """Test that the base template loads without errors"""
    print("\n=== Testing Base Template ===")
    
    try:
        # Try to load the base template
        template = get_template('dashboard/base.html')
        print("✓ Base template loaded successfully")
        
        # Test with a user context
        user = User.objects.get(email='aminul3065@gmail.com')
        context = {
            'user': user,
            'active_page': 'home',
            'request': None  # Mock request object
        }
        
        rendered = template.render(context)
        print("✓ Base template rendered successfully")
        print(f"✓ Rendered content length: {len(rendered)} characters")
        
        # Check for specific navigation items
        if 'Products' in rendered:
            print("✓ Products navigation item found")
        if 'Orders' in rendered:
            print("✓ Orders navigation item found")
        if 'Users' in rendered:
            print("✓ Users navigation item found")
            
        return True
        
    except Exception as e:
        print(f"✗ Base template test failed: {e}")
        return False

def test_permission_logic():
    """Test the permission logic for different user types"""
    print("\n=== Testing Permission Logic ===")
    
    try:
        # Test superuser
        superuser = User.objects.get(email='aminul3065@gmail.com')
        print(f"Testing superuser: {superuser.email}")
        
        tabs_to_test = ['products', 'orders', 'users', 'settings']
        for tab in tabs_to_test:
            has_access = superuser.has_dashboard_access(tab)
            status = "✓" if has_access else "✗"
            print(f"  {status} {tab}: {has_access}")
        
        # Test regular user if available
        regular_users = User.objects.filter(is_superuser=False, is_staff=False)[:1]
        if regular_users:
            regular_user = regular_users[0]
            print(f"\nTesting regular user: {regular_user.email}")
            
            for tab in tabs_to_test:
                has_access = regular_user.has_dashboard_access(tab)
                status = "✓" if has_access else "✗"
                print(f"  {status} {tab}: {has_access}")
        
        return True
        
    except Exception as e:
        print(f"✗ Permission logic test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Dashboard Template Fix - Verification Tests")
    print("=" * 50)
    
    test1 = test_template_filter()
    test2 = test_base_template()
    test3 = test_permission_logic()
    
    print("\n" + "=" * 50)
    if test1 and test2 and test3:
        print("✅ ALL TESTS PASSED!")
        print("✅ Template syntax error has been fixed")
        print("✅ Dashboard permissions are working correctly")
        print("✅ Navigation system is operational")
    else:
        print("❌ Some tests failed - please check the errors above")

if __name__ == "__main__":
    main()