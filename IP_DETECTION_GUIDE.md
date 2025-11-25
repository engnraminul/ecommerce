# Public IP Address Detection for Orders

## Overview

The ecommerce system has been enhanced to capture real public IP addresses when customers place orders, instead of just local/private IPs like `127.0.0.1`. This is crucial for:

- **Fraud Detection**: Track orders from specific geographical locations
- **Security**: Identify and block suspicious IP addresses
- **Analytics**: Better understand customer geographical distribution
- **Order Management**: Associate orders with real customer locations

## What Changed

### 1. Enhanced IP Detection (`orders/utils.py`)

The `get_client_ip()` function now includes:

- **Public IP Detection**: When a private/local IP is detected, it automatically fetches the public IP
- **Multiple Service Fallbacks**: Uses multiple external services for reliability
- **Caching**: Caches public IP for 5 minutes to avoid excessive API calls
- **Settings Integration**: Controlled by Django settings

### 2. Order Creation Enhancement

When customers place orders, the system now:

- Captures the real public IP address of the customer
- Stores it in the `Order.customer_ip` field
- Uses this IP for fraud detection and blocking checks

### 3. Configuration Setting

Added new Django setting in `settings.py`:

```python
# IP Detection Settings
FORCE_PUBLIC_IP_DETECTION = config('FORCE_PUBLIC_IP_DETECTION', default=True, cast=bool)
```

## Usage

### For Development

During development, you can control IP detection behavior:

```python
# In your .env file or environment variables
FORCE_PUBLIC_IP_DETECTION=True   # Capture public IP (recommended)
FORCE_PUBLIC_IP_DETECTION=False  # Use local IP (for testing)
```

### For Production

In production, keep `FORCE_PUBLIC_IP_DETECTION=True` to capture real customer IPs.

### Manual Usage

You can also use the enhanced function directly in your code:

```python
from orders.utils import get_client_ip

# Use setting-controlled behavior
customer_ip = get_client_ip(request)

# Force public IP detection
customer_ip = get_client_ip(request, force_public=True)

# Force local IP (bypass public detection)
customer_ip = get_client_ip(request, force_public=False)
```

## External Services Used

The system uses these reliable services to detect public IP:

1. `https://ifconfig.co/ip`
2. `https://ipinfo.io/ip`
3. `https://api.ipify.org`
4. `https://checkip.amazonaws.com`

If all services fail, it falls back to the detected local IP.

## Benefits

1. **Real Customer Tracking**: Orders now contain actual customer IP addresses
2. **Better Fraud Detection**: Can identify patterns and block suspicious IPs
3. **Geographical Analytics**: Understand where your customers are located
4. **Security Enhancement**: Better protection against fraudulent orders
5. **Reliable Service**: Multiple fallback services ensure high availability

## Technical Details

### IP Address Processing Order

1. Check standard proxy headers (`X-Forwarded-For`, `X-Real-IP`, etc.)
2. If a public IP is found in headers, use it
3. If only private/local IP is found and `FORCE_PUBLIC_IP_DETECTION=True`:
   - Query external services for public IP
   - Cache result for 5 minutes
   - Fall back to local IP if all services fail

### Caching Strategy

- Public IP is cached for 5 minutes to reduce API calls
- Cache key: `'public_ip'`
- Automatic cache invalidation after timeout

### Error Handling

- Graceful degradation if external services are unavailable
- Comprehensive logging for debugging
- Always returns a valid IP address (falls back to `127.0.0.1`)

## Testing

The system includes a test script to verify functionality:

```bash
python test_ip_detection.py
```

This will test:
- Public IP detection
- Request IP processing
- Proxy header handling
- Setting behavior

## Security Considerations

1. **External API Calls**: The system makes outbound HTTP requests to detect public IP
2. **Rate Limiting**: Caching prevents excessive API calls
3. **Privacy**: Only IP addresses are collected, no additional data
4. **Fallback**: Always works even if external services are down

## Monitoring

Consider monitoring:
- Success rate of public IP detection
- Response times from external services
- Cache hit rates
- Failed detection attempts

## Troubleshooting

### Common Issues

1. **Always getting 127.0.0.1**: Check `FORCE_PUBLIC_IP_DETECTION` setting
2. **Slow order creation**: External IP services might be slow (cached after first call)
3. **No public IP detected**: All external services might be down (check logs)

### Debug Logging

Enable debug logging to see IP detection process:

```python
LOGGING = {
    'loggers': {
        'orders.utils': {
            'level': 'DEBUG',
        },
    },
}
```

This will show detailed information about IP detection attempts.