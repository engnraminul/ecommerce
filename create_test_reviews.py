#!/usr/bin/env python3
"""
Create additional test reviews to test pagination
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Review, Product
from users.models import User
import random

def create_test_reviews():
    """Create additional test reviews for pagination testing"""
    print("Creating additional test reviews for pagination testing...")
    
    # Get existing users and products
    users = list(User.objects.all())
    products = list(Product.objects.all())
    
    if not users:
        print("No users found. Creating a test user...")
        user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        users = [user]
    
    if not products:
        print("No products found. Cannot create reviews without products.")
        return
    
    # Sample review data
    review_titles = [
        "Great product!", "Love it!", "Amazing quality", "Highly recommended", 
        "Good value for money", "Fast shipping", "Excellent service", "Perfect fit",
        "Durable and reliable", "Exceeded expectations", "Poor quality", "Not satisfied",
        "Average product", "Could be better", "Disappointed", "Waste of money",
        "Fantastic!", "Will buy again", "Top quality", "Outstanding", "Superb",
        "Nice product", "Good purchase", "Decent quality", "Fair enough"
    ]
    
    review_comments = [
        "Really happy with this purchase. The quality is excellent and shipping was fast.",
        "This product exceeded my expectations. Would definitely buy again.",
        "Good value for the price. Works as advertised.",
        "The product quality is okay but could be improved.",
        "Not what I expected. The description didn't match the actual product.",
        "Excellent customer service and fast delivery. Highly recommend!",
        "The product is decent but nothing special. Average quality.",
        "Outstanding quality! This is exactly what I was looking for.",
        "Poor quality material. Started falling apart after a few days.",
        "Perfect! Exactly as described and arrived quickly.",
        "Great product with excellent build quality. Very satisfied.",
        "The product is good but overpriced for what you get.",
        "Amazing quality and finish. Will definitely order more.",
        "Not satisfied with this purchase. Quality is below expectations.",
        "Excellent product! Fast shipping and great packaging.",
        "Good product overall. Minor issues but nothing major.",
        "Love this! Great quality and exactly as described.",
        "Disappointed with the quality. Expected much better.",
        "Fantastic product! Highly recommend to everyone.",
        "Average quality product. Nothing to complain about.",
        "Excellent value for money. Very happy with purchase.",
        "Poor quality control. Product had defects upon arrival.",
        "Great product! Fast delivery and excellent packaging.",
        "Not worth the money. Quality is below average.",
        "Perfect product! Exactly what I needed."
    ]
    
    current_count = Review.objects.count()
    target_count = 30  # Create enough for pagination testing
    
    reviews_to_create = target_count - current_count
    
    if reviews_to_create <= 0:
        print(f"Already have {current_count} reviews. No need to create more.")
        return
    
    print(f"Creating {reviews_to_create} additional reviews...")
    
    for i in range(reviews_to_create):
        user = random.choice(users)
        product = random.choice(products)
        
        # Check if this user already reviewed this product
        existing_review = Review.objects.filter(user=user, product=product).first()
        if existing_review:
            continue  # Skip if user already reviewed this product
        
        title = random.choice(review_titles)
        comment = random.choice(review_comments)
        rating = random.randint(1, 5)
        is_approved = random.choice([True, False])
        is_verified = random.choice([True, False])
        
        Review.objects.create(
            user=user,
            product=product,
            rating=rating,
            title=title,
            comment=comment,
            is_approved=is_approved,
            is_verified_purchase=is_verified
        )
        
        print(f"Created review {i+1}/{reviews_to_create}: {title} - {rating}★")
    
    final_count = Review.objects.count()
    print(f"\nReview creation completed!")
    print(f"Total reviews now: {final_count}")
    print(f"Approved: {Review.objects.filter(is_approved=True).count()}")
    print(f"Pending: {Review.objects.filter(is_approved=False).count()}")

if __name__ == "__main__":
    print("=" * 50)
    print("CREATING TEST REVIEWS FOR PAGINATION")
    print("=" * 50)
    
    try:
        create_test_reviews()
        
        print("\n" + "=" * 50)
        print("✓ Test reviews created successfully!")
        print("Now visit http://127.0.0.1:8000/mb-admin/reviews/ to see pagination")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Failed to create test reviews: {e}")
        import traceback
        traceback.print_exc()