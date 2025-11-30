# Meta Pixel Advanced Micro-Behavior Tracking Implementation Guide

## 🎯 Complete Implementation Summary

আপনার eCommerce সাইটে Meta Pixel এর সম্পূর্ণ micro-behavior tracking এখন implement করা হয়েছে। এখানে সব features এবং setup process।

---

## 📋 What's Implemented

### 1️⃣ **Dashboard Settings Enhanced**
- ✅ Meta Pixel ID field (modern approach)
- ✅ Access Token field (CAPI এর জন্য)
- ✅ Advanced tracking options:
  - Scroll Depth Tracking (25%, 50%, 75%, 100%)
  - Time on Page Tracking (15s, 30s, 60s, 120s)
  - Element Hover Tracking (buttons, products)
  - Section View Tracking (hero, products, etc.)
  - Advanced Cart Tracking (abandonment detection)
  - Checkout Funnel Tracking (step-by-step)
  - Server-Side Conversions API (CAPI)

### 2️⃣ **Frontend Tracking Classes Added**
- ✅ Product cards: `product-item` with tracking attributes
- ✅ Add to cart buttons: enhanced with product data
- ✅ Hero section: `hero-section` with ID
- ✅ Products section: `products-section` with ID
- ✅ Section tracking classes for IntersectionObserver

### 3️⃣ **Server-Side CAPI Service**
- ✅ Complete Meta Conversions API implementation
- ✅ Purchase event tracking
- ✅ Add to cart server-side events
- ✅ Checkout initiation tracking
- ✅ User data hashing (PII protection)

---

## 🚀 Setup Instructions

### Step 1: Dashboard Configuration

1. **Go to:** Dashboard > Settings > Integration Settings > Meta Pixel
2. **Enable:** Meta Pixel toggle
3. **Enter:** Your Meta Pixel ID (find in Facebook Events Manager)
4. **Enter:** Access Token (for CAPI - get from Facebook App settings)
5. **Enable tracking options you want:**
   - ✅ Scroll Depth Tracking
   - ✅ Time on Page Tracking  
   - ✅ Element Hover Tracking
   - ✅ Section View Tracking
   - ✅ Advanced Cart Tracking
   - ✅ Checkout Funnel Tracking
   - ✅ Server-Side Conversions API

### Step 2: Get Facebook Credentials

#### **Meta Pixel ID:**
1. Go to Facebook Events Manager
2. Select your Pixel
3. Copy the Pixel ID (15-16 digits)

#### **Access Token (for CAPI):**
1. Go to Facebook Developers
2. Create/select your app
3. Generate a System User Access Token with these permissions:
   - ads_management
   - business_management
4. Copy the long token

### Step 3: Test Implementation

1. **Save settings** in dashboard
2. **Visit your site** in incognito mode
3. **Open browser console** (F12)
4. **Test events:**
   - Scroll down → Should see scroll events
   - Hover over products → Should see hover events
   - Wait 15+ seconds → Should see time events
   - Add product to cart → Should see cart events

### Step 4: Verify in Facebook

1. **Go to:** Facebook Events Manager
2. **Select:** Your Pixel
3. **Check:** "Test Events" tab
4. **You should see:** All custom events coming in real-time

---

## 📊 Events That Will Be Tracked

### **Client-Side Events (JavaScript)**
```javascript
fbq('trackCustom', 'ScrollDepth', {scroll_percent: 50});
fbq('trackCustom', 'TimeOnPage', {time_seconds: 30});
fbq('trackCustom', 'HoverIntent', {element_type: 'product-card'});
fbq('trackCustom', 'ViewSection', {section_id: 'hero'});
fbq('trackCustom', 'AddToCart', {product_id: '123'});
fbq('trackCustom', 'CartAbandon', {product_id: '123'});
fbq('trackCustom', 'InitiateCheckout');
fbq('trackCustom', 'CheckoutShipping');
fbq('trackCustom', 'CheckoutPayment');
fbq('trackCustom', 'PaymentAbandon');
```

### **Server-Side Events (CAPI)**
- Purchase (with order details)
- AddToCart (server confirmation)
- InitiateCheckout (checkout start)

---

## 🔧 Integration with Your Existing Code

### **Cart Integration Example:**
```python
# In your cart views.py
from settings.meta_conversions_api import send_add_to_cart_event

def add_to_cart(request):
    # ... your existing cart logic ...
    
    # Send server-side event
    product_data = {
        'product_id': product.id,
        'product_name': product.name,
        'price': product.price,
        'currency': 'BDT'
    }
    user_data = {
        'email': request.user.email if request.user.is_authenticated else None
    }
    send_add_to_cart_event(request, product_data, user_data)
```

### **Order Integration Example:**
```python
# In your orders views.py  
from settings.meta_conversions_api import send_purchase_event

def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Send server-side purchase event
    order_data = {
        'order_id': order.id,
        'total_amount': float(order.total),
        'currency': 'BDT',
        'items': [
            {
                'product_id': item.product.id,
                'quantity': item.quantity,
                'price': float(item.price)
            } for item in order.items.all()
        ]
    }
    user_data = {
        'email': order.customer_email,
        'phone': order.customer_phone,
        'first_name': order.customer_name.split()[0] if order.customer_name else None
    }
    send_purchase_event(request, order_data, user_data)
```

---

## 🎯 Expected Results

### **Immediate Benefits:**
- 📈 **Better Ad Performance:** More accurate audience building
- 💰 **Lower CPM:** Better pixel optimization
- 🎯 **Precise Targeting:** Micro-behavior based audiences
- 📊 **Rich Analytics:** Detailed user journey tracking

### **Advanced Audiences You Can Create:**
1. **Engaged Users:** Scrolled 75%+ on product pages
2. **Intent Users:** Hovered over 3+ products
3. **Time Spenders:** Spent 60+ seconds on site
4. **Cart Abandoners:** Added to cart but didn't checkout
5. **Payment Abandoners:** Reached payment but didn't complete

---

## 🛠️ Troubleshooting

### **If Events Not Showing:**
1. Check browser console for JavaScript errors
2. Verify Pixel ID is correct (15-16 digits)
3. Check that Meta Pixel is enabled in settings
4. Ensure you're testing in incognito/private mode

### **If CAPI Not Working:**
1. Verify Access Token has correct permissions
2. Check Django logs for error messages
3. Ensure server can reach graph.facebook.com
4. Test with Facebook's Event Quality tab

### **Common Issues:**
- **Ad Blockers:** May block client-side events (CAPI still works)
- **iOS 14.5+:** Some events may be limited (CAPI helps here)
- **GDPR:** Ensure consent management if needed

---

## 📱 Mobile Optimization

All tracking is mobile-friendly and includes:
- Touch event handling
- Mobile-specific scroll tracking
- Responsive hover alternatives
- Mobile checkout funnel tracking

---

## 🔒 Privacy & Compliance

- All PII data is SHA256 hashed before sending to Facebook
- User consent is respected (integrate with your consent manager)
- GDPR/CCPA compliant data handling
- No sensitive data stored in cookies

---

## 📈 Advanced Optimization Tips

1. **Create Custom Audiences:**
   - ScrollDepth >= 75%
   - TimeOnPage >= 60s
   - HoverIntent >= 3 events

2. **Setup Conversion Optimization:**
   - Use Purchase events for ROAS campaigns
   - Create lookalike audiences from engaged users
   - Use micro-events for top-funnel optimization

3. **Attribution Analysis:**
   - Compare client-side vs server-side events
   - Monitor Event Quality scores
   - Track iOS vs Android performance differences

---

## 🎉 You're All Set!

Your Meta Pixel is now supercharged with advanced micro-behavior tracking! This implementation gives you enterprise-level Facebook advertising capabilities that most eCommerce sites don't have.

**Next Steps:**
1. Set up the credentials in your dashboard
2. Test all events in Facebook Events Manager  
3. Create advanced audiences based on micro-behaviors
4. Launch optimized ad campaigns with better targeting

**Need Help?** Check the Django logs for any server-side issues, or use browser console to debug client-side events.