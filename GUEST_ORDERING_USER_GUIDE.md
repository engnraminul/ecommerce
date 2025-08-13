# Guest Ordering - User Testing Guide

## Overview
Guest ordering allows users to place orders without creating an account or logging in. This feature has been successfully implemented and tested.

## How to Test Guest Ordering

### 1. Browse and Add to Cart
1. Open your browser and go to `http://127.0.0.1:8000/`
2. Browse products without logging in
3. Click on any product to view details
4. Select product options (color, size) if available
5. Click "Add to Cart" or "Buy Now"

### 2. Guest Checkout Process

#### Using "Add to Cart"
1. Add items to cart as a guest
2. Click the cart icon to view cart
3. Click "Checkout" button
4. **You should NOT be redirected to login page**
5. Fill in the checkout form with:
   - Email address (required for order tracking)
   - Phone number
   - Shipping address
   - Select payment method

#### Using "Buy Now" (Direct Checkout)
1. On any product page, click "Buy Now"
2. **You should be taken directly to checkout** (not login)
3. Complete the same checkout process

### 3. Required Information for Guest Orders
- **Email address** (required for order confirmation and tracking)
- **Phone number** (required for delivery contact)
- **Shipping address** (delivery location)
- **Payment method** (COD, bKash, or Nagad)

### 4. Order Tracking
After placing a guest order:
1. You'll receive an order number
2. Use this order number to track your order at `/track-order/`
3. No login required for order tracking

## Features Available for Guest Users

### ✅ Available
- Browse all products
- View product details
- Add items to cart (session-based)
- Modify cart quantities
- Remove items from cart
- Complete checkout
- Place orders
- Track orders using order number
- View order confirmation

### ❌ Not Available
- Order history (requires account)
- Wishlist (requires account)
- Saved addresses (requires account)
- User profile features
- Loyalty points/rewards

## Technical Details

### Session-Based Cart
- Guest carts are stored using browser sessions
- Cart persists across page refreshes
- Cart is cleared when:
  - Order is completed successfully
  - User manually clears cart
  - Session expires

### Guest Order Data
Guest orders store:
- Guest email (for tracking and communication)
- Guest phone (for delivery contact)
- Session ID (for reference)
- `is_guest_order = True` flag

### Order Tracking
- Public tracking endpoint: `/track-order/`
- No authentication required
- Uses order number for lookup

## Testing Checklist

### Manual Testing
- [ ] Can browse products without login
- [ ] Can add items to cart without login
- [ ] Cart persists across page refreshes
- [ ] "Buy Now" goes to checkout (not login)
- [ ] Checkout form loads correctly
- [ ] Can complete order with email and phone
- [ ] Receives order confirmation
- [ ] Can track order with order number

### Error Cases to Test
- [ ] Empty cart checkout (should redirect to cart)
- [ ] Invalid email format (should show validation error)
- [ ] Missing required fields (should show field errors)
- [ ] Network errors during order placement

## Browser Compatibility
Guest ordering works with:
- Chrome, Firefox, Safari, Edge
- Mobile browsers
- Requires JavaScript enabled
- Requires cookies enabled (for session management)

## Security Notes
- Guest data is handled securely
- Email addresses are validated
- Session data expires automatically
- No sensitive data stored in local storage
- CSRF protection enabled

## Troubleshooting

### If "Buy Now" Still Redirects to Login
1. Check that `@login_required` decorator was removed from checkout view
2. Clear browser cache and cookies
3. Restart Django server
4. Test in incognito/private browsing mode

### If Cart Doesn't Persist
1. Ensure cookies are enabled in browser
2. Check Django session configuration
3. Verify session middleware is enabled

### If Order Creation Fails
1. Check that order form includes guest email
2. Verify API endpoints allow guest access
3. Check browser console for JavaScript errors

## Success Indicators
When guest ordering is working correctly:
1. ✅ "Buy Now" button takes you directly to checkout
2. ✅ Checkout page loads without login requirement
3. ✅ Order can be completed with just email/phone
4. ✅ Order confirmation page displays
5. ✅ Order tracking works with order number

## Contact Support
If you encounter any issues with guest ordering:
1. Check browser console for error messages
2. Verify all required fields are filled
3. Try clearing browser cache
4. Test in different browser or incognito mode

The guest ordering feature is now fully functional and ready for production use!
