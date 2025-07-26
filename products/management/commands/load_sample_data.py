from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage
from cart.models import Coupon
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Load sample data for eCommerce platform'
    
    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')
        
        # Create categories
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
            {'name': 'Clothing', 'description': 'Fashion and apparel'},
            {'name': 'Home & Garden', 'description': 'Home improvement and garden items'},
            {'name': 'Sports & Outdoors', 'description': 'Sports equipment and outdoor gear'},
            {'name': 'Books', 'description': 'Books and educational materials'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create subcategories
        subcategories_data = [
            {'name': 'Smartphones', 'parent': 'Electronics', 'description': 'Mobile phones and accessories'},
            {'name': 'Laptops', 'parent': 'Electronics', 'description': 'Computers and laptops'},
            {'name': "Men's Fashion", 'parent': 'Clothing', 'description': 'Clothing for men'},
            {'name': "Women's Fashion", 'parent': 'Clothing', 'description': 'Clothing for women'},
            {'name': 'Kitchen', 'parent': 'Home & Garden', 'description': 'Kitchen appliances and tools'},
        ]
        
        for subcat_data in subcategories_data:
            parent_cat = categories[subcat_data.pop('parent')]
            subcategory, created = Category.objects.get_or_create(
                name=subcat_data['name'],
                parent=parent_cat,
                defaults=subcat_data
            )
            categories[subcat_data['name']] = subcategory
            if created:
                self.stdout.write(f'Created subcategory: {subcategory.name}')
        
        # Create products
        products_data = [
            {
                'name': 'iPhone 15 Pro',
                'category': 'Smartphones',
                'description': 'Latest iPhone with advanced features and powerful performance.',
                'short_description': 'Premium smartphone with cutting-edge technology.',
                'price': Decimal('999.99'),
                'compare_price': Decimal('1099.99'),
                'stock_quantity': 50,
                'is_featured': True,
            },
            {
                'name': 'Samsung Galaxy S24',
                'category': 'Smartphones',
                'description': 'High-end Android smartphone with excellent camera and display.',
                'short_description': 'Android flagship with amazing camera capabilities.',
                'price': Decimal('899.99'),
                'stock_quantity': 45,
                'is_featured': True,
            },
            {
                'name': 'MacBook Pro 16"',
                'category': 'Laptops',
                'description': 'Professional laptop for creative professionals and developers.',
                'short_description': 'Powerful laptop for professional use.',
                'price': Decimal('2399.99'),
                'compare_price': Decimal('2499.99'),
                'stock_quantity': 25,
                'is_featured': True,
            },
            {
                'name': 'Classic T-Shirt',
                'category': "Men's Fashion",
                'description': 'Comfortable cotton t-shirt perfect for everyday wear.',
                'short_description': 'Basic cotton t-shirt in various colors.',
                'price': Decimal('29.99'),
                'stock_quantity': 100,
            },
            {
                'name': 'Designer Jeans',
                'category': "Women's Fashion",
                'description': 'Stylish jeans with perfect fit and premium denim quality.',
                'short_description': 'Premium denim jeans with modern fit.',
                'price': Decimal('89.99'),
                'compare_price': Decimal('120.00'),
                'stock_quantity': 75,
            },
            {
                'name': 'Kitchen Mixer',
                'category': 'Kitchen',
                'description': 'Professional-grade kitchen mixer for all your baking needs.',
                'short_description': 'Powerful kitchen mixer for baking enthusiasts.',
                'price': Decimal('199.99'),
                'stock_quantity': 30,
            },
            {
                'name': 'Yoga Mat',
                'category': 'Sports & Outdoors',
                'description': 'High-quality yoga mat with excellent grip and cushioning.',
                'short_description': 'Premium yoga mat for comfortable practice.',
                'price': Decimal('39.99'),
                'stock_quantity': 60,
            },
            {
                'name': 'Programming Book',
                'category': 'Books',
                'description': 'Comprehensive guide to modern web development techniques.',
                'short_description': 'Learn modern web development from scratch.',
                'price': Decimal('49.99'),
                'stock_quantity': 40,
            },
        ]
        
        for product_data in products_data:
            category_name = product_data.pop('category')
            category = categories[category_name]
            
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                category=category,
                defaults=product_data
            )
            
            if created:
                self.stdout.write(f'Created product: {product.name}')
        
        # Create sample coupons
        coupons_data = [
            {
                'code': 'WELCOME10',
                'name': 'Welcome Discount',
                'description': '10% discount for new customers',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'minimum_order_amount': Decimal('50.00'),
                'usage_limit': 100,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=30),
            },
            {
                'code': 'FLAT20',
                'name': '$20 Off',
                'description': '$20 flat discount on orders over $100',
                'discount_type': 'fixed',
                'discount_value': Decimal('20.00'),
                'minimum_order_amount': Decimal('100.00'),
                'usage_limit': 50,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=15),
            },
        ]
        
        for coupon_data in coupons_data:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults=coupon_data
            )
            if created:
                self.stdout.write(f'Created coupon: {coupon.code}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded sample data!')
        )
