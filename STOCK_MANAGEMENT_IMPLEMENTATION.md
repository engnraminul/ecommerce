# Stock Management Implementation for Order Operations

## Overview
This document describes the implemented automatic stock management system for order deletions and status changes in the ecommerce platform.

## Features Implemented

### 1. **Order Deletion Stock Management**

#### Individual Order Deletion (`deleteOrderBtn`)
- **Trigger**: When admin clicks "Delete" button in order details modal
- **Action**: Before deleting the order, all order items are automatically restocked
- **Backend**: `OrderDashboardViewSet.perform_destroy()` method
- **Stock Restoration**: 
  - For variant-based items: Adds quantity back to `variant.stock_quantity`
  - For product-based items: Adds quantity back to `product.stock_quantity`

#### Bulk Order Deletion (`<option value="delete">Delete Selected</option>`)
- **Trigger**: When admin selects multiple orders and chooses "Delete Selected"
- **Action**: Before deleting orders, all items from all selected orders are automatically restocked
- **Backend**: `OrderDashboardViewSet.bulk_action()` method with `action='delete'`
- **Stock Restoration**: Same logic as individual deletion, applied to all selected orders

### 2. **Order Status Change Stock Management**

#### Status Change to "Cancelled" (`changeStatusBtn`)
- **Trigger**: When order status is changed to "cancelled"
- **Action**: All order items are automatically restocked
- **Logic**: `should_restock_status()` helper function identifies cancellation statuses

#### Status Change from "Cancelled" to Active Statuses
- **Trigger**: When order status is changed from "cancelled" to any active status ("pending", "confirmed", "processing", "shipped", "delivered")
- **Action**: Stock is automatically reduced for all order items
- **Logic**: `should_reduce_stock_status()` helper function identifies active statuses

## Implementation Details

### Backend Changes

#### Helper Functions (in `dashboard/views.py`)
```python
def restock_order_items(order):
    """Restore stock for all items in an order"""
    
def reduce_order_stock(order):
    """Reduce stock for all items in an order"""
    
def should_restock_status(status):
    """Check if a status change should trigger restocking"""
    return status.lower() in ['cancelled', 'returned', 'partially_returned']
    
def should_reduce_stock_status(status):
    """Check if a status change should trigger stock reduction"""
    return status.lower() in ['pending', 'confirmed', 'processing', 'shipped', 'delivered']
```

#### Updated Methods

1. **`OrderDashboardViewSet.perform_destroy()`**
   - Added stock restocking before order deletion
   - Uses `@transaction.atomic` for data consistency

2. **`OrderDashboardViewSet.bulk_action()`**
   - Added stock management for both deletion and status updates
   - Handles stock restoration for deletions
   - Handles stock changes for status transitions

3. **`OrderDashboardViewSet.update_status()`**
   - Added `@transaction.atomic` decorator
   - Compares old vs new status to determine stock action
   - Automatically handles stock reduction/restoration based on status transition

### Frontend Changes

#### Updated Success Messages
- Delete operations now show "deleted successfully and stock has been restored"
- Status updates show backend-provided messages that include stock management info
- Bulk operations display backend success messages with stock management details

## Stock Management Logic

### When Stock is Restocked (Added Back)
1. **Order Deletion**: Always restocks, regardless of current status
2. **Status Change TO**: `cancelled`, `returned`, `partially_returned`
3. **Status Transition**: From active status (pending, confirmed, etc.) TO cancelled

### When Stock is Reduced (Subtracted)
1. **Status Transition**: From cancelled TO active status (pending, confirmed, processing, shipped, delivered)

### Stock Management Rules
- **Variant-based items**: Stock changes applied to `ProductVariant.stock_quantity`
- **Product-based items**: Stock changes applied to `Product.stock_quantity`
- **Safety checks**: Warns if insufficient stock but doesn't block operations
- **Transaction safety**: All operations use database transactions

## Error Handling

### Backend
- Wrapped in try-catch blocks with detailed logging
- Database transactions ensure data consistency
- Continues with operation even if stock management fails (with logging)

### Frontend
- Uses existing error handling mechanisms
- Shows detailed success messages including stock management status
- Maintains user experience with proper modal cleanup

## Testing the Implementation

### Test Cases

1. **Delete Order with Items**
   - Create order with items that have stock
   - Note current stock levels
   - Delete order via "Delete" button
   - Verify stock levels increased by order quantities

2. **Bulk Delete Orders**
   - Select multiple orders with items
   - Use "Delete Selected" bulk action
   - Verify all order items were restocked

3. **Cancel Order**
   - Change order status from "pending" to "cancelled"
   - Verify stock was restored

4. **Reactivate Cancelled Order**
   - Change order status from "cancelled" to "confirmed"
   - Verify stock was reduced again

5. **Status Changes Between Active States**
   - Change from "pending" to "shipped" (no stock change)
   - Change from "shipped" to "delivered" (no stock change)

## Console Logging

The implementation includes detailed console logging for debugging:
- Stock operations are logged with quantities and SKUs
- Status transitions are logged with old/new status
- Error conditions are logged with details

## Backward Compatibility

- All existing functionality remains unchanged
- No breaking changes to existing APIs
- Frontend calls work exactly as before
- Additional stock management is transparent to users

## Security Considerations

- All operations require admin permissions
- CSRF protection maintained
- Database transactions prevent partial operations
- Stock changes are logged in admin activity