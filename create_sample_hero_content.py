#!/usr/bin/env python3
"""
Create sample hero content for testing the carousel
"""
import os
import sys
import django
from django.conf import settings as django_settings

# Add the project directory to the Python path
sys.path.append(r'c:\Users\aminu\OneDrive\Desktop\ecommerce')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from settings.models import HeroContent

def create_sample_hero_content():
    """Create sample hero content for testing"""
    
    # Sample hero slides
    hero_slides = [
        {
            'title': 'Welcome to Our Amazing Store',
            'subtitle': 'Discover premium quality products at unbeatable prices with fast shipping',
            'desktop_image': 'media/hero/desktop-hero-1.jpg',
            'mobile_image': 'media/hero/mobile-hero-1.jpg',
            'primary_button_text': 'Shop Now',
            'primary_button_url': '/products/',
            'secondary_button_text': 'View Categories',
            'secondary_button_url': '/categories/',
            'text_color': '#ffffff',
            'text_shadow': True,
            'background_gradient': 'linear-gradient(135deg, #930000, #7a0000)',
            'display_order': 1,
            'is_active': True
        },
        {
            'title': 'Special Winter Collection',
            'subtitle': 'Stay warm and stylish with our exclusive winter collection. Limited time offers!',
            'desktop_image': 'media/hero/desktop-hero-2.jpg',
            'mobile_image': 'media/hero/mobile-hero-2.jpg',
            'primary_button_text': 'Explore Collection',
            'primary_button_url': '/products/?category=winter',
            'secondary_button_text': 'View Deals',
            'secondary_button_url': '/products/?sale=true',
            'text_color': '#ffffff',
            'text_shadow': True,
            'background_gradient': 'linear-gradient(135deg, #1e3a8a, #1e40af)',
            'display_order': 2,
            'is_active': True
        },
        {
            'title': 'Free Shipping on Orders Over $50',
            'subtitle': 'Get your favorite products delivered to your doorstep with our fast and reliable shipping',
            'desktop_image': 'media/hero/desktop-hero-3.jpg',
            'mobile_image': 'media/hero/mobile-hero-3.jpg',
            'primary_button_text': 'Start Shopping',
            'primary_button_url': '/products/',
            'secondary_button_text': 'Learn More',
            'secondary_button_url': '/shipping-info/',
            'text_color': '#ffffff',
            'text_shadow': True,
            'background_gradient': 'linear-gradient(135deg, #059669, #047857)',
            'display_order': 3,
            'is_active': True
        }
    ]
    
    # Delete existing hero content
    print("Clearing existing hero content...")
    HeroContent.objects.all().delete()
    
    # Create new hero slides
    print("Creating sample hero content...")
    created_slides = []
    
    for slide_data in hero_slides:
        slide = HeroContent.objects.create(**slide_data)
        created_slides.append(slide)
        print(f"✓ Created: {slide.title} (Order: {slide.display_order})")
    
    print(f"\n✅ Successfully created {len(created_slides)} hero slides!")
    print("\nNext steps:")
    print("1. Upload hero images to the media/hero/ folder:")
    print("   - desktop-hero-1.jpg, desktop-hero-2.jpg, desktop-hero-3.jpg (1920x600px)")
    print("   - mobile-hero-1.jpg, mobile-hero-2.jpg, mobile-hero-3.jpg (800x600px)")
    print("2. Go to Django Admin → Settings → Hero Content to manage slides")
    print("3. View the home page to see your hero carousel in action!")
    
    return created_slides

if __name__ == "__main__":
    create_sample_hero_content()