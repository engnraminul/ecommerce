# Dashboard Permissions Implementation - Complete Guide

## Overview
This implementation adds a comprehensive dashboard permission system to the eCommerce application, allowing granular control over which dashboard tabs users can access.

## Features Implemented

### 1. Database Models
- **DashboardPermission Model**: Stores user-specific dashboard tab permissions
- **Fields**:
  - `user`: OneToOneField to User model
  - `allowed_tabs`: JSONField storing list of allowed dashboard tab codes
  - `created_at` / `updated_at`: Timestamp fields

### 2. Available Dashboard Tabs (17 total)
1. `home` - Dashboard Home
2. `products` - Products Management
3. `categories` - Categories Management
4. `media` - Media Library
5. `stock` - Stock Management
6. `orders` - Orders Management
7. `incomplete_orders` - Incomplete Orders
8. `reviews` - Reviews Management
9. `contacts` - Contacts Management
10. `pages` - Pages Management
11. `blocklist` - Block List Management
12. `users` - Users Management
13. `expenses` - Expenses Management
14. `statistics` - Statistics & Analytics
15. `email_settings` - Email Settings
16. `settings` - System Settings
17. `api_docs` - API Documentation

### 3. Permission Logic
- **Superusers**: Always have full access to all dashboard tabs
- **Staff Users**: Always have full access to all dashboard tabs
- **Regular Users**: Access controlled by DashboardPermission model
- **No Permissions Set**: Users with no permissions have no dashboard access

### 4. Admin Interface Enhancements

#### User Admin
- Added dashboard permissions inline form
- Dashboard access summary column in user list
- Checkbox interface for selecting allowed tabs
- Visual indicators for permission levels

#### DashboardPermission Admin
- Separate admin interface for advanced permission management
- Bulk operations support
- Permission statistics and summaries

### 5. API Enhancements

#### UserDashboardViewSet
- Added `dashboard_tabs` endpoint to get available tabs
- Enhanced user serialization with permission data
- Support for creating/updating users with permissions

#### API Endpoints
- `GET /mb-admin/api/users/dashboard_tabs/` - Get available dashboard tabs
- Standard CRUD operations include permission handling

### 6. Frontend Implementation

#### Users Management Interface
- Dashboard permissions section in add/edit user modals
- Checkbox grid for tab selection
- "Select All" / "Deselect All" functionality
- Real-time permission summary display

#### Navigation Control
- Template tags for permission checking
- Dynamic navigation menu based on user permissions
- Clean, maintainable template structure

### 7. Security Implementation

#### Middleware
- `DashboardPermissionMiddleware`: Enforces permissions on dashboard URLs
- Checks both frontend views and API endpoints
- Automatic redirection for unauthorized access
- JSON error responses for API calls

#### Template Tags
- `has_dashboard_access` filter for permission checking
- `dashboard_access_summary` tag for status display
- `dashboard_nav_item` inclusion tag for navigation items

### 8. Management Commands

#### `setup_dashboard_permissions`
```bash
python manage.py setup_dashboard_permissions --all-tabs --basic-tabs
```
- Sets up permissions for existing users
- `--all-tabs`: Give staff users access to all tabs
- `--basic-tabs`: Give regular users access to basic tabs

#### `promote_user`
```bash
python manage.py promote_user --email user@example.com --create
```
- Promotes users to staff/superuser status
- Creates users if they don't exist
- Sets up full dashboard permissions

### 9. Database Schema

#### Migration: `users/0003_dashboardpermission.py`
```sql
CREATE TABLE users_dashboardpermission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users_user(id),
    allowed_tabs TEXT NOT NULL,  -- JSON field
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

## Usage Examples

### Check User Permissions (Python)
```python
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(username='testuser')

# Check specific tab access
has_products_access = user.has_dashboard_access('products')
has_users_access = user.has_dashboard_access('users')

# Get permission object
try:
    permissions = user.dashboard_permissions
    allowed_tabs = permissions.allowed_tabs
    tab_names = permissions.get_allowed_tab_names()
except DashboardPermission.DoesNotExist:
    # User has no permissions set
    pass
```

### Template Usage
```html
{% load dashboard_permissions %}

<!-- Check permission in template -->
{% if user|has_dashboard_access:'products' %}
    <a href="{% url 'dashboard:products' %}">Products</a>
{% endif %}

<!-- Get access summary -->
{% dashboard_access_summary user as summary %}
<span class="badge">{{ summary.message }}</span>

<!-- Use navigation template tag -->
{% dashboard_nav_item 'products' 'dashboard:products' 'fas fa-box' 'Products' active_page %}
```

### API Usage
```javascript
// Get available dashboard tabs
fetch('/mb-admin/api/users/dashboard_tabs/')
    .then(response => response.json())
    .then(tabs => {
        // tabs = [{'value': 'products', 'label': 'Products'}, ...]
    });

// Create user with permissions
const userData = {
    username: 'newuser',
    email: 'newuser@example.com',
    dashboard_permissions: {
        allowed_tabs: ['products', 'orders', 'statistics']
    }
};

fetch('/mb-admin/api/users/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(userData)
});
```

## Configuration

### Settings (already configured)
```python
MIDDLEWARE = [
    # ... other middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'users.middleware.DashboardPermissionMiddleware',  # Added
    # ... other middleware
]
```

### URL Configuration
The middleware automatically protects these URL patterns:
- `/mb-admin/` - Dashboard home
- `/mb-admin/products/` - Products section
- `/mb-admin/api/products/` - Products API
- ... (all other dashboard URLs)

## User Setup

### For aminul3065@gmail.com (Already Configured)
- Status: Superuser and Staff
- Permissions: Full access to all dashboard tabs
- Can access: All 17 dashboard sections

### Default Permissions Applied
- **Staff users**: All 17 tabs
- **Regular users**: 4 basic tabs (home, orders, products, statistics)
- **Superusers**: Automatic full access (bypasses permission system)

## Testing

### Test Script
Run `python test_dashboard_permissions.py` to verify:
- User permission status
- Dashboard access methods
- Permission counts and summaries
- Available tabs list

### Manual Testing
1. Login as different user types
2. Check navigation menu visibility
3. Try accessing restricted URLs
4. Test API endpoints
5. Verify admin interface functionality

## Security Considerations

1. **Middleware Order**: Permission middleware runs after authentication
2. **API Protection**: All dashboard API endpoints are protected
3. **Template Security**: Navigation items only shown if accessible
4. **Bypass Logic**: Superusers and staff always have full access
5. **Graceful Degradation**: Users without permissions see limited interface

## Maintenance

### Adding New Dashboard Tabs
1. Add to `DashboardPermission.DASHBOARD_TABS`
2. Update middleware URL patterns
3. Add navigation template tag usage
4. Run migration if needed

### Modifying Permissions
- Use Django admin interface
- Use management commands
- Use API endpoints
- Direct database modification (advanced)

## Performance Notes

- Permissions are cached per request
- Uses `select_related` and `prefetch_related` for efficiency
- Minimal database queries for permission checking
- Template tags use smart caching

This implementation provides a complete, secure, and user-friendly dashboard permission system that can be easily extended and maintained.