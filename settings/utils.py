import requests
import json
import logging
from django.conf import settings
from .models import Curier

logger = logging.getLogger(__name__)

def get_active_curier():
    """Get the SteadFast curier configuration from the database"""
    try:
        # First, try to get a curier with name 'steadFast'
        steadfast = Curier.objects.filter(name='steadFast').first()
        if steadfast:
            # Debug log the found SteadFast configuration
            print(f"DEBUG - Using SteadFast configuration: name={steadfast.name}, api_url={steadfast.api_url}")
            return steadfast
        
        # If no 'steadFast' curier exists, fall back to any active curier
        active_curier = Curier.objects.filter(is_active=True).first()
        if active_curier:
            print(f"DEBUG - No 'steadFast' entry found, using active curier: name={active_curier.name}, api_url={active_curier.api_url}")
        else:
            print("DEBUG - No curier configuration found!")
            
        return active_curier
    except Exception as e:
        logger.error(f"Failed to retrieve active curier configuration: {str(e)}")
        print(f"DEBUG - Error retrieving curier config: {str(e)}")
        return None

def send_order_to_curier(order):
    """
    Send order data to the curier API
    Returns tuple: (success, result_data)
    """
    try:
        curier = get_active_curier()
        if not curier:
            logger.error("No active curier configuration found")
            return False, {"error": "No active curier configuration found"}
        
        # Get shipping address
        shipping_address = order.shipping_address
        if not shipping_address:
            logger.error(f"No shipping address found for order {order.id}")
            return False, {"error": "No shipping address found for this order"}
        
        # Get order items to build item description
        items = order.items.all()
        item_descriptions = []
        for item in items:
            sku = item.variant.sku if item.variant and hasattr(item.variant, 'sku') and item.variant.sku else item.product_sku
            item_descriptions.append(f"{item.quantity}x {item.product_name} {sku}")
        
        item_description = ", ".join(item_descriptions) if item_descriptions else "Order items"
        
        # Build request payload for SteadFast API
        # Make sure to follow exactly what's in the API documentation
        payload = {
            "invoice": str(order.order_number),
            "recipient_name": shipping_address.full_name,
            "recipient_phone": shipping_address.phone or "",
            "recipient_address": shipping_address.full_address,
            "cod_amount": str(order.total_amount),
            "item_description": item_description,
            "status": "in_review",
            "note": order.customer_notes or ""
        }
        
        # Only add optional fields if they have values
        if shipping_address.email or order.customer_email:
            payload["recipient_email"] = shipping_address.email or order.customer_email
            
        if shipping_address.phone:
            payload["alternative_phone"] = shipping_address.phone
        
        # Log the payload for debugging
        logger.info(f"Sending payload to SteadFast API: {json.dumps(payload)}")
        
        # Build headers for SteadFast API according to documentation
        # Note: API headers are case-sensitive
        headers = {
            "api-key": curier.api_key,
            "secret-key": curier.secret_key,
            "Content-Type": "application/json",
            "Accept": "application/json"  # Add Accept header
        }
        
        # Log the headers (excluding secret-key for security)
        safe_headers = headers.copy()
        if 'secret-key' in safe_headers:
            safe_headers['secret-key'] = '***REDACTED***'
        logger.info(f"Using headers: {safe_headers}")
        
        # Print full headers for debugging (with sensitive data masked)
        print(f"DEBUG - API Headers: {safe_headers}")
        
        # Serialize the payload to JSON
        json_payload = json.dumps(payload)
        print(f"DEBUG - API URL: {curier.api_url}")
        print(f"DEBUG - Request Payload: {json_payload}")
        
        # Make API request
        response = requests.post(
            curier.api_url,
            headers=headers,
            data=json_payload
        )
        
        # Check response with detailed debugging
        logger.info(f"Received response with status code: {response.status_code}")
        print(f"DEBUG - Response Status Code: {response.status_code}")
        print(f"DEBUG - Response Headers: {dict(response.headers)}")
        print(f"DEBUG - Response Content: {response.text}")
        
        logger.info(f"Response content: {response.text[:500]}...")  # Log first 500 chars for debugging
        
        if response.status_code >= 200 and response.status_code < 300:
            try:
                result = response.json()
                logger.info(f"Successfully sent order {order.id} to SteadFast curier service")
                
                # Check for SteadFast specific success indicators
                if result.get('status') == 200 or result.get('message') == 'Consignment has been created successfully.':
                    return True, result
                else:
                    logger.warning(f"SteadFast API returned success status code but unexpected content: {result}")
                    return True, result  # Still return as success since the HTTP status was ok
                    
            except json.JSONDecodeError:
                logger.error(f"Failed to decode SteadFast API response: {response.text}")
                return False, {"error": "Invalid response from SteadFast curier service"}
        else:
            logger.error(f"Failed to send order to SteadFast curier: {response.status_code} - {response.text}")
            return False, {"error": f"Failed with status {response.status_code}"}
    
    except requests.RequestException as e:
        # Handle specific request-related exceptions
        logger.error(f"Request exception while sending order to SteadFast: {str(e)}")
        return False, {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        # Handle other exceptions with detailed traceback
        import traceback
        logger.error(f"Exception while sending order to SteadFast: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False, {"error": str(e)}