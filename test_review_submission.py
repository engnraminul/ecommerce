#!/usr/bin/env python
"""
Test script to verify review submission functionality
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from products.models import Product, Review
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
import json

def test_review_submission():
    """Test the review submission endpoint"""
    client = Client()
    
    # Get a test product
    try:
        product = Product.objects.filter(is_active=True).first()
        if not product:
            print("❌ No active products found")
            return
        
        print(f"✅ Testing with product: {product.name} (ID: {product.id})")
        
        # Test data
        review_data = {
            'rating': 5,
            'comment': 'Test review comment',
            'title': 'Test Review Title',
            'guest_name': 'Test User',
            'guest_email': 'test@example.com'
        }
        
        # Test the submission endpoint - use the correct URL pattern
        try:
            url = reverse('frontend:submit_review', kwargs={'product_id': product.id})
            print(f"📡 Testing URL: {url}")
        except:
            url = f'/frontend/submit-review/{product.id}/'
            print(f"📡 Testing URL (fallback): {url}")
        
        response = client.post(url, review_data, follow=True)
        
        print(f"🔍 Response status: {response.status_code}")
        print(f"🔍 Response content (first 500 chars): {response.content.decode()[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    print("✅ Review submission successful!")
                    
                    # Verify review was saved
                    latest_review = Review.objects.filter(product=product).last()
                    if latest_review:
                        print(f"✅ Review saved to database: ID {latest_review.id}")
                        print(f"   - Rating: {latest_review.rating}")
                        print(f"   - Comment: {latest_review.comment}")
                        print(f"   - Guest name: {latest_review.guest_name}")
                    else:
                        print("❌ Review not found in database")
                else:
                    print(f"❌ Review submission failed: {data}")
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_review_submission()
