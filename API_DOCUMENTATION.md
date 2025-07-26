# API Documentation

## Base URL
```
http://localhost:8000/api/v1/
```

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Get Token
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Refresh Token
```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Users API

### User Registration
```http
POST /api/v1/users/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
}
```

**Response:**
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "is_email_verified": false,
    "date_joined": "2023-12-07T10:00:00Z"
}
```

### User Login
```http
POST /api/v1/users/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123"
}
```

### Get User Profile
```http
GET /api/v1/users/profile/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890"
    },
    "date_of_birth": "1990-01-01",
    "gender": "M",
    "bio": "Software developer",
    "avatar": null,
    "preferred_language": "en",
    "preferred_currency": "USD",
    "newsletter_subscription": true
}
```

### Update User Profile
```http
PUT /api/v1/users/profile/
Authorization: Bearer <token>
Content-Type: application/json

{
    "user": {
        "first_name": "John",
        "last_name": "Smith",
        "phone": "+1234567890"
    },
    "bio": "Updated bio",
    "preferred_currency": "EUR"
}
```

### User Addresses
```http
GET /api/v1/users/addresses/
Authorization: Bearer <token>
```

### Add Address
```http
POST /api/v1/users/addresses/
Authorization: Bearer <token>
Content-Type: application/json

{
    "full_name": "John Doe",
    "phone": "+1234567890",
    "address_line_1": "123 Main St",
    "address_line_2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US",
    "is_default": true
}
```

## Products API

### List Products
```http
GET /api/v1/products/
```

**Query Parameters:**
- `category` - Filter by category slug
- `min_price` - Minimum price filter
- `max_price` - Maximum price filter
- `is_available` - Filter by availability (true/false)
- `min_rating` - Minimum rating filter
- `ordering` - Order by: price, -price, rating, -rating, created_at, -created_at
- `search` - Search in name and description
- `page` - Page number for pagination

**Response:**
```json
{
    "count": 8,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Premium Laptop",
            "slug": "premium-laptop",
            "description": "High-performance laptop for professionals",
            "price": "999.99",
            "discounted_price": "899.99",
            "is_available": true,
            "stock_quantity": 50,
            "category": {
                "id": 1,
                "name": "Electronics",
                "slug": "electronics"
            },
            "average_rating": "4.50",
            "review_count": 10,
            "images": [
                {
                    "id": 1,
                    "image": "/media/products/laptop1.jpg",
                    "alt_text": "Premium Laptop",
                    "is_primary": true
                }
            ],
            "created_at": "2023-12-07T10:00:00Z"
        }
    ]
}
```

### Product Detail
```http
GET /api/v1/products/<slug>/
```

**Response:**
```json
{
    "id": 1,
    "name": "Premium Laptop",
    "slug": "premium-laptop",
    "description": "High-performance laptop for professionals",
    "price": "999.99",
    "discounted_price": "899.99",
    "is_available": true,
    "stock_quantity": 50,
    "category": {
        "id": 1,
        "name": "Electronics",
        "slug": "electronics",
        "parent": null
    },
    "variants": [
        {
            "id": 1,
            "variant_type": "color",
            "variant_value": "Silver",
            "price_adjustment": "0.00",
            "stock_quantity": 25,
            "is_available": true
        }
    ],
    "images": [
        {
            "id": 1,
            "image": "/media/products/laptop1.jpg",
            "alt_text": "Premium Laptop",
            "is_primary": true
        }
    ],
    "reviews": [
        {
            "id": 1,
            "user": {
                "first_name": "Jane",
                "last_name": "D."
            },
            "rating": 5,
            "title": "Excellent laptop!",
            "comment": "Great performance and battery life.",
            "is_verified_purchase": true,
            "created_at": "2023-12-06T15:30:00Z"
        }
    ],
    "average_rating": "4.50",
    "review_count": 10,
    "created_at": "2023-12-07T10:00:00Z"
}
```

### Product Categories
```http
GET /api/v1/products/categories/
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "Electronics",
        "slug": "electronics",
        "description": "Electronic devices and gadgets",
        "parent": null,
        "image": "/media/categories/electronics.jpg",
        "is_active": true,
        "children": [
            {
                "id": 6,
                "name": "Laptops",
                "slug": "laptops",
                "parent": 1
            }
        ]
    }
]
```

### Search Products
```http
GET /api/v1/products/search/?q=laptop
```

### Featured Products
```http
GET /api/v1/products/featured/
```

## Cart API

### Get Cart
```http
GET /api/v1/cart/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "id": 1,
    "items": [
        {
            "id": 1,
            "product": {
                "id": 1,
                "name": "Premium Laptop",
                "slug": "premium-laptop",
                "price": "999.99",
                "discounted_price": "899.99",
                "images": [
                    {
                        "image": "/media/products/laptop1.jpg",
                        "alt_text": "Premium Laptop"
                    }
                ]
            },
            "variant": {
                "id": 1,
                "variant_type": "color",
                "variant_value": "Silver"
            },
            "quantity": 2,
            "unit_price": "899.99",
            "total_price": "1799.98",
            "added_at": "2023-12-07T10:00:00Z"
        }
    ],
    "subtotal": "1799.98",
    "discount_amount": "179.99",
    "total": "1619.99",
    "applied_coupon": {
        "code": "WELCOME10",
        "discount_type": "percentage",
        "discount_value": "10.00"
    },
    "created_at": "2023-12-07T09:00:00Z",
    "updated_at": "2023-12-07T10:30:00Z"
}
```

### Add to Cart
```http
POST /api/v1/cart/add/
Authorization: Bearer <token>
Content-Type: application/json

{
    "product_id": 1,
    "variant_id": 1,
    "quantity": 2
}
```

### Update Cart Item
```http
PUT /api/v1/cart/items/<item_id>/update/
Authorization: Bearer <token>
Content-Type: application/json

{
    "quantity": 3
}
```

### Remove from Cart
```http
DELETE /api/v1/cart/items/<item_id>/remove/
Authorization: Bearer <token>
```

### Apply Coupon
```http
POST /api/v1/cart/apply-coupon/
Authorization: Bearer <token>
Content-Type: application/json

{
    "coupon_code": "WELCOME10"
}
```

### Remove Coupon
```http
DELETE /api/v1/cart/remove-coupon/
Authorization: Bearer <token>
```

## Orders API

### List Orders
```http
GET /api/v1/orders/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "order_number": "ORD-2023-001",
            "status": "delivered",
            "total_amount": "1619.99",
            "payment_method": "cod",
            "payment_status": "pending",
            "shipping_address": {
                "full_name": "John Doe",
                "phone": "+1234567890",
                "address_line_1": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US"
            },
            "created_at": "2023-12-07T10:00:00Z",
            "estimated_delivery": "2023-12-14T00:00:00Z"
        }
    ]
}
```

### Create Order
```http
POST /api/v1/orders/create/
Authorization: Bearer <token>
Content-Type: application/json

{
    "shipping_address": {
        "full_name": "John Doe",
        "phone": "+1234567890",
        "address_line_1": "123 Main St",
        "address_line_2": "Apt 4B",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US"
    },
    "payment_method": "cod",
    "notes": "Please call before delivery"
}
```

### Order Detail
```http
GET /api/v1/orders/<order_id>/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "id": 1,
    "order_number": "ORD-2023-001",
    "status": "confirmed",
    "items": [
        {
            "id": 1,
            "product": {
                "id": 1,
                "name": "Premium Laptop",
                "slug": "premium-laptop",
                "images": [
                    {
                        "image": "/media/products/laptop1.jpg",
                        "alt_text": "Premium Laptop"
                    }
                ]
            },
            "variant": {
                "variant_type": "color",
                "variant_value": "Silver"
            },
            "quantity": 2,
            "unit_price": "899.99",
            "total_price": "1799.98"
        }
    ],
    "subtotal": "1799.98",
    "discount_amount": "179.99",
    "shipping_cost": "0.00",
    "total_amount": "1619.99",
    "payment_method": "cod",
    "payment_status": "pending",
    "shipping_address": {
        "full_name": "John Doe",
        "phone": "+1234567890",
        "address_line_1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US"
    },
    "tracking_number": "TRK123456789",
    "notes": "Please call before delivery",
    "created_at": "2023-12-07T10:00:00Z",
    "estimated_delivery": "2023-12-14T00:00:00Z"
}
```

### Cancel Order
```http
POST /api/v1/orders/<order_id>/cancel/
Authorization: Bearer <token>
Content-Type: application/json

{
    "reason": "Changed my mind"
}
```

### Track Order
```http
GET /api/v1/orders/<order_number>/track/
```

**Response:**
```json
{
    "order_number": "ORD-2023-001",
    "status": "shipped",
    "tracking_number": "TRK123456789",
    "estimated_delivery": "2023-12-14T00:00:00Z",
    "tracking_history": [
        {
            "status": "pending",
            "message": "Order placed successfully",
            "timestamp": "2023-12-07T10:00:00Z"
        },
        {
            "status": "confirmed",
            "message": "Order confirmed by merchant",
            "timestamp": "2023-12-07T11:00:00Z"
        },
        {
            "status": "shipped",
            "message": "Order shipped via courier",
            "timestamp": "2023-12-08T09:00:00Z"
        }
    ]
}
```

### Reorder
```http
POST /api/v1/orders/<order_id>/reorder/
Authorization: Bearer <token>
```

## Wishlist API

### Get Wishlist
```http
GET /api/v1/products/wishlist/
Authorization: Bearer <token>
```

### Add to Wishlist
```http
POST /api/v1/products/wishlist/
Authorization: Bearer <token>
Content-Type: application/json

{
    "product_id": 1
}
```

### Remove from Wishlist
```http
DELETE /api/v1/products/wishlist/<item_id>/
Authorization: Bearer <token>
```

## Reviews API

### Add Product Review
```http
POST /api/v1/products/<product_id>/reviews/
Authorization: Bearer <token>
Content-Type: application/json

{
    "rating": 5,
    "title": "Excellent product!",
    "comment": "Great quality and fast delivery."
}
```

### Update Review
```http
PUT /api/v1/products/reviews/<review_id>/
Authorization: Bearer <token>
Content-Type: application/json

{
    "rating": 4,
    "title": "Good product",
    "comment": "Updated review comment."
}
```

### Delete Review
```http
DELETE /api/v1/products/reviews/<review_id>/
Authorization: Bearer <token>
```

## Error Responses

All API endpoints return consistent error responses:

### 400 Bad Request
```json
{
    "error": "Bad Request",
    "message": "Invalid data provided",
    "details": {
        "email": ["This field is required."],
        "password": ["This field is required."]
    }
}
```

### 401 Unauthorized
```json
{
    "error": "Unauthorized",
    "message": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "error": "Forbidden",
    "message": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "error": "Not Found",
    "message": "The requested resource was not found."
}
```

### 429 Too Many Requests
```json
{
    "error": "Too Many Requests",
    "message": "Request was throttled. Expected available in 60 seconds."
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal Server Error",
    "message": "An error occurred processing your request."
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Admin users**: Unlimited

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1671267600
```

## Pagination

List endpoints support pagination with the following parameters:

- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

**Response format:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/v1/products/?page=3",
    "previous": "http://localhost:8000/api/v1/products/?page=1",
    "results": [...]
}
```

## File Upload

For endpoints that accept file uploads (like product images or user avatars), use `multipart/form-data` content type:

```http
POST /api/v1/users/avatar/
Authorization: Bearer <token>
Content-Type: multipart/form-data

avatar: <file>
```

## Webhook Support

The API supports webhooks for real-time notifications:

- Order status changes
- Payment confirmations
- Stock level alerts
- New user registrations

Configure webhook endpoints in the admin panel or via API settings.

---

For more detailed examples and interactive API testing, visit the Django REST Framework browsable API at: http://localhost:8000/api/v1/
