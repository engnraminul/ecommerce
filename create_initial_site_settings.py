#!/usr/bin/env python
"""
Script to create initial site settings with default values.
Run this after migrating the SiteSettings model.
"""

import os
import sys
import django

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from settings.models import SiteSettings

def create_initial_site_settings():
    """Create initial site settings if none exist"""
    
    # Check if any site settings exist
    if SiteSettings.objects.exists():
        print("Site settings already exist. No action needed.")
        return
    
    # Create initial site settings
    site_settings = SiteSettings.objects.create(
        site_name="My Brand Store",
        site_tagline="Your one-stop shop for quality products",
        contact_phone="+1 123-456-7890",
        contact_email="contact@mybrandstore.com",
        contact_address="123 Main Street, City, State 12345, Country",
        footer_short_text="Your trusted online shopping destination with quality products and excellent service.",
        facebook_link="",
        youtube_link="",
        quick_links_title="Quick Links",
        customer_service_title="Customer Service",
        home_text="Home",
        home_url="/",
        products_text="Products",
        products_url="/products",
        categories_text="Categories", 
        categories_url="/categories",
        about_text="About Us",
        about_url="/about",
        contact_text="Contact",
        contact_url="/contact",
        track_order_text="Track Order",
        track_order_url="/track-order",
        return_policy_text="Return Policy",
        return_policy_url="/return-policy",
        shipping_info_text="Shipping Info",
        shipping_info_url="/shipping-info",
        fraud_checker_text="Fraud Checker",
        fraud_checker_url="/fraud-checker",
        faq_text="FAQ",
        faq_url="/faq",
        copyright_text="© {year} My Brand Store. All rights reserved.",
        why_shop_section_title="Why Shop With Us?",
        feature1_title="Fast Delivery",
        feature1_subtitle="Quick & reliable shipping",
        feature2_title="Quality Products",
        feature2_subtitle="Premium quality guaranteed",
        feature3_title="24/7 Support",
        feature3_subtitle="Round the clock assistance",
        feature4_title="Secure Payment",
        feature4_subtitle="Safe & secure transactions",
        is_active=True
    )
    
    print(f"✅ Initial site settings created successfully!")
    print(f"Site Name: {site_settings.site_name}")
    print(f"Site Tagline: {site_settings.site_tagline}")
    print("You can now edit these settings through the Django admin or dashboard.")

if __name__ == "__main__":
    create_initial_site_settings()