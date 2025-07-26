# Testing Guide

This guide will help you test all the features of the eCommerce platform.

## Prerequisites

1. Make sure the development server is running:
   ```bash
   python manage.py runserver
   ```

2. Ensure sample data is loaded:
   ```bash
   python manage.py populate_data
   ```

## Testing Workflow

### 1. Access the Admin Panel

Visit `http://127.0.0.1:8000/admin/` and login with your superuser account.

Explore the following sections:
- **Users**: View user accounts and profiles
- **Products**: Manage products, categories, variants
- **Cart**: View cart items and coupons
- **Orders**: Track orders and order history

### 2. Test the REST API

#### Using Django REST Framework Browsable API
Visit `http://127.0.0.1:8000/api/` to explore the API endpoints interactively.

#### Using curl or Postman

**Register a new user:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+1234567890"
  }'
```

**Login:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpass123"
  }'
```

Save the `access` token from the response for authenticated requests.

**Browse products:**
```bash
curl -X GET "http://127.0.0.1:8000/api/products/"
```

**Add product to cart:**
```bash
curl -X POST http://127.0.0.1:8000/api/cart/add/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

**View cart:**
```bash
curl -X GET http://127.0.0.1:8000/api/cart/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Test Using the Demo Account

You can also use the pre-created demo account:
- **Email**: demo@example.com
- **Password**: demo123456

### 4. Feature Testing Checklist

#### Authentication ✅
- [ ] User registration
- [ ] User login
- [ ] Token refresh
- [ ] Profile management
- [ ] Password change

#### Product Management ✅
- [ ] Browse products
- [ ] Search products
- [ ] Filter by category
- [ ] Filter by price range
- [ ] View product details
- [ ] View product variants
- [ ] Product reviews and ratings

#### Shopping Cart ✅
- [ ] Add products to cart
- [ ] Update item quantities
- [ ] Remove items from cart
- [ ] Apply coupon codes
- [ ] Save items for later
- [ ] Clear cart

#### Order Management ✅
- [ ] Create orders with COD payment
- [ ] View order history
- [ ] Track order status
- [ ] Cancel orders
- [ ] Download invoice PDF

#### Wishlist ✅
- [ ] Add products to wishlist
- [ ] View wishlist
- [ ] Remove from wishlist
- [ ] Move wishlist items to cart

#### Admin Features ✅
- [ ] Manage products
- [ ] Manage categories
- [ ] View orders
- [ ] Manage users
- [ ] Generate reports

## Test Scenarios

### Scenario 1: Complete Purchase Flow
1. Register a new user
2. Browse products and add items to cart
3. Apply a coupon code (try `WELCOME10`)
4. Create an order with shipping address
5. View order in order history
6. Check order status in admin panel

### Scenario 2: Product Management
1. Login to admin panel
2. Add a new product category
3. Create a new product with variants
4. Upload product images
5. Test product search and filtering

### Scenario 3: Cart Operations
1. Add multiple products to cart
2. Update quantities
3. Apply and remove coupons
4. Save items for later
5. Clear cart

### Scenario 4: Review System
1. Purchase a product (complete order)
2. Add a review for the product
3. Rate the product
4. View reviews on product page

## Testing with Different User Roles

### Customer Testing
- Register as a regular customer
- Test all shopping features
- Place orders and track status

### Admin Testing
- Login to admin panel
- Manage products and orders
- Generate reports
- Handle customer inquiries

## Performance Testing

### Load Testing
```bash
# Install Apache Bench (ab)
# Test API endpoints
ab -n 100 -c 10 http://127.0.0.1:8000/api/products/
```

### Database Performance
- Monitor query performance in Django Debug Toolbar
- Check database file size as data grows
- Test pagination with large datasets

## Security Testing

### Authentication Testing
- [ ] Test with invalid tokens
- [ ] Test token expiration
- [ ] Test unauthorized access to protected endpoints

### Input Validation
- [ ] Test with invalid email formats
- [ ] Test with SQL injection attempts
- [ ] Test with XSS payloads
- [ ] Test file upload limitations

## Troubleshooting

### Common Issues

**Migration Issues:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Static Files Not Loading:**
```bash
python manage.py collectstatic
```

**Token Authentication Errors:**
- Check token format in Authorization header
- Ensure token hasn't expired
- Verify user permissions

**Database Issues:**
- Delete `db.sqlite3` and re-run migrations
- Check database permissions
- Verify model relationships

### Debug Settings
Enable debug mode in `.env`:
```env
DEBUG=True
```

### Logging
Check logs in `ecommerce.log` for detailed error information.

## Test Data Reset

To start fresh with new test data:
```bash
# Clear existing data
python manage.py flush

# Load fresh sample data
python manage.py populate_data

# Create new superuser
python manage.py createsuperuser
```

## API Testing Tools

Recommended tools for API testing:
- **Postman**: GUI-based API testing
- **curl**: Command-line HTTP client  
- **HTTPie**: User-friendly command-line HTTP client
- **Django REST Framework Browsable API**: Built-in web interface

## Frontend Integration Testing

If you're building a frontend:
1. Test CORS settings
2. Verify API response formats
3. Test authentication flow
4. Handle API errors gracefully
5. Test pagination
6. Implement proper loading states

## Automated Testing

Run the Django test suite:
```bash
python manage.py test
```

Add custom tests in `tests.py` files in each app directory.

## Production Testing

Before deploying to production:
- [ ] Test with PostgreSQL database
- [ ] Verify environment variables
- [ ] Test static file serving
- [ ] Check security settings
- [ ] Test email functionality
- [ ] Verify SSL/HTTPS setup
- [ ] Test backup and restore procedures
