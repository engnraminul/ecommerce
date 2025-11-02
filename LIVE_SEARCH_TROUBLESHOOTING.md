# Live Search Troubleshooting Guide

## 🔧 Common Issues and Solutions

### Issue 1: "Unable to fetch search results. Please try again."

**Possible Causes:**
1. API endpoint not properly configured
2. JavaScript fetch request failing
3. Django view has errors
4. Database connection issues

**Solutions:**

#### Check API Endpoint
```bash
# Test the API directly in browser or curl
curl "http://127.0.0.1:8000/api/live-search/?q=test"
```

#### Verify URL Configuration
Ensure in `frontend/urls.py`:
```python
path('api/live-search/', views.live_search_api, name='live_search_api'),
```

#### Check Django Logs
Look for errors in the Django console where you ran `python manage.py runserver`

#### Test API Function
```python
# In Django shell (python manage.py shell)
from frontend.views import live_search_api
from django.test import RequestFactory
factory = RequestFactory()
request = factory.get('/api/live-search/?q=test')
response = live_search_api(request)
print(response.content)
```

### Issue 2: Live Search Dropdown Not Showing in Right Place

**Possible Causes:**
1. CSS positioning conflicts
2. Z-index issues
3. Overflow hidden on parent elements
4. JavaScript positioning errors

**Solutions:**

#### CSS Fixes Applied
```css
/* Fixed in live-search.css */
.search-input-wrapper {
    overflow: visible; /* Changed from hidden */
}

.live-search-dropdown {
    position: absolute;
    top: calc(100% + 5px);
    z-index: 9999;
    width: 100%;
}
```

#### JavaScript Positioning Fix
```javascript
// Fixed in live-search.js
positionDropdown() {
    const searchForm = this.searchInput.closest('.search-form');
    if (searchForm) {
        const rect = searchForm.getBoundingClientRect();
        this.dropdown.style.top = `${rect.height + 5}px`;
        this.dropdown.style.left = '0';
        this.dropdown.style.width = `${rect.width}px`;
    }
}
```

### Issue 3: JavaScript Not Loading

**Check Loading Order:**
Ensure in `base.html`:
```html
<script src="{% static 'frontend/js/live-search.js' %}?v=1.0"></script>
```

**Debug JavaScript:**
```javascript
// In browser console
console.log(window.liveSearch);
window.debugLiveSearch();
```

### Issue 4: No Search Results Despite Having Data

**Check Database:**
```python
# In Django shell
from products.models import Product
print(Product.objects.filter(name__icontains='test').count())
```

**Verify Model Fields:**
Ensure products have:
- `is_active=True`
- Proper `name` and `description` fields
- Valid `category` relationships

## 🧪 Testing Checklist

### Manual Testing Steps

1. **Visit Test Page**
   ```
   http://127.0.0.1:8000/test/live-search/
   ```

2. **API Test**
   - Click "Test API" button
   - Should return JSON with products/categories
   - Check browser network tab for requests

3. **Elements Test**
   - Click "Check Elements" button
   - All elements should show ✅ Found

4. **Live Search Test**
   - Type in search box (minimum 2 characters)
   - Dropdown should appear below search box
   - Should show products, categories, suggestions

5. **Keyboard Navigation**
   - Use arrow keys to navigate suggestions
   - Press Enter to select
   - Press Escape to close

### Browser Console Debugging

```javascript
// Check if live search is loaded
console.log('Live search loaded:', !!window.liveSearch);

// Debug live search
window.debugLiveSearch();

// Test API manually
fetch('/api/live-search/?q=test')
    .then(r => r.json())
    .then(console.log);

// Check dropdown positioning
const dropdown = document.querySelector('.live-search-dropdown');
console.log('Dropdown:', dropdown?.getBoundingClientRect());
```

## 🚀 Performance Optimization

### Caching Implementation
```python
# Add to Django settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'live-search-cache',
    }
}

# Use in view
from django.core.cache import cache

def live_search_api(request):
    cache_key = f"search_{query}_{category}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse(cached_result)
    # ... perform search ...
    cache.set(cache_key, result, 300)  # Cache for 5 minutes
```

### Database Optimization
```python
# Add database indexes
class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
```

## 📱 Mobile Specific Issues

### Touch Events
```javascript
// Add to live-search.js for better mobile support
bindTouchEvents() {
    if ('ontouchstart' in window) {
        this.dropdown.addEventListener('touchstart', (e) => {
            e.preventDefault();
        });
    }
}
```

### Viewport Issues
```css
/* Mobile dropdown positioning */
@media (max-width: 768px) {
    .live-search-dropdown {
        position: fixed;
        top: auto;
        left: 10px;
        right: 10px;
        width: auto;
    }
}
```

## 🔍 Advanced Debugging

### Enable Debug Mode
```javascript
// Add to live-search.js constructor
this.debugMode = true; // Set to true for detailed logging

if (this.debugMode) {
    console.log('LiveSearch Debug Mode Enabled');
}
```

### Network Analysis
1. Open browser Developer Tools (F12)
2. Go to Network tab
3. Type in search box
4. Check for `/api/live-search/` requests
5. Verify request/response data

### Element Inspection
1. Right-click on search input
2. Select "Inspect Element"
3. Check if `.live-search-dropdown` element exists
4. Verify CSS styles and positioning

## 📞 Support

If issues persist:

1. **Check Django Logs**: Look for Python errors in terminal
2. **Browser Console**: Check for JavaScript errors
3. **Network Tab**: Verify API requests are being made
4. **Element Inspector**: Check DOM structure and CSS

### Common Error Messages

- **"LiveSearchManager is not defined"**: JavaScript file not loaded
- **"Cannot read property of null"**: DOM elements not found
- **"Failed to fetch"**: API endpoint not accessible
- **"Dropdown not positioned correctly"**: CSS positioning issue

### Quick Fixes

```bash
# Clear browser cache
Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

# Restart Django server
Ctrl+C then python manage.py runserver

# Check file permissions
# Ensure static files are accessible
```

---

**Created**: November 2025  
**Last Updated**: November 2025  
**Version**: 1.0