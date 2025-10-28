#!/usr/bin/env python
"""
Test script to verify reviews dashboard functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from products.models import Review

User = get_user_model()

def test_reviews_dashboard():
    print("Testing Reviews Dashboard Functionality...")
    
    # Get an admin user (staff member)
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ No admin user found. Creating one...")
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        print("✓ Created admin user")
    
    print(f"✓ Using admin user: {admin_user.username}")
    
    # Test client
    client = Client()
    client.force_login(admin_user)
    
    # Test 1: Access reviews dashboard
    print("\n--- Test 1: Access Reviews Dashboard ---")
    response = client.get('/mb-admin/reviews/')
    if response.status_code == 200:
        print("✓ Reviews dashboard loads successfully")
        
        # Check if statistics are in context
        if hasattr(response, 'context') and response.context:
            context = response.context
            print(f"  Total reviews: {context.get('total_reviews', 'N/A')}")
            print(f"  Approved reviews: {context.get('approved_reviews', 'N/A')}")
            print(f"  Pending reviews: {context.get('pending_reviews', 'N/A')}")
            print(f"  Verified reviews: {context.get('verified_reviews', 'N/A')}")
            print(f"  Reviews with images: {context.get('reviews_with_images', 'N/A')}")
            print(f"  Average rating: {context.get('avg_rating', 'N/A')}")
        else:
            print("✓ Dashboard loads but context not available in test mode")
            
        # Check if the page contains review elements
        content = response.content.decode('utf-8')
        if 'Reviews Management' in content:
            print("✓ Reviews management page content found")
        if 'review-checkbox' in content:
            print("✓ Review selection checkboxes found")
        if 'bulkAction' in content:
            print("✓ Bulk action functionality found")
            
    else:
        print(f"❌ Reviews dashboard failed with status {response.status_code}")
        print(response.content.decode('utf-8')[:500])
    
    # Test 2: Test review filters
    print("\n--- Test 2: Test Review Filters ---")
    test_filters = [
        ('status', 'approved'),
        ('status', 'pending'),
        ('rating', '5'),
        ('verified', 'verified'),
    ]
    
    for filter_name, filter_value in test_filters:
        response = client.get(f'/mb-admin/reviews/?{filter_name}={filter_value}')
        if response.status_code == 200:
            print(f"✓ Filter {filter_name}={filter_value} works")
        else:
            print(f"❌ Filter {filter_name}={filter_value} failed")
    
    # Test 3: Test search functionality
    print("\n--- Test 3: Test Search ---")
    response = client.get('/mb-admin/reviews/?search=test')
    if response.status_code == 200:
        print("✓ Search functionality works")
    else:
        print("❌ Search functionality failed")
    
    # Test 4: Test review data
    print("\n--- Test 4: Review Data ---")
    reviews = Review.objects.all()
    print(f"✓ Total reviews in database: {reviews.count()}")
    
    approved_count = reviews.filter(is_approved=True).count()
    pending_count = reviews.filter(is_approved=False).count()
    verified_count = reviews.filter(is_verified_purchase=True).count()
    with_images_count = reviews.filter(images__isnull=False).distinct().count()
    
    print(f"  - Approved: {approved_count}")
    print(f"  - Pending: {pending_count}")
    print(f"  - Verified: {verified_count}")
    print(f"  - With images: {with_images_count}")
    
    if reviews.exists():
        latest_review = reviews.order_by('-created_at').first()
        print(f"  - Latest review: {latest_review}")
        print(f"  - By: {latest_review.reviewer_name}")
        print(f"  - Product: {latest_review.product.name}")
        print(f"  - Rating: {latest_review.rating}/5")
    
    print(f"\n🌐 Visit: http://127.0.0.1:8000/mb-admin/reviews/")
    print("✅ Reviews dashboard test completed!")

if __name__ == '__main__':
    test_reviews_dashboard()