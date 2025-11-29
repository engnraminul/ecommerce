# Dynamic Site Name and Tagline Implementation Guide

This document explains how the site name and tagline have been made dynamic across all SEO meta tags and schema markup, sourced from the Dashboard > Settings > General > Site Identity section.

## 🎛️ **Dashboard Settings Integration**

### **Settings Model Fields**
Located in `settings/models.py` - SiteSettings model:
```python
class SiteSettings(models.Model):
    # Site Identity
    site_name = models.CharField(max_length=200, default="My Brand Store")
    site_tagline = models.CharField(max_length=300, default="Your one-stop shop for quality products")
    site_logo = models.CharField(max_length=500, blank=True, null=True)
    site_favicon = models.CharField(max_length=500, blank=True, null=True)
```

### **Dashboard Admin Interface**
Accessible via: **Dashboard > Settings > General Settings > Site Identity**
- **Site Name**: Primary brand name (e.g., "Manob Bazar")
- **Site Tagline**: Brand description/slogan (e.g., "Premium Bangladeshi fashion accessories")
- **Site Logo**: Logo file path
- **Site Favicon**: Favicon file path

## 🔄 **Dynamic Template Implementation**

### **Template Variable Usage**
All templates now use dynamic variables with fallbacks:
```django
{{ site_settings.site_name|default:'Manob Bazar' }}
{{ site_settings.site_tagline|default:'Leading Bangladeshi brand for premium leather wallets...' }}
```

## 📄 **Updated Pages and Templates**

### **1. Homepage** (`frontend/templates/frontend/home.html`)
```html
<!-- Title -->
{{ site_settings.site_name|default:'Manob Bazar' }} - Premium Fashion Accessories in Bangladesh

<!-- Meta Description -->
{{ site_settings.site_name|default:'Manob Bazar' }} - {{ site_settings.site_tagline|default:'Leading Bangladeshi brand...' }}

<!-- Open Graph -->
<meta property="og:site_name" content="{{ site_settings.site_name|default:'Manob Bazar' }}">

<!-- Schema -->
"name": "{{ site_settings.site_name|default:'Manob Bazar'|escapejs }}"
```

### **2. Product Detail Page** (`frontend/templates/frontend/product_detail.html`)
```html
<!-- Title -->
{{ product.name }} | {{ site_settings.site_name|default:'Manob Bazar' }} BD

<!-- Brand Schema -->
"brand": {
    "@type": "Brand",
    "name": "{{ site_settings.site_name|default:'Manob Bazar'|escapejs }}"
}

<!-- Seller Schema -->
"seller": {
    "@type": "Organization", 
    "name": "{{ site_settings.site_name|default:'Manob Bazar'|escapejs }}"
}
```

### **3. Category Pages** (`frontend/templates/frontend/category_products.html`)
```html
<!-- Title -->
{{ category.name }} | {{ site_settings.site_name|default:'Manob Bazar' }} - Premium Fashion Accessories

<!-- Description -->
Shop premium {{ category.name|lower }} at {{ site_settings.site_name|default:'Manob Bazar' }}
```

### **4. Products Listing** (`frontend/templates/frontend/products.html`)
```html
<!-- Title -->
All Fashion Accessories | {{ site_settings.site_name|default:'Manob Bazar' }} - Premium Brand

<!-- Description -->
{{ site_settings.site_tagline|default:'Discover authentic leather wallets...' }}
```

### **5. Search Results** (`frontend/templates/frontend/search.html`)
```html
<!-- Title -->
Search Results for {{ query }} | {{ site_settings.site_name|default:'Manob Bazar' }}

<!-- Twitter Cards -->
Found {{ products.count }} fashion accessories at {{ site_settings.site_name|default:'Manob Bazar' }}
```

### **6. Contact Page** (`contact/templates/contact/contact.html`)
```html
<!-- Title -->
Contact {{ site_settings.site_name|default:'Manob Bazar' }} - Customer Support

<!-- Schema -->
"name": "{{ site_settings.site_name|default:'Manob Bazar'|escapejs }}"
"description": "{{ site_settings.site_tagline|default:'Premium Bangladeshi...'|escapejs }}"
```

### **7. Categories Listing** (`frontend/templates/frontend/categories.html`)
```html
<!-- Title -->
Fashion Accessories Categories | {{ site_settings.site_name|default:'Manob Bazar' }}

<!-- Description -->
{{ site_settings.site_tagline|default:'Discover leather wallets...' }}
```

### **8. Shopping Cart** (`frontend/templates/frontend/cart.html`)
```html
<!-- Title -->
Shopping Cart - {{ site_settings.site_name|default:'Manob Bazar' }}

<!-- Open Graph -->
<meta property="og:site_name" content="{{ site_settings.site_name|default:'Manob Bazar' }}">
```

## 🎨 **Advanced Dynamic Features**

### **Logo Integration**
```html
<!-- Dynamic Logo Usage -->
"logo": "{{ request.scheme }}://{{ request.get_host }}{% if site_settings.site_logo %}{{ site_settings.site_logo }}{% else %}{% static 'frontend/images/logo.png' %}{% endif %}"
```

### **Social Media Links**
```html
<!-- Dynamic Social Links -->
"sameAs": [
    "{% if site_settings.facebook_link %}{{ site_settings.facebook_link }}{% else %}https://facebook.com/{{ site_settings.site_name|default:'manobbazar'|lower|slugify }}{% endif %}"
]
```

### **Fallback Strategy**
Every dynamic field includes intelligent fallbacks:
1. **Primary**: Database value (`site_settings.site_name`)
2. **Fallback**: Default brand value (`'Manob Bazar'`)
3. **Schema Safe**: Escaped for JSON (`|escapejs`)

## 🛠️ **How to Update Site Information**

### **Step 1: Access Dashboard**
1. Log into admin dashboard
2. Navigate to **Settings** → **General Settings**
3. Click on **Site Identity** section

### **Step 2: Update Fields**
- **Site Name**: Enter your brand name (e.g., "Manob Bazar", "Fashion Hub BD")
- **Site Tagline**: Enter brand description (e.g., "Premium fashion accessories from Bangladesh")
- **Site Logo**: Upload or specify logo path
- **Site Favicon**: Upload or specify favicon path

### **Step 3: Save Changes**
- Click **Save Settings**
- Changes will automatically reflect across all pages

## 📱 **SEO Benefits of Dynamic Implementation**

### **Brand Consistency**
- ✅ Single source of truth for brand information
- ✅ Consistent branding across all pages
- ✅ Easy rebranding without template changes
- ✅ Centralized brand management

### **SEO Advantages**
- ✅ Dynamic title optimization
- ✅ Consistent brand mentions in schemas
- ✅ Proper Open Graph branding
- ✅ Social media integration
- ✅ Search engine brand recognition

### **Maintenance Benefits**
- ✅ No hardcoded values in templates
- ✅ Easy brand updates
- ✅ Scalable for multiple brands
- ✅ Admin-friendly interface

## 🔧 **Technical Implementation Notes**

### **Context Processor**
The `site_settings` variable is available in all templates through the context processor that loads the active site settings.

### **Template Filters Used**
- `|default:'fallback'` - Provides fallback values
- `|escapejs` - Escapes content for JSON schema
- `|lower|slugify` - Creates URL-friendly versions

### **Database Efficiency**
Settings are cached and retrieved using `SiteSettings.get_active_settings()` method for optimal performance.

## 🎯 **Example Configuration**

### **Sample Settings for Manob Bazar**
```
Site Name: Manob Bazar
Site Tagline: Premium Bangladeshi fashion accessories - leather wallets, belts, watches, ladies bags & clothing with authentic quality and nationwide delivery
Site Logo: media/logos/manob-bazar-logo.png
Site Favicon: media/icons/manob-bazar-favicon.ico
```

### **Resulting SEO Output**
- **Homepage Title**: "Manob Bazar - Premium Fashion Accessories in Bangladesh"
- **Product Title**: "Leather Wallet | Manob Bazar BD"
- **Schema Brand**: "Manob Bazar"
- **Social Links**: Dynamic generation based on brand name

This implementation ensures that your entire eCommerce platform maintains consistent branding while allowing for easy updates through the admin dashboard, making it perfect for both single-brand stores and multi-brand marketplaces.