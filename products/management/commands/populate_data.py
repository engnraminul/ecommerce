from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage, ProductVariant
from cart.models import Coupon
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate the database with sample eCommerce data'
    
    def handle(self, *args, **options):
        self.stdout.write('Starting data population...')
        
        # Create categories
        self.create_categories()
        
        # Create products
        self.create_products()
        
        # Create coupons
        self.create_coupons()
        
        # Create sample user
        self.create_sample_user()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database with sample data!'))
    
    def create_categories(self):
        self.stdout.write('Creating categories...')
        
        categories = [
            {
                'name': 'Electronics',
                'description': 'Electronic devices and gadgets',
                'subcategories': [
                    {'name': 'Smartphones', 'description': 'Mobile phones and accessories'},
                    {'name': 'Laptops', 'description': 'Laptops and notebook computers'},
                    {'name': 'Audio', 'description': 'Headphones, speakers, and audio equipment'},
                ]
            },
            {
                'name': 'Clothing',
                'description': 'Fashion and apparel',
                'subcategories': [
                    {'name': 'Men\'s Clothing', 'description': 'Clothing for men'},
                    {'name': 'Women\'s Clothing', 'description': 'Clothing for women'},
                    {'name': 'Shoes', 'description': 'Footwear for all occasions'},
                ]
            },
            {
                'name': 'Home & Garden',
                'description': 'Home improvement and garden supplies',
                'subcategories': [
                    {'name': 'Furniture', 'description': 'Home and office furniture'},
                    {'name': 'Kitchen', 'description': 'Kitchen appliances and tools'},
                    {'name': 'Garden', 'description': 'Garden tools and supplies'},
                ]
            },
        ]
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Created category: {category.name}')
            
            # Create subcategories
            for subcat_data in cat_data.get('subcategories', []):
                subcategory, created = Category.objects.get_or_create(
                    name=subcat_data['name'],
                    defaults={
                        'description': subcat_data['description'],
                        'parent': category,
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'Created subcategory: {subcategory.name}')
    
    def create_products(self):
        self.stdout.write('Creating products...')
        
        products = [
            # Electronics - Smartphones
            {
                'name': 'iPhone 15 Pro',
                'description': 'Latest iPhone with advanced features and Pro camera system.',
                'short_description': 'Premium smartphone with Pro camera system',
                'category': 'Smartphones',
                'price': Decimal('999.99'),
                'compare_price': Decimal('1099.99'),
                'stock_quantity': 50,
                'is_featured': True,
                'variants': [
                    {'name': '128GB - Titanium', 'size': '128GB', 'color': 'Titanium', 'stock': 20},
                    {'name': '256GB - Titanium', 'size': '256GB', 'color': 'Titanium', 'price': Decimal('1099.99'), 'stock': 15},
                    {'name': '128GB - Blue', 'size': '128GB', 'color': 'Blue', 'stock': 15},
                ]
            },
            {
                'name': 'Samsung Galaxy S24',
                'description': 'Powerful Android smartphone with excellent camera and display.',
                'short_description': 'Premium Android smartphone',
                'category': 'Smartphones',
                'price': Decimal('799.99'),
                'stock_quantity': 40,
                'is_featured': True,
            },
            # Electronics - Laptops
            {
                'name': 'MacBook Pro 16"',
                'description': 'Professional laptop with M3 Pro chip and stunning display.',
                'short_description': 'Professional laptop with M3 Pro chip',
                'category': 'Laptops',
                'price': Decimal('2499.99'),
                'stock_quantity': 25,
                'is_featured': True,
                'weight': Decimal('2.16'),
            },
            {
                'name': 'Dell XPS 13',
                'description': 'Compact and powerful Windows laptop for professionals.',
                'short_description': 'Compact professional Windows laptop',
                'category': 'Laptops',
                'price': Decimal('1299.99'),
                'compare_price': Decimal('1499.99'),
                'stock_quantity': 30,
            },
            # Electronics - Audio
            {
                'name': 'AirPods Pro',
                'description': 'Wireless earbuds with active noise cancellation.',
                'short_description': 'Premium wireless earbuds',
                'category': 'Audio',
                'price': Decimal('249.99'),
                'stock_quantity': 100,
                'is_featured': True,
            },
            # Clothing - Men's
            {
                'name': 'Classic Cotton T-Shirt',
                'description': 'Comfortable 100% cotton t-shirt in various colors.',
                'short_description': '100% cotton comfortable t-shirt',
                'category': 'Men\'s Clothing',
                'price': Decimal('29.99'),
                'stock_quantity': 200,
                'variants': [
                    {'name': 'Small - Black', 'size': 'S', 'color': 'Black', 'stock': 50},
                    {'name': 'Medium - Black', 'size': 'M', 'color': 'Black', 'stock': 60},
                    {'name': 'Large - Black', 'size': 'L', 'color': 'Black', 'stock': 40},
                    {'name': 'Small - White', 'size': 'S', 'color': 'White', 'stock': 50},
                ]
            },
            # Home & Garden - Furniture
            {
                'name': 'Modern Office Chair',
                'description': 'Ergonomic office chair with lumbar support and adjustable height.',
                'short_description': 'Ergonomic office chair with lumbar support',
                'category': 'Furniture',
                'price': Decimal('299.99'),
                'compare_price': Decimal('399.99'),
                'stock_quantity': 15,
                'weight': Decimal('15.50'),
            },
        ]
        
        for product_data in products:
            try:
                category = Category.objects.get(name=product_data['category'])
                
                product, created = Product.objects.get_or_create(
                    name=product_data['name'],
                    defaults={
                        'description': product_data['description'],
                        'short_description': product_data['short_description'],
                        'category': category,
                        'price': product_data['price'],
                        'compare_price': product_data.get('compare_price'),
                        'stock_quantity': product_data['stock_quantity'],
                        'is_featured': product_data.get('is_featured', False),
                        'weight': product_data.get('weight'),
                        'is_active': True,
                    }
                )
                
                if created:
                    self.stdout.write(f'Created product: {product.name}')
                    
                    # Create variants if specified
                    for variant_data in product_data.get('variants', []):
                        ProductVariant.objects.create(
                            product=product,
                            name=variant_data['name'],
                            size=variant_data.get('size', ''),
                            color=variant_data.get('color', ''),
                            price=variant_data.get('price'),
                            stock_quantity=variant_data['stock'],
                            is_active=True
                        )
                        self.stdout.write(f'  Created variant: {variant_data["name"]}')
                
            except Category.DoesNotExist:
                self.stdout.write(f'Category {product_data["category"]} not found for product {product_data["name"]}')
    
    def create_coupons(self):
        self.stdout.write('Creating coupons...')
        
        coupons = [
            {
                'code': 'WELCOME10',
                'name': 'Welcome Discount',
                'description': '10% off for new customers',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'minimum_order_amount': Decimal('50.00'),
                'usage_limit': 100,
                'usage_limit_per_user': 1,
            },
            {
                'code': 'SAVE50',
                'name': 'Save $50',
                'description': '$50 off orders over $500',
                'discount_type': 'fixed_amount',
                'discount_value': Decimal('50.00'),
                'minimum_order_amount': Decimal('500.00'),
                'usage_limit': 50,
                'usage_limit_per_user': 1,
            },
            {
                'code': 'FREESHIP',
                'name': 'Free Shipping',
                'description': 'Free shipping on all orders',
                'discount_type': 'free_shipping',
                'discount_value': Decimal('0.00'),
                'minimum_order_amount': Decimal('75.00'),
                'usage_limit': 200,
                'usage_limit_per_user': 5,
            },
        ]
        
        for coupon_data in coupons:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults={
                    'name': coupon_data['name'],
                    'description': coupon_data['description'],
                    'discount_type': coupon_data['discount_type'],
                    'discount_value': coupon_data['discount_value'],
                    'minimum_order_amount': coupon_data['minimum_order_amount'],
                    'usage_limit': coupon_data['usage_limit'],
                    'usage_limit_per_user': coupon_data['usage_limit_per_user'],
                    'valid_from': timezone.now(),
                    'valid_until': timezone.now() + timedelta(days=365),
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(f'Created coupon: {coupon.code}')
    
    def create_sample_user(self):
        self.stdout.write('Creating sample user...')
        
        if not User.objects.filter(email='demo@example.com').exists():
            user = User.objects.create_user(
                username='demo',
                email='demo@example.com',
                password='demo123456',
                first_name='Demo',
                last_name='User',
                phone='+1234567890'
            )
            self.stdout.write(f'Created sample user: {user.username} (password: demo123456)')
        else:
            self.stdout.write('Sample user already exists')
