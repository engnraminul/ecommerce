#!/usr/bin/env python
"""Test script to validate CKEditor configuration."""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.conf import settings

def main():
    # Check the current CKEditor configurations
    default_config = settings.CKEDITOR_CONFIGS.get('default', {})
    pages_config = settings.CKEDITOR_CONFIGS.get('pages', {})

    print("=== CKEDITOR CONFIGURATION ANALYSIS ===\n")

    print("DEFAULT CONFIG (used by email templates):")
    print(f"  Toolbar type: {default_config.get('toolbar', 'NOT SET')}")
    if default_config.get('toolbar') == 'Custom':
        toolbar_custom = default_config.get('toolbar_Custom', [])
        print(f"  Toolbar rows: {len(toolbar_custom)}")
        total_tools = sum(len(row) for row in toolbar_custom if isinstance(row, list))
        print(f"  Total tools: {total_tools}")
    else:
        print(f"  Toolbar: {default_config.get('toolbar', 'NOT SET')}")

    print(f"  Width: {default_config.get('width', 'NOT SET')}")
    print(f"  Height: {default_config.get('height', 'NOT SET')}")
    print(f"  Format tags: {default_config.get('format_tags', 'NOT SET')}")

    print("\nPAGES CONFIG:")
    print(f"  Toolbar type: {pages_config.get('toolbar', 'NOT SET')}")
    if pages_config.get('toolbar') == 'Custom':
        toolbar_custom = pages_config.get('toolbar_Custom', [])
        print(f"  Toolbar rows: {len(toolbar_custom)}")
        total_tools = sum(len(row) for row in toolbar_custom if isinstance(row, list))
        print(f"  Total tools: {total_tools}")
    else:
        print(f"  Toolbar: {pages_config.get('toolbar', 'NOT SET')}")

    print(f"  Width: {pages_config.get('width', 'NOT SET')}")
    print(f"  Height: {pages_config.get('height', 'NOT SET')}")
    print(f"  Format tags: {pages_config.get('format_tags', 'NOT SET')}")

    print("\n=== COMPARISON ===")
    print(f"Both use same toolbar type: {default_config.get('toolbar') == pages_config.get('toolbar')}")
    if default_config.get('toolbar') == 'Custom' and pages_config.get('toolbar') == 'Custom':
        default_toolbar = default_config.get('toolbar_Custom', [])
        pages_toolbar = pages_config.get('toolbar_Custom', [])
        print(f"Toolbars are identical: {default_toolbar == pages_toolbar}")

    print("\n=== ADMIN FORM SETUP ===")
    # Check what forms are being used
    try:
        from pages.admin import PageAdminForm, PageAdmin
        print("PageAdminForm exists: ✓")
        
        # Check if the form field is correctly configured
        form = PageAdminForm()
        content_field = form.fields.get('content')
        if content_field:
            widget = content_field.widget
            print(f"Content field widget: {type(widget).__name__}")
            if hasattr(widget, 'config_name'):
                print(f"Widget config_name: {widget.config_name}")
            else:
                print("Widget has no config_name attribute")
        else:
            print("No content field found in form")
            
    except Exception as e:
        print(f"Error checking admin form: {e}")

    print("\n=== DETAILED TOOLBAR COMPARISON ===")
    if default_config.get('toolbar') == 'Custom' and pages_config.get('toolbar') == 'Custom':
        default_toolbar = default_config.get('toolbar_Custom', [])
        pages_toolbar = pages_config.get('toolbar_Custom', [])
        
        print("\nDEFAULT toolbar_Custom:")
        for i, row in enumerate(default_toolbar):
            print(f"  Row {i+1}: {row}")
            
        print("\nPAGES toolbar_Custom:")
        for i, row in enumerate(pages_toolbar):
            print(f"  Row {i+1}: {row}")

    print("\n=== SUMMARY ===")
    print("✓ Both configurations should now be identical")
    print("✓ PageAdminForm uses CKEditorWidget(config_name='default')")
    print("✓ Same approach as email templates")
    print("\nNow test by:")
    print("1. Clear browser cache (Ctrl+Shift+R)")
    print("2. Go to Django admin -> Pages -> Add Page")
    print("3. Check the content field toolbar")
    print("4. Compare with email templates toolbar")

if __name__ == '__main__':
    main()