#!/usr/bin/env python3
"""
Simple test script to check existing reviews and functionality
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Review, ReviewImage
from django.db.models import Q

def check_existing_reviews():
    """Check existing review data"""
    print("Checking existing review data...")
    
    total_reviews = Review.objects.count()
    print(f"✓ Total reviews in database: {total_reviews}")
    
    if total_reviews > 0:
        approved_reviews = Review.objects.filter(is_approved=True).count()
        pending_reviews = Review.objects.filter(is_approved=False).count()
        verified_reviews = Review.objects.filter(is_verified_purchase=True).count()
        reviews_with_images = Review.objects.filter(images__isnull=False).distinct().count()
        
        print(f"✓ Approved reviews: {approved_reviews}")
        print(f"✓ Pending reviews: {pending_reviews}")
        print(f"✓ Verified purchases: {verified_reviews}")
        print(f"✓ Reviews with images: {reviews_with_images}")
        
        # Show sample reviews
        print("\nSample reviews:")
        for review in Review.objects.select_related('product', 'user')[:3]:
            reviewer = review.user.username if review.user else review.guest_name
            print(f"  - {reviewer}: {review.rating}★ for '{review.product.name}' - {review.title}")
    
    else:
        print("No reviews found in database.")

def test_api_views():
    """Test that API views are properly imported"""
    print("\nTesting API view imports...")
    
    try:
        from dashboard.views import reviews_dashboard, review_bulk_action, review_single_action, review_edit
        print("✓ All review management views imported successfully")
        print(f"  - reviews_dashboard: {reviews_dashboard.__name__}")
        print(f"  - review_bulk_action: {review_bulk_action.__name__}")
        print(f"  - review_single_action: {review_single_action.__name__}")
        print(f"  - review_edit: {review_edit.__name__}")
    except ImportError as e:
        print(f"✗ Error importing review views: {e}")

def check_url_patterns():
    """Check URL patterns"""
    print("\nChecking URL patterns...")
    
    try:
        from dashboard.urls import urlpatterns
        
        review_patterns = []
        for pattern in urlpatterns:
            pattern_str = str(pattern.pattern)
            if 'review' in pattern_str:
                review_patterns.append(pattern_str)
        
        print(f"✓ Found {len(review_patterns)} review URL patterns:")
        for pattern in review_patterns:
            print(f"  - {pattern}")
            
    except Exception as e:
        print(f"✗ Error checking URLs: {e}")

def check_templates():
    """Check if templates exist"""
    print("\nChecking templates...")
    
    import os
    dashboard_template_path = r"c:\Users\aminu\OneDrive\Desktop\ecommerce\dashboard\templates\dashboard"
    reviews_template = os.path.join(dashboard_template_path, "reviews.html")
    
    if os.path.exists(reviews_template):
        print("✓ Reviews template exists")
        with open(reviews_template, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for key elements
        if 'editReview(' in content:
            print("✓ Edit functionality found in template")
        if 'singleAction(' in content:
            print("✓ Action buttons found in template") 
        if 'getCSRFToken()' in content:
            print("✓ CSRF token handling found in template")
        if 'editReviewModal' in content:
            print("✓ Edit modal found in template")
            
    else:
        print("✗ Reviews template not found")

if __name__ == "__main__":
    print("=" * 50)
    print("REVIEWS FUNCTIONALITY CHECK")
    print("=" * 50)
    
    try:
        check_existing_reviews()
        test_api_views()
        check_url_patterns()
        check_templates()
        
        print("\n" + "=" * 50)
        print("✓ All checks completed!")
        print("\nREADY TO TEST:")
        print("1. Visit http://127.0.0.1:8000/mb-admin/reviews/")
        print("2. Test action buttons (approve, disapprove, delete, edit)")
        print("3. Test bulk actions")
        print("4. Test search and filtering")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Check failed with error: {e}")
        import traceback
        traceback.print_exc()