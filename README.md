# Professional eCommerce Platform

A comprehensive eCommerce platform built with Django and Django REST Framework, featuring a complete backend API and optional frontend templates.

## 🚀 Features

### ✅ Core Features
- **User Authentication**
  - Register/Login/Logout with JWT authentication
  - User profile management
  - Multiple shipping addresses support
  - Password change functionality

- **Product Management**
  - Categories & subcategories with hierarchy support
  - Product listings with images, descriptions, stock, prices
  - Product variants (size, color, material)
  - Advanced search and filtering (category, price, availability, rating)
  - Product reviews and ratings
  - Wishlist functionality

- **Shopping Cart**
  - Add/remove products to cart
  - Update quantities
  - Save items for later
  - Coupon/discount code system
  - Cart persistence across sessions

- **Order Management**
  - Complete checkout process
  - Cash on Delivery (COD) payment method
  - Order confirmation & status tracking
  - Multiple order statuses (Pending, Confirmed, Shipped, Delivered)
  - Order history and details
  - Order cancellation (before shipping)
  - Reorder functionality

- **Admin Panel**
  - Comprehensive Django admin interface
  - Manage users, products, orders, coupons
  - Order status management
  - Inventory tracking
  - Sales analytics

### ✨ Advanced Features
- **Product Reviews & Ratings**
  - Verified purchase reviews
  - Rating system (1-5 stars)
  - Review approval system

- **Discount System**
  - Percentage and fixed amount coupons
  - Usage limits and expiration dates
  - Minimum order requirements

- **Wishlist**
  - Save products for later purchase
  - Easy wishlist management

- **API Features**
  - RESTful API with pagination
  - JWT token authentication
  - Comprehensive filtering and searching
  - CORS support for frontend frameworks

## 🛠 Technology Stack

- **Backend**: Django 4.2.7, Django REST Framework 3.14.0
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: JWT (Simple JWT)
- **API Documentation**: Django REST Framework browsable API
- **File Storage**: Local filesystem (configurable for cloud storage)
- **Caching**: Redis support
- **Task Queue**: Celery (for email notifications)

## 📋 Requirements

- Python 3.8+
- Django 4.2.7
- PostgreSQL (optional, for production)
- Redis (optional, for caching and background tasks)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
cd ecommerce
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment file
cp .env.example .env

# Edit .env file with your settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py load_sample_data
```

### 4. Run Development Server

```bash
python manage.py runserver
```

The application will be available at:
- **API**: http://127.0.0.1:8000/api/v1/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Frontend**: http://127.0.0.1:8000/ (if using Django templates)

## 📚 API Documentation

### Authentication Endpoints

```
POST /api/v1/users/register/          # User registration
POST /api/v1/users/login/             # User login
POST /api/v1/users/logout/            # User logout
POST /api/v1/auth/token/              # Get JWT token
POST /api/v1/auth/token/refresh/      # Refresh JWT token
```

### Product Endpoints

```
GET    /api/v1/products/              # List products
GET    /api/v1/products/<slug>/       # Product detail
GET    /api/v1/products/search/       # Search products
GET    /api/v1/products/featured/     # Featured products
GET    /api/v1/products/categories/   # List categories
POST   /api/v1/products/wishlist/     # Add to wishlist
```

### Cart Endpoints

```
GET    /api/v1/cart/                  # Get cart
POST   /api/v1/cart/add/              # Add to cart
PUT    /api/v1/cart/items/<id>/update/ # Update cart item
DELETE /api/v1/cart/items/<id>/remove/ # Remove from cart
POST   /api/v1/cart/apply-coupon/     # Apply coupon
```

### Order Endpoints

```
GET    /api/v1/orders/                # List orders
POST   /api/v1/orders/create/         # Create order
GET    /api/v1/orders/<id>/           # Order detail
POST   /api/v1/orders/<id>/cancel/    # Cancel order
GET    /api/v1/orders/<number>/track/ # Track order
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DB_NAME` | Database name | `ecommerce_db` |
| `DB_USER` | Database user | - |
| `DB_PASSWORD` | Database password | - |
| `EMAIL_HOST` | SMTP host | - |
| `EMAIL_PORT` | SMTP port | `587` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379` |

### Database Configuration

**SQLite (Development):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**PostgreSQL (Production):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ecommerce_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🎨 Frontend Options

### Option 1: Django Templates
- Server-side rendered HTML templates
- Bootstrap/Tailwind CSS for styling
- HTMX for dynamic interactions

### Option 2: React/Vue.js SPA
- Modern JavaScript framework
- Consumes REST API
- Complete separation of concerns

### Option 3: Mobile App
- React Native or Flutter
- Uses the same REST API
- Cross-platform mobile solution

## 📱 Sample Frontend Implementation

The project includes basic Django templates for:
- Product catalog
- User authentication
- Shopping cart
- Order management
- User profile

## 🔒 Security Features

- JWT-based authentication
- CSRF protection
- SQL injection prevention
- XSS protection
- Rate limiting (configurable)
- CORS configuration
- Secure password validation

## 📊 Admin Features

### Product Management
- Bulk product import/export
- Inventory tracking
- Product variant management
- Category hierarchy management

### Order Management
- Order status updates
- Bulk order processing
- Order analytics
- Customer communication

### User Management
- User accounts overview
- Order history per user
- User analytics

## 🚀 Deployment

### Production Checklist

1. **Environment**
   - Set `DEBUG=False`
   - Configure proper database (PostgreSQL)
   - Set up Redis for caching
   - Configure email backend

2. **Static Files**
   - Run `python manage.py collectstatic`
   - Configure web server (Nginx/Apache)

3. **Security**
   - Set strong `SECRET_KEY`
   - Configure HTTPS
   - Set proper `ALLOWED_HOSTS`

4. **Performance**
   - Enable Redis caching
   - Configure database connection pooling
   - Set up CDN for static files

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ecommerce_project.wsgi:application"]
```

## 📈 Performance Optimization

- Database query optimization with select_related/prefetch_related
- API pagination for large datasets
- Image optimization and CDN integration
- Redis caching for frequently accessed data
- Database indexing for search optimization

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API endpoints in Django REST Framework browser

## 🎯 Roadmap

- [ ] Payment gateway integration (Stripe, PayPal)
- [ ] Email notifications system
- [ ] Advanced analytics dashboard
- [ ] Multi-vendor support
- [ ] Mobile app (React Native)
- [ ] Elasticsearch integration
- [ ] Social authentication
- [ ] Product recommendations
- [ ] Multi-language support

---

**Built with ❤️ using Django and Django REST Framework**
