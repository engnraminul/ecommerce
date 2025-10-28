#!/usr/bin/env python3
"""
Test script to verify reviews functionality is working properly
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Review, ReviewImage, Product, Category
from users.models import User
import random

def create_test_data():
    """Create test review data if needed"""
    print("Creating test review data...")
    
    # Create a test user if needed
    user, created = User.objects.get_or_create(
        username='test_reviewer',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'Reviewer'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create a test category and product if needed
    category, _ = Category.objects.get_or_create(
        name='Test Category',
        defaults={'slug': 'test-category'}
    )
    
    product, _ = Product.objects.get_or_create(
        name='Test Product for Reviews',
        defaults={
            'slug': 'test-product-reviews',
            'category': category,
            'price': 99.99,
            'description': 'A test product for review testing'
        }
    )
    
    # Create some test reviews if they don't exist
    if Review.objects.count() < 5:
        comments = [
            "Great product! Really satisfied with the quality.",
            "Good value for money, fast shipping.",
            "Not bad, but could be better. Average quality.",
            "Excellent! Exceeded my expectations.",
            "Poor quality, wouldn't recommend."
        ]
        
        titles = [
            "Highly Recommended",
            "Good Purchase",
            "Average Product", 
            "Outstanding Quality",
            "Disappointing"
        ]
        
        for i in range(5):
            Review.objects.get_or_create(
                user=user,
                product=product,
                rating=random.randint(1, 5),
                defaults={
                    'title': titles[i],
                    'comment': comments[i],
                    'is_approved': random.choice([True, False]),
                    'is_verified_purchase': random.choice([True, False])
                }
            )
    
    print(f"Total reviews in database: {Review.objects.count()}")
    print(f"Approved reviews: {Review.objects.filter(is_approved=True).count()}")
    print(f"Pending reviews: {Review.objects.filter(is_approved=False).count()}")
    print(f"Verified purchases: {Review.objects.filter(is_verified_purchase=True).count()}")

def test_review_functionality():
    """Test various review operations"""
    print("\nTesting review functionality...")
    
    # Test basic queries
    reviews = Review.objects.all()
    print(f"✓ Can query all reviews: {reviews.count()} found")
    
    # Test filtering
    approved = Review.objects.filter(is_approved=True)
    print(f"✓ Can filter approved reviews: {approved.count()} found")
    
    # Test related queries
    reviews_with_products = Review.objects.select_related('product', 'user')
    print(f"✓ Can query reviews with related objects: {reviews_with_products.count()} found")
    
    # Test creating a review
    try:
        if Product.objects.exists() and User.objects.exists():
            product = Product.objects.first()
            user = User.objects.first()
            
            test_review = Review.objects.create(
                user=user,
                product=product,
                rating=5,
                title="Test Review from Script",
                comment="This is a test review created by the test script",
                is_approved=True,
                is_verified_purchase=True
            )
            print(f"✓ Can create new review: {test_review.id}")
            
            # Clean up test review
            test_review.delete()
            print("✓ Can delete review")
        
    except Exception as e:
        print(f"✗ Error creating/deleting test review: {e}")

def check_api_endpoints():
    """Check if API endpoints are properly configured"""
    print("\nChecking API endpoint configurations...")
    
    from dashboard.urls import urlpatterns
    
    # Check if review URLs exist
    review_urls = [pattern for pattern in urlpatterns if 'review' in str(pattern.pattern)]
    
    print(f"✓ Found {len(review_urls)} review-related URL patterns")
    for url in review_urls:
        print(f"  - {url.pattern}")

if __name__ == "__main__":
    print("=" * 50)
    print("REVIEWS FUNCTIONALITY TEST")
    print("=" * 50)
    
    try:
        create_test_data()
        test_review_functionality()
        check_api_endpoints()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        print("You can now visit http://127.0.0.1:8000/mb-admin/reviews/ to test the dashboard")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()