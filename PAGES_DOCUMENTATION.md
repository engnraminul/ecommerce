# Pages Management System Documentation

## Overview

The Pages Management System is a comprehensive Django app that provides a professional content management solution for creating, managing, and displaying static pages on your website. It includes features like categorization, templates, SEO optimization, comments, analytics, and a full dashboard interface.

## Features

### Core Features
- **Page Management**: Create, edit, delete, and organize pages
- **Categories**: Organize pages into logical categories
- **Templates**: Multiple page templates for different layouts
- **SEO Optimization**: Built-in meta tags, canonical URLs, and SEO-friendly features
- **Publishing Control**: Draft, published, and archived status with scheduled publishing
- **Content Editor**: Rich text content editing
- **Media Management**: Attach images, videos, and documents to pages
- **Comments System**: Optional commenting with approval workflow
- **Analytics**: Track page views, bounce rates, and performance
- **Menu Integration**: Show pages in navigation menus
- **User Permissions**: Role-based access control

### Dashboard Features
- **Modern Interface**: Clean, responsive dashboard for content management
- **Bulk Operations**: Perform actions on multiple pages at once
- **Search & Filtering**: Find pages quickly with advanced filters
- **Real-time Statistics**: View page performance and analytics
- **Revision History**: Track changes and restore previous versions
- **Quick Actions**: Publish, feature, duplicate pages with one click

## Models

### PageCategory
Organizes pages into categories for better content management.

**Fields:**
- `name`: Category name
- `slug`: URL-friendly identifier
- `description`: Category description
- `is_active`: Whether category is active
- `created_at`, `updated_at`: Timestamps

### PageTemplate
Defines different layouts and styles for pages.

**Fields:**
- `name`: Template name
- `slug`: URL-friendly identifier
- `template_type`: Type of template (default, landing, article, etc.)
- `template_file`: Path to template file
- `description`: Template description
- `preview_image`: Template preview image
- `is_active`: Whether template is active

### Page
The main page model containing all page content and settings.

**Fields:**
- `title`: Page title
- `slug`: URL-friendly identifier
- `category`: Associated category (optional)
- `template`: Page template (optional)
- `content`: Main page content
- `excerpt`: Short description for SEO and previews
- `featured_image`: Main page image
- `meta_title`, `meta_description`, `meta_keywords`: SEO fields
- `canonical_url`: Canonical URL for SEO
- `status`: Draft, published, or archived
- `is_featured`: Featured page flag
- `show_in_menu`: Display in navigation
- `menu_order`: Order in navigation menu
- `allow_comments`: Enable comments
- `require_login`: Require user authentication
- `publish_date`, `expiry_date`: Publishing schedule
- `author`, `last_modified_by`: User tracking
- `view_count`, `share_count`: Analytics counters

### PageRevision
Tracks page changes for version control.

### PageMedia
Manages media attachments for pages.

### PageComment
Handles user comments on pages.

### PageAnalytics
Stores analytics data for pages.

## API Endpoints

### Pages API
- `GET /api/v1/pages/pages/` - List pages
- `POST /api/v1/pages/pages/` - Create page
- `GET /api/v1/pages/pages/{id}/` - Get page details
- `PUT /api/v1/pages/pages/{id}/` - Update page
- `DELETE /api/v1/pages/pages/{id}/` - Delete page
- `POST /api/v1/pages/pages/{id}/duplicate/` - Duplicate page
- `POST /api/v1/pages/pages/{id}/publish/` - Publish page
- `GET /api/v1/pages/pages/featured/` - Get featured pages
- `GET /api/v1/pages/pages/menu_items/` - Get menu pages

### Categories API
- `GET /api/v1/pages/categories/` - List categories
- `POST /api/v1/pages/categories/` - Create category
- `GET /api/v1/pages/categories/{id}/` - Get category
- `PUT /api/v1/pages/categories/{id}/` - Update category
- `DELETE /api/v1/pages/categories/{id}/` - Delete category

### Dashboard API
- `GET /mb-admin/api/pages/pages/` - Dashboard pages list
- `GET /mb-admin/api/pages/pages/statistics/` - Page statistics
- `POST /mb-admin/api/pages/pages/bulk_action/` - Bulk operations
- `GET /mb-admin/api/pages/analytics/summary/` - Analytics summary

## Frontend Views

### Public Views
- `/pages/` - List all published pages
- `/pages/category/{slug}/` - Pages in specific category
- `/pages/{slug}/` - Individual page view

### Dashboard Views
- `/mb-admin/pages/` - Pages management dashboard

## Installation & Setup

1. **Add to INSTALLED_APPS**:
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'pages.apps.PagesConfig',
   ]
   ```

2. **Include URLs**:
   ```python
   # In main urls.py
   urlpatterns = [
       # ... other patterns
       path('api/v1/pages/', include('pages.urls')),
       path('pages/', include('pages.urls')),
   ]
   ```

3. **Run Migrations**:
   ```bash
   python manage.py makemigrations pages
   python manage.py migrate pages
   ```

4. **Create Sample Data** (optional):
   ```bash
   python manage.py create_sample_pages
   ```

## Usage Examples

### Creating a Page Programmatically
```python
from pages.models import Page, PageCategory
from django.contrib.auth import get_user_model

User = get_user_model()
author = User.objects.first()

# Create category
category = PageCategory.objects.create(
    name="Company",
    description="Company pages"
)

# Create page
page = Page.objects.create(
    title="About Us",
    content="Welcome to our company...",
    excerpt="Learn about our company",
    category=category,
    author=author,
    status='published',
    show_in_menu=True
)
```

### Using the API
```javascript
// Fetch published pages
fetch('/api/v1/pages/pages/?status=published')
    .then(response => response.json())
    .then(data => console.log(data));

// Create a new page
fetch('/api/v1/pages/pages/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        title: 'New Page',
        content: 'Page content here...',
        status: 'draft'
    })
});
```

### Template Usage
```html
<!-- In your template -->
{% load static %}

<!-- List featured pages -->
{% for page in featured_pages %}
    <div class="page-card">
        <h3><a href="{{ page.get_absolute_url }}">{{ page.title }}</a></h3>
        <p>{{ page.excerpt }}</p>
    </div>
{% endfor %}

<!-- Display page content -->
<article>
    <h1>{{ page.title }}</h1>
    <div class="content">
        {{ page.content|linebreaks }}
    </div>
</article>
```

## Customization

### Custom Templates
Create custom page templates by:

1. Creating template files in `pages/templates/pages/`
2. Adding template entries in the admin or via API
3. Assigning templates to pages

### Custom Fields
Extend the Page model by creating a custom model that inherits from Page:

```python
class CustomPage(Page):
    custom_field = models.CharField(max_length=200)
    
    class Meta:
        proxy = True
```

### Custom Serializers
Create custom serializers for additional API functionality:

```python
from pages.serializers import PageDetailSerializer

class CustomPageSerializer(PageDetailSerializer):
    custom_data = serializers.SerializerMethodField()
    
    def get_custom_data(self, obj):
        return "Custom data here"
```

## Security Considerations

- User permissions are enforced at the view level
- CSRF protection is enabled for all POST requests
- User input is properly escaped in templates
- File uploads are validated and stored securely
- Login requirements can be set per page

## Performance Optimization

- Database queries are optimized with select_related and prefetch_related
- Pagination is implemented for large datasets
- Caching can be added for frequently accessed pages
- Media files are served efficiently
- Analytics are aggregated for better performance

## Troubleshooting

### Common Issues

1. **URL namespace conflicts**: Ensure unique namespace in urls.py
2. **Missing templates**: Create required template files
3. **Permission errors**: Check user permissions and authentication
4. **Media files not loading**: Verify MEDIA_URL and MEDIA_ROOT settings

### Debug Mode
Enable Django debug mode for detailed error messages:
```python
DEBUG = True
```

## Support

For issues and feature requests, please check the documentation or contact support.

## Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added analytics and revision history
- **v1.2.0**: Enhanced dashboard and bulk operations

## License

This app is part of the ecommerce project and follows the same licensing terms.