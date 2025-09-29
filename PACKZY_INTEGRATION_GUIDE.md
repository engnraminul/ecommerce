# Packzy Delivery Status Integration

This implementation provides automatic delivery status synchronization between your e-commerce platform and the Packzy courier service.

## Features

### 1. Automatic Status Checking
- When an order status is changed to "Shipped" and the order has a `curier_id`, the system automatically checks the Packzy API for delivery status
- If the Packzy API reports the order as "delivered", the order status is automatically updated to "delivered"

### 2. Manual Delivery Status Check
- A "Check Delivery Status" button is available in the orders management interface
- Clicking this button checks all shipped orders with courier IDs against the Packzy API
- Shows a summary of how many orders were checked and updated

### 3. Background Status Monitoring
- A Django management command is available to run periodic checks
- Can be scheduled using cron jobs or task schedulers

## API Integration Details

### Packzy API Endpoint
```
GET https://portal.packzy.com/api/v1/status_by_cid/{courier_id}
```

### Expected Response Format
The integration expects the Packzy API to return JSON with a `status` field:
```json
{
  "status": "delivered"
}
```

### Status Mapping
- When Packzy status is `"delivered"` (case-insensitive), the order status is updated to `"delivered"`
- Other statuses are stored in the `curier_status` field for tracking purposes

## Usage Instructions

### Frontend Interface
1. Navigate to the Orders Management page (`/mb-admin/orders/`)
2. Use the "Check Delivery Status" button to manually check all shipped orders
3. The system will show a progress indicator and summary of results
4. Orders that are found to be delivered will be automatically updated

### Management Command
Run the delivery status check command:

```bash
# Basic usage - check up to 50 orders shipped more than 1 hour ago
python manage.py check_delivery_status

# Check more orders
python manage.py check_delivery_status --max-orders 100

# Only check orders shipped more than 6 hours ago
python manage.py check_delivery_status --older-than-hours 6

# Dry run - see what would be updated without making changes
python manage.py check_delivery_status --dry-run

# Combine options
python manage.py check_delivery_status --max-orders 200 --older-than-hours 2 --dry-run
```

### Scheduling Automatic Checks
Add to your crontab to run every 30 minutes:
```bash
# Run every 30 minutes during business hours (9 AM to 9 PM)
*/30 9-21 * * * cd /path/to/your/project && python manage.py check_delivery_status
```

Or run every hour:
```bash
# Run every hour
0 * * * * cd /path/to/your/project && python manage.py check_delivery_status
```

## Implementation Details

### Backend Changes
- **dashboard/views.py**: Enhanced `update_status` method to trigger delivery status check when status changes to "shipped"
- **dashboard/views.py**: Added `check_packzy_delivery_status` method for individual order checking
- **dashboard/views.py**: Added `check_all_shipped_orders` API endpoint for bulk checking
- **orders/management/commands/check_delivery_status.py**: Management command for background processing

### Frontend Changes
- **orders.html**: Added "Check Delivery Status" button in the orders management interface
- **orders.html**: Added JavaScript function `checkAllShippedOrdersDeliveryStatus()` for API communication
- **orders.html**: Enhanced user feedback with SweetAlert2 notifications showing check results

### Database Fields Used
- `Order.curier_id`: Courier tracking ID provided by Packzy
- `Order.status`: Main order status (updated to "delivered" when Packzy confirms delivery)
- `Order.curier_status`: Tracks the latest status from courier API for reference

### Error Handling
- Network timeouts (30 seconds) for API requests
- HTTP error status handling
- Graceful degradation if Packzy API is unavailable
- Comprehensive logging for debugging

### Activity Logging
- All automatic status updates are logged in the `AdminActivity` model
- Manual checks via the interface are tracked
- Management command provides detailed output logs

## Configuration

### Required Dependencies
- `requests` library for HTTP API calls (already included in the implementation)

### Environment Considerations
- Ensure your server can make outbound HTTPS requests to `portal.packzy.com`
- Consider implementing rate limiting if checking large numbers of orders
- Monitor API response times and adjust timeout values if needed

## Troubleshooting

### Common Issues

1. **Orders not being checked automatically**
   - Verify the order has a `curier_id` value
   - Check that the order status was actually changed to "shipped"
   - Look for error messages in the console/logs

2. **Packzy API returning errors**
   - Verify the courier ID is valid in the Packzy system
   - Check if the Packzy API endpoint URL is correct
   - Ensure your server's IP is not blocked by Packzy

3. **Status not updating despite API success**
   - Check the exact status value returned by Packzy API
   - Verify case-insensitive matching (status comparison uses `.lower()`)
   - Review the order's current status in the database

### Debugging Steps
1. Enable Django debug mode to see detailed error messages
2. Check the browser console for JavaScript errors
3. Use the management command with `--dry-run` to test without making changes
4. Monitor server logs for API request/response details

## Future Enhancements

Potential improvements that could be added:
- Webhook support from Packzy for real-time updates
- Support for multiple courier services
- Email notifications when orders are automatically marked as delivered
- Dashboard analytics for delivery status trends
- Retry mechanism for failed API calls
- Rate limiting for API requests