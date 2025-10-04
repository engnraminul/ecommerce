"""
Create sample products with variants to test intelligent stock management
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Product, ProductVariant, Category
from decimal import Decimal

def create_sample_products_with_variants():
    """Create sample products with variants for testing"""
    print("🏗️ Creating sample products with variants...")
    
    try:
        # Get or create category
        category, created = Category.objects.get_or_create(
            name="Test Electronics",
            defaults={
                'description': 'Test category for electronics'
            }
        )
        
        # Create a product with variants (T-Shirt)
        tshirt, created = Product.objects.get_or_create(
            name="Premium T-Shirt",
            defaults={
                'sku': 'TSH-001',
                'description': 'High quality cotton t-shirt with variants',
                'category': category,
                'price': Decimal('25.00'),
                'cost_price': Decimal('12.00'),
                'stock_quantity': 0,  # Will use variant stock
                'low_stock_threshold': 5,
                'track_inventory': True,
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created product: {tshirt.name}")
            
            # Create variants for T-Shirt
            variants_data = [
                {'name': 'Red - Small', 'size': 'S', 'color': 'Red', 'sku': 'TSH-001-R-S', 'stock': 15, 'cost': Decimal('12.00'), 'price': Decimal('25.00')},
                {'name': 'Red - Medium', 'size': 'M', 'color': 'Red', 'sku': 'TSH-001-R-M', 'stock': 8, 'cost': Decimal('12.00'), 'price': Decimal('25.00')},
                {'name': 'Red - Large', 'size': 'L', 'color': 'Red', 'sku': 'TSH-001-R-L', 'stock': 3, 'cost': Decimal('12.00'), 'price': Decimal('25.00')},
                {'name': 'Blue - Small', 'size': 'S', 'color': 'Blue', 'sku': 'TSH-001-B-S', 'stock': 12, 'cost': Decimal('12.50'), 'price': Decimal('26.00')},
                {'name': 'Blue - Medium', 'size': 'M', 'color': 'Blue', 'sku': 'TSH-001-B-M', 'stock': 0, 'cost': Decimal('12.50'), 'price': Decimal('26.00')},
                {'name': 'Blue - Large', 'size': 'L', 'color': 'Blue', 'sku': 'TSH-001-B-L', 'stock': 7, 'cost': Decimal('12.50'), 'price': Decimal('26.00')},
            ]
            
            for variant_data in variants_data:
                variant, created = ProductVariant.objects.get_or_create(
                    product=tshirt,
                    sku=variant_data['sku'],
                    defaults={
                        'name': variant_data['name'],
                        'size': variant_data['size'],
                        'color': variant_data['color'],
                        'stock_quantity': variant_data['stock'],
                        'cost_price': variant_data['cost'],
                        'price': variant_data['price'],
                        'is_active': True,
                        'in_stock': variant_data['stock'] > 0
                    }
                )
                if created:
                    print(f"  📌 Created variant: {variant.name} (Stock: {variant.stock_quantity}, Cost: ৳{variant.cost_price})")
        
        # Create a product without variants (Simple Book)
        book, created = Product.objects.get_or_create(
            name="Programming Guide Book",
            defaults={
                'sku': 'BOOK-001',
                'description': 'Comprehensive programming guide',
                'category': category,
                'price': Decimal('45.00'),
                'cost_price': Decimal('20.00'),
                'stock_quantity': 25,
                'low_stock_threshold': 10,
                'track_inventory': True,
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created product without variants: {book.name} (Stock: {book.stock_quantity}, Cost: ৳{book.cost_price})")
        
        # Create another product with variants (Smartphone)
        phone, created = Product.objects.get_or_create(
            name="Smart Phone Pro",
            defaults={
                'sku': 'PHONE-001',
                'description': 'Latest smartphone with multiple storage options',
                'category': category,
                'price': Decimal('599.00'),
                'cost_price': Decimal('350.00'),
                'stock_quantity': 0,  # Will use variant stock
                'low_stock_threshold': 3,
                'track_inventory': True,
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created product: {phone.name}")
            
            # Create variants for Smartphone
            phone_variants = [
                {'name': '128GB - Black', 'size': '128GB', 'color': 'Black', 'sku': 'PHONE-001-128-BK', 'stock': 5, 'cost': Decimal('350.00'), 'price': Decimal('599.00')},
                {'name': '256GB - Black', 'size': '256GB', 'color': 'Black', 'sku': 'PHONE-001-256-BK', 'stock': 2, 'cost': Decimal('400.00'), 'price': Decimal('699.00')},
                {'name': '128GB - White', 'size': '128GB', 'color': 'White', 'sku': 'PHONE-001-128-WH', 'stock': 0, 'cost': Decimal('350.00'), 'price': Decimal('599.00')},
                {'name': '256GB - White', 'size': '256GB', 'color': 'White', 'sku': 'PHONE-001-256-WH', 'stock': 1, 'cost': Decimal('400.00'), 'price': Decimal('699.00')},
            ]
            
            for variant_data in phone_variants:
                variant, created = ProductVariant.objects.get_or_create(
                    product=phone,
                    sku=variant_data['sku'],
                    defaults={
                        'name': variant_data['name'],
                        'size': variant_data['size'],
                        'color': variant_data['color'],
                        'stock_quantity': variant_data['stock'],
                        'cost_price': variant_data['cost'],
                        'price': variant_data['price'],
                        'is_active': True,
                        'in_stock': variant_data['stock'] > 0
                    }
                )
                if created:
                    print(f"  📌 Created variant: {variant.name} (Stock: {variant.stock_quantity}, Cost: ৳{variant.cost_price})")
        
        print("\n📊 Sample Data Summary:")
        print("=" * 50)
        
        # Show summary
        products_with_variants = Product.objects.filter(variants__isnull=False).distinct()
        products_without_variants = Product.objects.filter(variants__isnull=True, track_inventory=True)
        
        print(f"📦 Products with variants: {products_with_variants.count()}")
        for product in products_with_variants:
            variants = product.variants.filter(is_active=True)
            total_stock = sum(v.stock_quantity for v in variants)
            avg_cost = sum(v.effective_cost_price * v.stock_quantity for v in variants if v.effective_cost_price) / total_stock if total_stock > 0 else 0
            total_value = sum(v.stock_quantity * v.effective_cost_price for v in variants if v.effective_cost_price)
            print(f"  • {product.name}: {variants.count()} variants, {total_stock} total stock, ৳{avg_cost:.2f} avg cost, ৳{total_value:.2f} total value")
        
        print(f"\n📝 Products without variants: {products_without_variants.count()}")
        for product in products_without_variants:
            stock_value = product.stock_quantity * (product.cost_price or 0)
            print(f"  • {product.name}: {product.stock_quantity} stock, ৳{product.cost_price or 0} cost, ৳{stock_value:.2f} value")
        
        print("\n🎯 Test Scenarios Created:")
        print("  ✅ Products with variants (cost varies by variant)")
        print("  ✅ Products without variants (simple cost price)")
        print("  ✅ Low stock situations")
        print("  ✅ Out of stock variants")
        print("  ✅ Mixed stock levels for testing")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Creating intelligent stock management test data...")
    create_sample_products_with_variants()
    print("\n🎉 Sample data creation completed!")
    print("\n💡 Now you can test:")
    print("   1. Visit http://127.0.0.1:8000/mb-admin/stock/")
    print("   2. See intelligent stock management in action")
    print("   3. Test variant vs product stock adjustments")
    print("   4. View cost price-based stock valuations")