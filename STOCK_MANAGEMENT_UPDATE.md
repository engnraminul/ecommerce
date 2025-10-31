# Stock Management Logic Update

## Overview
Updated the out-of-stock badge logic in product cards to intelligently handle products with variants. The system now checks both main product stock and variant availability before showing "Out of Stock" badges.

## Problem Solved
Previously, the system would show "Out of Stock" if the main product had zero stock, even when variants of that product were still available and in stock.

## New Logic Implementation

### 1. Product Model Enhancement
Added a new property method to the `Product` model:

```python
@property
def has_stock_in_variants(self):
    """Check if any active variant has stock (in_stock=True)"""
    return self.variants.filter(is_active=True, in_stock=True).exists()
```

**Location**: `products/models.py`

### 2. Template Logic Update
Updated the template condition for showing out-of-stock badges:

```html
{% if not product.is_available and not product.has_stock_in_variants %}
<div class="product-badge out-of-stock-badge">Out of Stock</div>
{% endif %}
```

**Location**: `frontend/templates/frontend/home.html`

## Business Logic Flow

### Scenario 1: Product without variants
- **Condition**: `not product.is_available and not product.has_stock_in_variants`
- **Result**: Shows "Out of Stock" if main product stock is 0
- **Logic**: `has_stock_in_variants` returns `False` (no variants exist)

### Scenario 2: Product with variants - all variants out of stock
- **Condition**: `not product.is_available and not product.has_stock_in_variants`
- **Result**: Shows "Out of Stock"
- **Logic**: Main product stock is 0 AND no variants have `in_stock=True`

### Scenario 3: Product with variants - some variants in stock
- **Condition**: `not product.is_available and not product.has_stock_in_variants`
- **Result**: Does NOT show "Out of Stock"
- **Logic**: Main product stock is 0 BUT at least one variant has `in_stock=True`

### Scenario 4: Product with stock
- **Condition**: `not product.is_available and not product.has_stock_in_variants`
- **Result**: Does NOT show "Out of Stock"
- **Logic**: `product.is_available` is `True`

## Technical Details

### Database Fields Used
1. **Product.stock_quantity**: Main product stock count
2. **Product.is_active**: Product activation status
3. **ProductVariant.in_stock**: Boolean field indicating variant availability
4. **ProductVariant.is_active**: Variant activation status

### Query Optimization
The `has_stock_in_variants` property uses an efficient EXISTS query:
```sql
SELECT 1 FROM products_productvariant 
WHERE product_id = ? AND is_active = 1 AND in_stock = 1 
LIMIT 1
```

### Performance Considerations
- Uses `.exists()` for optimal performance (stops at first match)
- Filters on indexed fields (`is_active`, `in_stock`)
- No unnecessary data loading

## Benefits

### 1. Business Logic Accuracy
- Prevents showing "Out of Stock" when variants are available
- Improves customer experience by showing accurate availability
- Reduces cart abandonment due to incorrect stock indicators

### 2. Inventory Management
- Supports complex product structures with multiple variants
- Allows granular stock control at variant level
- Maintains consistency between admin stock settings and frontend display

### 3. User Experience
- Customers see accurate product availability
- Reduces confusion about product stock status
- Encourages purchases when variants are available

## Example Use Cases

### Fashion Store
```
Product: "Cotton T-Shirt"
- Main Product Stock: 0
- Variants:
  - Small Red: in_stock=True, stock_quantity=5
  - Medium Blue: in_stock=True, stock_quantity=3
  - Large White: in_stock=False, stock_quantity=0

Result: NO "Out of Stock" badge (variants available)
```

### Electronics Store
```
Product: "Smartphone Model X"
- Main Product Stock: 0
- Variants:
  - 64GB Black: in_stock=False, stock_quantity=0
  - 128GB White: in_stock=False, stock_quantity=0

Result: SHOWS "Out of Stock" badge (no variants available)
```

### Simple Product (No Variants)
```
Product: "USB Cable"
- Main Product Stock: 0
- Variants: None

Result: SHOWS "Out of Stock" badge (no stock, no variants)
```

## Testing Scenarios

### Test Case 1: Product with available variants
1. Set main product stock to 0
2. Ensure at least one variant has `in_stock=True`
3. Verify NO "Out of Stock" badge appears

### Test Case 2: Product with no available variants
1. Set main product stock to 0
2. Set all variants to `in_stock=False`
3. Verify "Out of Stock" badge appears

### Test Case 3: Product without variants
1. Set main product stock to 0
2. Ensure no variants exist
3. Verify "Out of Stock" badge appears

## Migration Notes
- No database migration required
- Only code changes in model and template
- Backward compatible with existing data
- No impact on existing cart or order functionality

## Future Enhancements
1. **Variant-Specific Stock Display**: Show individual variant availability
2. **Smart Stock Alerts**: Notify when only certain variants are available
3. **Dynamic Pricing**: Adjust pricing based on variant availability
4. **Pre-order Support**: Allow orders when specific variants are restocking

## Related Files Modified
- `products/models.py`: Added `has_stock_in_variants` property
- `frontend/templates/frontend/home.html`: Updated out-of-stock logic
- `STOCK_MANAGEMENT_UPDATE.md`: This documentation file

## Configuration Options
The logic respects the following model settings:
- `Product.track_inventory`: Must be True for stock checking
- `Product.is_active`: Product must be active
- `ProductVariant.is_active`: Variants must be active
- `ProductVariant.in_stock`: Variant-level availability flag

This update provides a more intelligent and business-friendly approach to stock management while maintaining system performance and user experience.