#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')

# Setup Django
django.setup()

from products.models import Product, ProductVariant
from decimal import Decimal

def recreate_tshirt_variants():
    """Recreate T-shirt variants with proper hex colors and names"""
    
    try:
        tshirt = Product.objects.get(slug='classic-t-shirt')
        print(f"Found product: {tshirt.name}")
        
        # Delete existing variants to avoid duplicates
        existing_variants = ProductVariant.objects.filter(product=tshirt)
        if existing_variants.exists():
            print(f"Deleting {existing_variants.count()} existing T-shirt variants...")
            existing_variants.delete()
        
        # T-shirt variant configurations
        variants_config = [
            {'name': 'Red Classic T-Shirt - Small', 'color': '#dc3545', 'size': 'S', 'stock': 15, 'price': None},
            {'name': 'Red Classic T-Shirt - Medium', 'color': '#dc3545', 'size': 'M', 'stock': 20, 'price': None},
            {'name': 'Red Classic T-Shirt - Large', 'color': '#dc3545', 'size': 'L', 'stock': 18, 'price': None},
            
            {'name': 'Blue Classic T-Shirt - Small', 'color': '#007bff', 'size': 'S', 'stock': 12, 'price': None},
            {'name': 'Blue Classic T-Shirt - Medium', 'color': '#007bff', 'size': 'M', 'stock': 25, 'price': None},
            {'name': 'Blue Classic T-Shirt - Large', 'color': '#007bff', 'size': 'L', 'stock': 22, 'price': None},
            
            {'name': 'Black Classic T-Shirt - Small', 'color': '#343a40', 'size': 'S', 'stock': 18, 'price': None},
            {'name': 'Black Classic T-Shirt - Medium', 'color': '#343a40', 'size': 'M', 'stock': 30, 'price': None},
            {'name': 'Black Classic T-Shirt - Large', 'color': '#343a40', 'size': 'L', 'stock': 28, 'price': None},
        ]
        
        print("Creating T-shirt variants with hex colors...")
        for config in variants_config:
            variant = ProductVariant.objects.create(
                product=tshirt,
                name=config['name'],
                color=config['color'],
                size=config['size'],
                stock_quantity=config['stock'],
                price=config['price'],  # Will use product price
                material="Cotton",
                is_active=True
            )
            print(f"Created: {variant.name} (Color: {variant.color}, Size: {variant.size}, Stock: {variant.stock_quantity})")
        
        print(f"\nSuccessfully created {len(variants_config)} T-shirt variants!")
        
    except Product.DoesNotExist:
        print("Classic T-Shirt product not found!")
        return

def clean_duplicate_variants():
    """Clean up any duplicate variants"""
    
    # Remove duplicate office chair variants
    office_chair = Product.objects.get(slug='modern-office-chair')
    
    # Get unique color variants for office chair
    blue_variants = ProductVariant.objects.filter(product=office_chair, color='#007bff')
    if blue_variants.count() > 1:
        print(f"Found {blue_variants.count()} blue office chair variants, keeping only one...")
        # Keep the first one, delete the rest
        for variant in blue_variants[1:]:
            print(f"Deleting duplicate: {variant.name}")
            variant.delete()

if __name__ == "__main__":
    clean_duplicate_variants()
    recreate_tshirt_variants()
    
    # Show final summary
    print("\nFinal variant summary:")
    for product in Product.objects.filter(variants__isnull=False).distinct():
        print(f"\n{product.name} ({product.variants.count()} variants):")
        for variant in product.variants.all():
            print(f"  - {variant.name} (Color: {variant.color}, Stock: {variant.stock_quantity})")
