# Testing Guide for Professional eCommerce Platform

## Quick Start Testing

### 1. Access the Platform

**Frontend (Website):**
- Homepage: http://127.0.0.1:8000/
- Admin Panel: http://127.0.0.1:8000/admin/
- API Browser: http://127.0.0.1:8000/api/v1/

**Admin Login:**
- Email: aminul3065@gmail.com
- Password: aminul

### 2. Test User Authentication

#### Register New User
1. Go to http://127.0.0.1:8000/register/
2. Fill in the registration form
3. Submit and verify redirect to login page

#### Login Test
1. Go to http://127.0.0.1:8000/login/
2. Use your registered credentials
3. Verify successful login and redirect

#### API Authentication Test
```bash
# Get JWT Token
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'

# Expected Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Test Product Functionality

#### Browse Products
1. Visit homepage to see featured products
2. Go to Products page: http://127.0.0.1:8000/products/
3. Test filtering by category, price, rating
4. Test search functionality
5. Test product detail pages

#### API Product Tests
```bash
# List all products
curl http://127.0.0.1:8000/api/v1/products/

# Get specific product by slug
curl http://127.0.0.1:8000/api/v1/products/premium-laptop/

# Search products
curl "http://127.0.0.1:8000/api/v1/products/?search=laptop"

# Filter by category
curl "http://127.0.0.1:8000/api/v1/products/?category=electronics"

# Filter by price range
curl "http://127.0.0.1:8000/api/v1/products/?min_price=100&max_price=1000"
```

### 4. Test Shopping Cart

#### Frontend Cart Test
1. Add products to cart from product pages
2. View cart: http://127.0.0.1:8000/cart/
3. Update quantities
4. Remove items
5. Apply coupon codes (try: WELCOME10, FLAT20)

#### API Cart Tests
```bash
# Get user cart (requires authentication)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8000/api/v1/cart/

# Add item to cart
curl -X POST http://127.0.0.1:8000/api/v1/cart/add/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Apply coupon
curl -X POST http://127.0.0.1:8000/api/v1/cart/apply-coupon/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"coupon_code": "WELCOME10"}'
```

### 5. Test Order Management

#### Place Order via API
```bash
# Create order
curl -X POST http://127.0.0.1:8000/api/v1/orders/create/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "full_name": "John Doe",
      "phone": "+1234567890",
      "address_line_1": "123 Main St",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US"
    },
    "payment_method": "cod",
    "notes": "Test order"
  }'

# List user orders
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8000/api/v1/orders/

# Get order detail
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8000/api/v1/orders/1/
```

### 6. Test Admin Panel

#### Access Admin Dashboard
1. Go to http://127.0.0.1:8000/admin/
2. Login with admin credentials
3. Navigate through different sections

#### Test Admin Features
- **Users**: View/edit user accounts and profiles
- **Products**: Add/edit/delete products and categories
- **Orders**: View and manage customer orders
- **Cart**: View active shopping carts
- **Coupons**: Create/manage discount coupons

#### Admin Tasks to Test
1. Create a new product category
2. Add a new product with images
3. Create a discount coupon
4. Update order status
5. View customer details and orders

### 7. API Testing with Sample Data

#### Categories API
```bash
# List categories
curl http://127.0.0.1:8000/api/v1/products/categories/

# Expected: Electronics, Clothing, Books, Home & Garden, Sports categories
```

#### Products API with Sample Data
```bash
# Get Electronics products
curl "http://127.0.0.1:8000/api/v1/products/?category=electronics"

# Get products with pagination
curl "http://127.0.0.1:8000/api/v1/products/?page=1&page_size=5"

# Sort products by price
curl "http://127.0.0.1:8000/api/v1/products/?ordering=price"
```

### 8. Test Advanced Features

#### Wishlist Testing
```bash
# Add to wishlist
curl -X POST http://127.0.0.1:8000/api/v1/products/wishlist/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1}'

# Get wishlist
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8000/api/v1/products/wishlist/
```

#### Product Reviews Testing
```bash
# Add product review
curl -X POST http://127.0.0.1:8000/api/v1/products/1/reviews/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "title": "Great product!",
    "comment": "Really happy with this purchase."
  }'
```

### 9. Frontend Navigation Test

Test all frontend pages:
- http://127.0.0.1:8000/ (Homepage)
- http://127.0.0.1:8000/products/ (Products listing)
- http://127.0.0.1:8000/categories/ (Categories)
- http://127.0.0.1:8000/search/ (Search)
- http://127.0.0.1:8000/login/ (Login)
- http://127.0.0.1:8000/register/ (Registration)
- http://127.0.0.1:8000/cart/ (Shopping cart)
- http://127.0.0.1:8000/orders/ (User orders)
- http://127.0.0.1:8000/profile/ (User profile)
- http://127.0.0.1:8000/wishlist/ (Wishlist)

### 10. Mobile Responsiveness Test

Test the website on different screen sizes:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (480px - 767px)
- Small Mobile (< 480px)

Use browser developer tools to simulate different devices.

## Performance Testing

### Load Testing Sample Commands
```bash
# Test multiple concurrent requests
for i in {1..10}; do
  curl http://127.0.0.1:8000/api/v1/products/ &
done

# Test with different parameters
curl -w "@curl-format.txt" -o /dev/null -s http://127.0.0.1:8000/api/v1/products/
```

### Database Query Testing
Check Django Debug Toolbar (if enabled) for:
- Number of database queries per page
- Query execution time
- N+1 query problems

## Security Testing

### Test Authentication
```bash
# Test without token (should fail)
curl http://127.0.0.1:8000/api/v1/cart/

# Test with invalid token (should fail)
curl -H "Authorization: Bearer invalid_token" \
  http://127.0.0.1:8000/api/v1/cart/
```

### Test CSRF Protection
- Try submitting forms without CSRF tokens
- Test with invalid CSRF tokens

### Test Input Validation
- Try XSS attacks in form inputs
- Test SQL injection attempts
- Submit forms with invalid data

## Sample Test Scenarios

### Scenario 1: Complete Shopping Flow
1. Register new user
2. Browse products
3. Add items to cart
4. Apply discount coupon
5. Create order
6. Track order status
7. View order history

### Scenario 2: Admin Management Flow
1. Login as admin
2. Add new product category
3. Create new product
4. Upload product images
5. Create discount coupon
6. Process customer orders
7. Update inventory

### Scenario 3: API Integration Flow
1. Get JWT token
2. Fetch product catalog
3. Manage shopping cart
4. Place order
5. Track order status
6. Handle authentication refresh

## Expected Sample Data

After running `python manage.py load_sample_data`, you should have:

- **8 Products**: Premium Laptop, Wireless Headphones, Running Shoes, etc.
- **5 Main Categories**: Electronics, Clothing, Books, Home & Garden, Sports
- **5 Subcategories**: Laptops, Audio, Footwear, Fiction, Appliances
- **2 Active Coupons**: WELCOME10 (10% off), FLAT20 ($20 off $100+)

## Troubleshooting

### Common Issues

1. **Server not starting**: Check if port 8000 is available
2. **Database errors**: Run migrations with `python manage.py migrate`
3. **Static files not loading**: Run `python manage.py collectstatic`
4. **JWT token expired**: Get new token using refresh endpoint
5. **CORS errors**: Check CORS settings in settings.py

### Debug Commands
```bash
# Check database status
python manage.py dbshell

# Check installed packages
pip list

# Test email configuration (optional)
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

## API Documentation

For complete API documentation, visit:
http://127.0.0.1:8000/api/v1/

This provides an interactive interface to test all API endpoints.

---

**Happy Testing! 🚀**
