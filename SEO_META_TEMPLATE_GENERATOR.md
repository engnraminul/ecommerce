# SEO Meta Tags Template Generator

Use this template to generate custom SEO meta tags for any product. Simply fill in your product details below:

## Product Details Format

```
Product Name: [Your product name here - max 50 characters for best SEO]
Brand: [Brand name or category]
Price: [Product price in your currency]
Product URL: [Full URL to the product page]
Image URL: [URL to the primary product image]
SKU: [Product SKU or unique identifier]
Rating Value: [Average rating (1-5) or 0 if no reviews]
Review Count: [Total number of reviews or 0 if none]
```

## Example Product Details

```
Product Name: iPhone 14 Pro Max 256GB Space Black
Brand: Apple
Price: 1299
Product URL: https://yourstore.com/products/iphone-14-pro-max-256gb
Image URL: https://yourstore.com/media/products/iphone-14-pro-max.jpg
SKU: APL-IP14PM-256-SB
Rating Value: 4.5
Review Count: 127
```

## Generated Meta Tags Template

Based on the product details above, here's what the complete meta setup would look like:

```html
<!-- SEO Title (60 chars max) -->
<title>iPhone 14 Pro Max 256GB Space Black | Buy Online</title>

<!-- Meta Description (130-160 chars) -->
<meta name="description" content="iPhone 14 Pro Max 256GB in Space Black. Latest Apple smartphone with advanced camera system, A16 Bionic chip. Free shipping available. 4.5★ (127 reviews)">

<!-- Canonical URL -->
<link rel="canonical" href="https://yourstore.com/products/iphone-14-pro-max-256gb">

<!-- Open Graph Tags -->
<meta property="og:title" content="iPhone 14 Pro Max 256GB Space Black">
<meta property="og:description" content="iPhone 14 Pro Max 256GB in Space Black. Latest Apple smartphone with advanced camera system, A16 Bionic chip. Free shipping available.">
<meta property="og:image" content="https://yourstore.com/media/products/iphone-14-pro-max.jpg">
<meta property="og:url" content="https://yourstore.com/products/iphone-14-pro-max-256gb">
<meta property="og:type" content="product">
<meta property="og:site_name" content="Your Store Name">
<meta property="product:price:amount" content="1299">
<meta property="product:price:currency" content="USD">
<meta property="product:availability" content="in stock">
<meta property="product:condition" content="new">
<meta property="product:retailer_item_id" content="APL-IP14PM-256-SB">

<!-- Twitter Card Tags -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="iPhone 14 Pro Max 256GB Space Black">
<meta name="twitter:description" content="iPhone 14 Pro Max 256GB in Space Black. Latest Apple smartphone with advanced camera system, A16 Bionic chip. Free shipping available.">
<meta name="twitter:image" content="https://yourstore.com/media/products/iphone-14-pro-max.jpg">

<!-- Product Schema (JSON-LD) -->
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "iPhone 14 Pro Max 256GB Space Black",
    "description": "iPhone 14 Pro Max 256GB in Space Black. Latest Apple smartphone with advanced camera system, A16 Bionic chip, and exceptional performance.",
    "image": [
        "https://yourstore.com/media/products/iphone-14-pro-max.jpg"
    ],
    "brand": {
        "@type": "Brand",
        "name": "Apple"
    },
    "sku": "APL-IP14PM-256-SB",
    "url": "https://yourstore.com/products/iphone-14-pro-max-256gb",
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.5",
        "reviewCount": "127",
        "bestRating": "5",
        "worstRating": "1"
    },
    "offers": {
        "@type": "Offer",
        "price": "1299",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock",
        "url": "https://yourstore.com/products/iphone-14-pro-max-256gb",
        "seller": {
            "@type": "Organization",
            "name": "Your Store Name"
        },
        "itemCondition": "https://schema.org/NewCondition"
    }
}
</script>
</script>

```

## Instructions for Custom Implementation

1. **Fill in your product details** using the format above
2. **Replace placeholder values** in the meta tags template
3. **Adjust character limits**:
   - Title: Keep under 60 characters
   - Meta description: Keep between 130-160 characters
4. **Update URLs** to match your domain and URL structure
5. **Set correct currency** (USD, EUR, GBP, BDT, etc.)
6. **Validate your implementation** using Google's Rich Results Test

## Quick Customization Checklist

- [ ] Product name is compelling and under 60 chars for title
- [ ] Meta description is informative and 130-160 chars
- [ ] All URLs are absolute and correct
- [ ] Image URL is high quality and accessible
- [ ] SKU is unique and trackable
- [ ] Currency matches your store's currency
- [ ] Brand name is correct
- [ ] Rating and review count are accurate (use 0 if no reviews)

## Advanced Options

For enhanced SEO, you can also add:
- **Product variants** (size, color, etc.)
- **Additional images** in the schema
- **Product category** information  
- **Shipping details** in offers
- **Product dimensions** and weight
- **GTIN/Barcode** if available

The current implementation in your Django template automatically handles all these details based on your product model data.