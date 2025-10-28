#!/usr/bin/env python3
"""
Test script to verify image modal functionality
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product, ProductVariant, Category
from products.models import Review, ReviewImage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string

def test_reviews_page_modal():
    """Test that the reviews page contains proper Bootstrap modal structure"""
    
    # Create test data
    client = Client()
    
    try:
        # Get the reviews page
        response = client.get('/reviews/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for Bootstrap CSS
            bootstrap_css_present = 'bootstrap@5.3.0/dist/css/bootstrap.min.css' in content
            print(f"✓ Bootstrap CSS present: {bootstrap_css_present}")
            
            # Check for Bootstrap JS
            bootstrap_js_present = 'bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js' in content
            print(f"✓ Bootstrap JS present: {bootstrap_js_present}")
            
            # Check for image modal structure
            modal_present = 'id="imageModal"' in content
            print(f"✓ Image modal present: {modal_present}")
            
            # Check for modal attributes on images
            modal_attributes_present = 'data-bs-toggle="modal"' in content and 'data-bs-target="#imageModal"' in content
            print(f"✓ Modal attributes on images: {modal_attributes_present}")
            
            # Check for modal event handling JavaScript
            modal_js_present = 'imageModal.addEventListener' in content and 'show.bs.modal' in content
            print(f"✓ Modal JavaScript present: {modal_js_present}")
            
            if all([bootstrap_css_present, bootstrap_js_present, modal_present, modal_attributes_present, modal_js_present]):
                print("\n🎉 SUCCESS: All modal components are properly configured!")
                print("The image modal should now work correctly when clicking on review images.")
                
                # Additional tips
                print("\n📝 Modal Functionality:")
                print("1. Bootstrap 5 CSS and JS are now loaded")
                print("2. Images have proper data-bs-toggle and data-bs-target attributes")
                print("3. Modal event handlers are in place to set image src and caption")
                print("4. Clicking on any review image should open the modal with full-size image")
                
                return True
            else:
                print("\n❌ ISSUE: Some modal components are missing")
                return False
        else:
            print(f"❌ ERROR: Reviews page returned status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == '__main__':
    print("🔍 Testing Image Modal Configuration...")
    print("=" * 50)
    
    success = test_reviews_page_modal()
    
    if success:
        print("\n✅ Image modal is ready to use!")
        print("Visit http://127.0.0.1:8000/reviews/ to test the functionality")
    else:
        print("\n❌ Image modal needs additional configuration")

    print("\n" + "=" * 50)