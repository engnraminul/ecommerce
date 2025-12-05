# Packzy Fraud Checker API Integration Guide

## Overview
This integration connects your ecommerce system with Packzy's fraud checking API to verify customer phone numbers against their courier delivery history.

## API Details
- **Endpoint**: `https://portal.packzy.com/api/v1/fraud_check/{phone_number}`
- **Method**: GET
- **Headers Required**:
  - `api-key`: Your Packzy API key
  - `secret-key`: Your Packzy secret key

## Setup Instructions

### 1. Get API Credentials
1. Log in to your Packzy portal account
2. Navigate to API settings
3. Copy your API key and secret key

### 2. Configure Courier Settings
1. Go to Django Admin → Settings → Curiers
2. Add a new courier or edit existing one:
   - **Name**: Enter "SteadFast", "Packzy", or similar (case insensitive)
   - **API URL**: `https://portal.packzy.com/api/v1/fraud_check`
   - **API Key**: Your Packzy API key
   - **Secret Key**: Your Packzy secret key
   - **Is Active**: Check this box
3. Save the courier configuration

### 3. Test the Integration
1. Go to Django Admin
2. Navigate to "Test Fraud Checker API" (custom admin page)
3. Enter a phone number to test
4. Check the results

### 4. Use in Code
```python
from fraud_checker.services import PackzyFraudChecker

# Initialize service (automatically loads credentials)
fraud_checker = PackzyFraudChecker()

# Check fraud status
result = fraud_checker.check_fraud("01309055966")

if result['success']:
    print(f"Fraud Score: {result['fraud_score']}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Total Parcels: {result['total_parcels']}")
    print(f"Delivered: {result['total_delivered']}")
    print(f"Cancelled: {result['total_cancelled']}")
else:
    print(f"Error: {result['error']}")
```

## API Response Format
```json
{
    "success": true,
    "phone_number": "01309055966",
    "total_parcels": 10,
    "total_delivered": 5,
    "total_cancelled": 5,
    "total_fraud_reports": [],
    "fraud_score": 50,
    "risk_level": "MEDIUM",
    "risk_color": "warning"
}
```

## Fraud Scoring System
- **Score Range**: 0-100
- **Risk Levels**:
  - `MINIMAL` (0-19): Low risk customer
  - `LOW` (20-39): Slightly risky
  - `MEDIUM` (40-69): Moderate risk
  - `HIGH` (70-100): High risk customer

## Calculation Logic
- High cancellation rate (>50%): +30 points
- Medium cancellation rate (30-50%): +15 points
- Each fraud report: +20 points
- Maximum score: 100

## Management Commands

### Test Fraud Checker
```bash
python manage.py test_fraud_checker 01309055966
```

### Test with Mock Data
```bash
python manage.py test_fraud_checker 01309055966 --mock
```

## Troubleshooting

### Common Issues

1. **"API credentials not configured"**
   - Check that you have an active courier with name containing "steadfast" or "packzy"
   - Verify API key and secret key are entered correctly
   - Ensure the courier is marked as active

2. **"Connection error to fraud check API"**
   - Check internet connectivity
   - Verify the API endpoint is accessible
   - Check firewall settings

3. **"API call failed with status 401"**
   - Verify your API key and secret key are correct
   - Check if credentials have expired
   - Contact Packzy support for credential verification

4. **"API call returned empty response"**
   - The phone number may not exist in Packzy's system
   - Verify phone number format (should be 11 digits starting with 01)

### Debug Mode
Enable mock data for testing without API calls:
```python
fraud_checker = PackzyFraudChecker()
fraud_checker.USE_MOCK_DATA = True
result = fraud_checker.check_fraud("01309055966")
```

## Integration Points

### Combined Fraud Checker
The system supports multiple courier fraud checks:
```python
from fraud_checker.combined_service import CombinedFraudChecker

combined_checker = CombinedFraudChecker()
result = combined_checker.check_fraud_all_couriers("01309055966")

# Results include all couriers:
# - SteadFast (Packzy)
# - Pathao
# - RedX
```

### API Endpoint
The fraud checker is available via API:
- **URL**: `/fraud-checker/api/check/`
- **Method**: POST
- **Authentication**: Login required
- **Payload**: `{"phone_number": "01309055966"}`

## Maintenance

### Refreshing Credentials
If you update courier settings, the service will automatically load new credentials on the next request. For immediate refresh:
```python
fraud_checker.refresh_credentials()
```

### Monitoring
Check logs for API call status:
```python
import logging
logging.getLogger('fraud_checker.services').setLevel(logging.DEBUG)
```

## Security Notes
- API keys are stored securely in the database
- Credentials are loaded from active courier settings only
- Failed API calls are logged for monitoring
- No sensitive data is exposed in error messages