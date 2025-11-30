# Courier Item Description Fix

## Problem
When sending orders to courier services, the item descriptions were showing full product names and SKUs, resulting in long descriptions like:
```
1x One Part Leather Luxury Wallet MW02 MW02 Black, 1x Original Leather Classic Wallet MW04 MW04 Black
```

## Solution
Updated the courier item description logic to:
- **For products with variants**: Show only the variant identifier (SKU or name) like "MW02 Black"  
- **For products without variants**: Show the full product name

## Result
Now courier descriptions are concise and clear:
```
1x MW02 Black, 1x MW04 Black
```

## Files Modified
1. `settings/utils.py` - Updated `send_order_to_curier()` function
2. `dashboard/templates/dashboard/orders.html` - Updated courier sticker generation logic

## Implementation Details
The logic prioritizes:
1. Variant SKU (if available and not empty)
2. Variant name (if SKU is not available)
3. Product name (for non-variant products or as fallback)

This ensures consistency between courier API calls and courier sticker generation.