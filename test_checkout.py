import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from cart.models import Cart, CartItem
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

print('🛒 Testing checkout abandonment tracking...')
print()

# Get or create a user
user = User.objects.first()
if not user:
    user = User.objects.create_user(username='testuser', email='test@example.com')
    print('✅ Created test user')

# Get or create cart
cart, created = Cart.objects.get_or_create(user=user)
if created:
    print('✅ Created new cart')
else:
    print('✅ Using existing cart')

# Check if cart has items
if not cart.items.exists():
    # Add a test item to cart
    product = Product.objects.first()
    if product:
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            unit_price=product.price
        )
        print(f'✅ Added {product.name} to cart')
    else:
        print('❌ No products available. Please create a product first.')
else:
    print(f'✅ Cart has {cart.items.count()} items')

print(f'   Cart total: ${cart.subtotal}')
print()
print('🎯 Ready to test checkout abandonment!')
print('📝 Instructions:')
print('   1. Go to http://127.0.0.1:8000/checkout/')
print('   2. Fill out the form (name, email, address)')
print('   3. Navigate away or close the tab')
print('   4. Check incomplete orders in admin')
print()