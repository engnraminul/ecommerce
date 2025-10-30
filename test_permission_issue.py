#!/usr/bin/env python
"""
Test script to verify dashboard display with limited permissions
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

def test_template_with_limited_user():
    """Test template rendering with limited user"""
    print("=== Testing Template with Limited User ===")
    
    # Get a user with limited permissions
    limited_user = User.objects.get(email='test@example.com')
    print(f"Testing with user: {limited_user.email}")
    print(f"Is superuser: {limited_user.is_superuser}")
    print(f"Is staff: {limited_user.is_staff}")
    
    # Get their permissions
    perm = DashboardPermission.objects.get(user=limited_user)
    print(f"Allowed tabs: {perm.allowed_tabs}")
    
    # Test template rendering for each navigation item
    template_string = """
    {% load dashboard_permissions %}
    {% if user.is_superuser or user.is_staff or user|has_dashboard_access:'products' %}PRODUCTS_VISIBLE{% endif %}
    {% if user.is_superuser or user.is_staff or user|has_dashboard_access:'categories' %}CATEGORIES_VISIBLE{% endif %}
    {% if user.is_superuser or user.is_staff or user|has_dashboard_access:'users' %}USERS_VISIBLE{% endif %}
    {% if user.is_superuser or user.is_staff or user|has_dashboard_access:'settings' %}SETTINGS_VISIBLE{% endif %}
    """
    
    template = Template(template_string)
    context = Context({'user': limited_user})
    rendered = template.render(context)
    
    print("\nTemplate rendering results:")
    print("- Products visible:", "PRODUCTS_VISIBLE" in rendered)
    print("- Categories visible:", "CATEGORIES_VISIBLE" in rendered)
    print("- Users visible:", "USERS_VISIBLE" in rendered)
    print("- Settings visible:", "SETTINGS_VISIBLE" in rendered)
    
    # Expected results for test@example.com (should only have: home, orders, products, statistics)
    expected_results = {
        'products': True,    # Should be visible
        'categories': False, # Should be hidden
        'users': False,      # Should be hidden
        'settings': False    # Should be hidden
    }
    
    actual_results = {
        'products': "PRODUCTS_VISIBLE" in rendered,
        'categories': "CATEGORIES_VISIBLE" in rendered,
        'users': "USERS_VISIBLE" in rendered,
        'settings': "SETTINGS_VISIBLE" in rendered
    }
    
    print("\nComparison:")
    all_correct = True
    for tab, expected in expected_results.items():
        actual = actual_results[tab]
        status = "✓" if actual == expected else "✗"
        print(f"{status} {tab}: Expected {expected}, Got {actual}")
        if actual != expected:
            all_correct = False
    
    return all_correct

def check_current_dashboard_logic():
    """Check the current template logic in the actual dashboard"""
    print("\n=== Checking Current Dashboard Template Logic ===")
    
    # Read the current base template
    try:
        with open('dashboard/templates/dashboard/base.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if template logic is correct
        if "user.is_superuser or user.is_staff or user|has_dashboard_access:" in content:
            print("✓ Template uses OR logic (user.is_superuser OR user.is_staff OR permission)")
            print("⚠️  ISSUE FOUND: This means staff/superuser ALWAYS see all tabs!")
            
            # Count occurrences
            staff_checks = content.count("user.is_superuser or user.is_staff")
            print(f"Found {staff_checks} instances of superuser/staff bypass logic")
            
            return False  # This is the issue!
        else:
            print("Template logic appears different")
            return True
            
    except FileNotFoundError:
        print("Could not read dashboard template")
        return False

def identify_the_problem():
    """Identify the exact problem"""
    print("\n=== PROBLEM IDENTIFICATION ===")
    
    print("The issue is in the template logic:")
    print("Current: {% if user.is_superuser or user.is_staff or user|has_dashboard_access:'tab' %}")
    print("Problem: This means if user is_staff=True, they see ALL tabs regardless of permissions")
    print("")
    print("Solution needed:")
    print("- Remove the 'or user.is_staff' part for limited staff users")
    print("- Or use different logic to respect staff permission limitations")
    print("")
    print("Current user types in system:")
    
    users = User.objects.all()
    for user in users:
        user_type = []
        if user.is_superuser:
            user_type.append("SUPERUSER")
        if user.is_staff:
            user_type.append("STAFF")
        if not user.is_superuser and not user.is_staff:
            user_type.append("REGULAR")
        
        print(f"- {user.email}: {', '.join(user_type)}")

def main():
    """Run all tests"""
    print("Dashboard Permission Issue Analysis")
    print("=" * 50)
    
    template_correct = test_template_with_limited_user()
    dashboard_correct = check_current_dashboard_logic()
    identify_the_problem()
    
    print("\n" + "=" * 50)
    if not dashboard_correct:
        print("❌ ISSUE IDENTIFIED: Staff users bypass permission system!")
        print("🔧 Fix needed: Modify template logic to respect staff permissions")
    else:
        print("✅ No obvious issues found in template logic")

if __name__ == "__main__":
    main()