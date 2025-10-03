# Stock Management System Documentation

## Overview

The Stock Management System is a comprehensive solution for managing product inventory in the ecommerce dashboard. It provides real-time stock tracking, bulk operations, alerts, and detailed reporting capabilities.

## Features

### 1. Stock Dashboard
- **Real-time Stock Overview**: View current stock levels for all products and variants
- **Stock Summary Cards**: 
  - Total Products
  - Low Stock Products 
  - Out of Stock Products
  - Total Stock Value
- **Advanced Filtering**: Filter by category, stock status, active/inactive products
- **Search Functionality**: Search by product name or SKU
- **Toggle Views**: Switch between product view and variant view

### 2. Individual Stock Adjustments
- **Quick Adjustments**: Increase or decrease stock for individual products/variants
- **Reason Tracking**: Add reasons for stock adjustments
- **Real-time Updates**: Immediate reflection of changes in the dashboard
- **Activity Logging**: All adjustments are logged for audit purposes

### 3. Bulk Stock Operations
- **Bulk Adjustments**: Adjust stock for multiple products simultaneously
- **Smart Selection**: 
  - Select all products
  - Select only low stock products
  - Custom selection with search
- **Preview Mode**: Preview changes before execution
- **Batch Processing**: Process multiple adjustments with detailed results

### 4. Stock Reports & Analytics
- **Low Stock Report**: Detailed report of products below threshold
- **Export Functionality**: Export stock data to CSV
- **Stock Value Calculation**: Calculate total inventory value
- **Status Tracking**: Monitor stock status (In Stock, Low Stock, Out of Stock)

### 5. Variant Management
- **Variant Stock Tracking**: Individual stock management for product variants
- **Variant-specific Adjustments**: Adjust stock for specific sizes, colors, etc.
- **Hierarchical View**: View variants within their parent products
- **Variant Filtering**: Filter and search specifically for variants

## Implementation Details

### Backend Components

#### Models
- **Product**: Main product model with stock tracking
- **ProductVariant**: Variant-specific stock management
- **StockMovement**: Audit trail for all stock changes (planned)
- **StockAlert**: Alert system for low stock notifications (planned)

#### ViewSets
- **StockDashboardViewSet**: Main API for product stock management
- **StockVariantDashboardViewSet**: API for variant stock management

#### Key API Endpoints
```
GET /dashboard/api/stock/ - List products with stock info
POST /dashboard/api/stock/{id}/adjust_stock/ - Adjust individual product stock
GET /dashboard/api/stock/stock_summary/ - Get stock summary statistics
POST /dashboard/api/stock/bulk_adjust/ - Bulk stock adjustments
GET /dashboard/api/stock/low_stock_report/ - Low stock report
GET /dashboard/api/stock/export_stock_report/ - Export stock report

GET /dashboard/api/stock-variants/ - List variants with stock info
POST /dashboard/api/stock-variants/{id}/adjust_stock/ - Adjust variant stock
```

### Frontend Components

#### Templates
- **stock.html**: Main stock management interface
- **Modals**: 
  - Individual stock adjustment modal
  - Bulk stock adjustment modal
  - Low stock report modal

#### JavaScript Features
- **Real-time Updates**: Dynamic loading and updating of stock data
- **Advanced Filtering**: Client-side and server-side filtering
- **Bulk Operations**: Comprehensive bulk adjustment interface
- **Export Functionality**: CSV export with current filters applied
- **Responsive Design**: Mobile-friendly interface

## Usage Guide

### Accessing Stock Management
1. Navigate to the dashboard
2. Click on the "Stock" tab in the sidebar
3. The stock management interface will load with current stock data

### Adjusting Individual Stock
1. Find the product in the stock table
2. Click the "Adjust" button
3. Select action (Increase/Decrease)
4. Enter quantity and reason
5. Save changes

### Bulk Stock Adjustments
1. Click "Bulk Adjust" button
2. Select products using checkboxes or smart selection buttons
3. Choose action and quantity
4. Preview changes
5. Execute bulk adjustment

### Generating Reports
1. **Low Stock Report**: Click "Low Stock Report" to view products below threshold
2. **Export CSV**: Click "Export CSV" to download current view as spreadsheet
3. **Filtering**: Apply filters before exporting for targeted reports

### Variant Management
1. Click "Toggle Variant View" to switch to variant management
2. View and adjust stock for individual variants
3. Use product-specific filtering to focus on specific products
4. Switch back to product view as needed

## Stock Status Indicators

### Status Types
- **In Stock**: Green badge - Product has sufficient stock
- **Low Stock**: Yellow badge - Stock is at or below threshold
- **Out of Stock**: Red badge - No stock available
- **Not Tracked**: Gray badge - Inventory tracking disabled

### Stock Calculations
- **Product Stock**: Direct stock quantity on product
- **Variant Stock**: Individual variant stock quantities
- **Total Variant Stock**: Sum of all variant stocks for a product
- **Stock Value**: Calculated using cost price × stock quantity

## Configuration

### Stock Thresholds
- Set `low_stock_threshold` on each product
- System automatically flags products below this threshold
- Used for alerts and reports

### Inventory Tracking
- Enable/disable per product using `track_inventory` field
- Only tracked products appear in stock management
- Non-tracked products assume unlimited stock

## Security & Permissions

### Access Control
- Requires admin/staff user authentication
- All operations logged with user information
- IP address and user agent tracking for audit

### Data Validation
- Positive quantity validation
- Sufficient stock checks for decreases
- Invalid operation prevention

## API Response Formats

### Stock Summary Response
```json
{
    "total_products": 25,
    "low_stock_products": 3,
    "out_of_stock_products": 1,
    "total_stock_value": 125000.50
}
```

### Stock Adjustment Response
```json
{
    "success": true,
    "new_stock": 15,
    "old_stock": 10,
    "action": "increase",
    "quantity": 5
}
```

### Bulk Adjustment Response
```json
{
    "success": true,
    "results": [
        {
            "product_id": 1,
            "success": true,
            "old_stock": 10,
            "new_stock": 15,
            "action": "increase",
            "quantity": 5
        }
    ],
    "summary": {
        "total": 10,
        "success": 9,
        "errors": 1
    }
}
```

## Best Practices

### Stock Management
1. **Regular Monitoring**: Check stock levels daily
2. **Threshold Setting**: Set appropriate low stock thresholds
3. **Bulk Operations**: Use for inventory adjustments after physical counts
4. **Documentation**: Always provide clear reasons for adjustments

### Performance
1. **Filtering**: Use filters to reduce data load on large inventories
2. **Pagination**: System handles pagination automatically
3. **Caching**: Summary data is calculated efficiently

### Data Integrity
1. **Audit Trail**: All stock movements are logged
2. **Validation**: System prevents invalid operations
3. **Backup**: Regular database backups recommended

## Troubleshooting

### Common Issues
1. **Stock Adjustment Fails**: Check permissions and stock availability
2. **Bulk Operations Timeout**: Reduce batch size or contact administrator
3. **Export Issues**: Ensure browser allows downloads
4. **Slow Loading**: Check network connection and server performance

### Error Messages
- "Insufficient stock": Attempting to decrease below available quantity
- "Quantity must be positive": Invalid quantity entered
- "Product not found": Product ID doesn't exist or access denied

## Future Enhancements

### Planned Features
1. **Stock Movement History**: Detailed audit trail with history view
2. **Automated Alerts**: Email/SMS notifications for low stock
3. **Barcode Scanning**: Quick stock adjustments via barcode
4. **Stock Forecasting**: Predict stock needs based on sales trends
5. **Multi-location Support**: Track stock across multiple warehouses
6. **Supplier Integration**: Automatic reorder suggestions

### API Improvements
1. **Webhook Support**: Real-time notifications for stock changes
2. **GraphQL Support**: More flexible data querying
3. **Rate Limiting**: API usage controls
4. **Batch Import**: CSV import for bulk stock updates

## Support

For technical support or feature requests, please contact the development team or refer to the main project documentation.

## Version History

- **v1.0**: Initial implementation with basic stock management
- **v1.1**: Added bulk operations and export functionality
- **v1.2**: Enhanced variant management and reporting

---

*This documentation is part of the MB Admin Dashboard system.*