import requests
import json
import logging
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.conf import settings
from .models import Curier, SiteSettings

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


# ===== DELIVERY DATE CALCULATION UTILITIES =====

class DeliveryCalculator:
    """
    A utility class for calculating estimated delivery dates based on
    order placement time, custom settings, and delivery areas.
    """
    
    def __init__(self):
        self.settings = SiteSettings.get_active_settings()
        # Bangladesh Standard Time is UTC+6
        self.bst_offset = timedelta(hours=6)
    
    def get_bangladesh_now(self):
        """Get current datetime in Bangladesh Standard Time (UTC+6)."""
        utc_now = timezone.now()
        # Convert UTC to Bangladesh time (UTC+6)
        if timezone.is_aware(utc_now):
            # Convert to naive UTC, then add BST offset
            utc_naive = utc_now.replace(tzinfo=None)
            bst_naive = utc_naive + self.bst_offset
        else:
            # Already naive, assume it's UTC and add offset
            bst_naive = utc_now + self.bst_offset
        
        return bst_naive
    
    def get_today_date(self):
        """
        Get the effective 'today' date considering custom today date setting.
        Returns either the custom date (if set) or current date in BST.
        """
        if self.settings and self.settings.custom_today_date:
            return self.settings.custom_today_date
        return self.get_bangladesh_now().date()
    
    def get_current_time(self):
        """Get current time in Bangladesh Standard Time."""
        return self.get_bangladesh_now().time()
    
    def get_cutoff_time(self):
        """Get the daily cutoff time for order processing."""
        if self.settings and self.settings.delivery_cutoff_time:
            return self.settings.delivery_cutoff_time
        return datetime.strptime("16:00", "%H:%M").time()  # Default 4 PM
    
    def is_after_cutoff(self, order_time=None):
        """
        Check if the given time (or current time) is after the cutoff time.
        
        Args:
            order_time: Time to check. If None, uses current time.
        
        Returns:
            bool: True if after cutoff time, False otherwise.
        """
        if order_time is None:
            order_time = self.get_current_time()
        
        cutoff = self.get_cutoff_time()
        return order_time > cutoff
    
    def get_processing_start_date(self, order_time=None):
        """
        Get the date when order processing will start based on order time.
        
        Args:
            order_time: Time when order was placed. If None, uses current time.
        
        Returns:
            date: The date when order processing starts.
        """
        today = self.get_today_date()
        
        if self.is_after_cutoff(order_time):
            # Order placed after cutoff, processing starts day after tomorrow
            return today + timedelta(days=2)
        else:
            # Order placed before cutoff, processing starts tomorrow
            return today + timedelta(days=1)
    
    def get_delivery_dates(self, area='dhaka', order_time=None):
        """
        Calculate estimated delivery date range for the given area.
        
        Args:
            area: 'dhaka' or 'outside' for delivery area
            order_time: Time when order was placed. If None, uses current time.
        
        Returns:
            dict: Contains 'min_date', 'max_date', 'area_label' and 'days_range'
        """
        processing_start = self.get_processing_start_date(order_time)
        
        if area.lower() == 'dhaka':
            min_days = self.settings.dhaka_delivery_days_min if self.settings else 1
            max_days = self.settings.dhaka_delivery_days_max if self.settings else 2
            area_label = self.settings.delivery_area_dhaka_label if self.settings else "Inside Dhaka City"
        else:
            min_days = self.settings.outside_dhaka_delivery_days_min if self.settings else 1
            max_days = self.settings.outside_dhaka_delivery_days_max if self.settings else 3
            area_label = self.settings.delivery_area_outside_label if self.settings else "Outside Dhaka City"
        
        # Delivery starts from processing date itself, not after processing
        # For min_days=1, delivery starts on processing day
        # For min_days=2, delivery starts one day after processing
        min_date = processing_start + timedelta(days=min_days - 1)
        max_date = processing_start + timedelta(days=max_days - 1)
        
        return {
            'min_date': min_date,
            'max_date': max_date,
            'area_label': area_label,
            'days_range': f"{min_days}-{max_days}" if min_days != max_days else str(min_days),
            'processing_start': processing_start
        }
    
    def get_all_delivery_estimates(self, order_time=None):
        """
        Get delivery estimates for both Dhaka and outside Dhaka areas.
        
        Args:
            order_time: Time when order was placed. If None, uses current time.
        
        Returns:
            dict: Contains delivery estimates for both areas
        """
        return {
            'dhaka': self.get_delivery_dates('dhaka', order_time),
            'outside': self.get_delivery_dates('outside', order_time),
            'today_date': self.get_today_date(),
            'current_time': self.get_current_time(),
            'cutoff_time': self.get_cutoff_time(),
            'is_after_cutoff': self.is_after_cutoff(order_time),
        }
    
    def format_date_range(self, min_date, max_date):
        """
        Format date range for display.
        
        Args:
            min_date: Start date
            max_date: End date
        
        Returns:
            str: Formatted date range (e.g., "10-11 November" or "10 November")
        """
        if min_date == max_date:
            return min_date.strftime("%d %B")
        
        if min_date.month == max_date.month:
            return f"{min_date.strftime('%d')}-{max_date.strftime('%d')} {min_date.strftime('%B')}"
        else:
            return f"{min_date.strftime('%d %B')} - {max_date.strftime('%d %B')}"
    
    def get_formatted_delivery_info(self, area='dhaka', order_time=None):
        """
        Get formatted delivery information ready for display.
        
        Args:
            area: 'dhaka' or 'outside' for delivery area
            order_time: Time when order was placed. If None, uses current time.
        
        Returns:
            dict: Formatted delivery information
        """
        delivery_data = self.get_delivery_dates(area, order_time)
        
        return {
            'area_label': delivery_data['area_label'],
            'date_range': self.format_date_range(
                delivery_data['min_date'], 
                delivery_data['max_date']
            ),
            'days_range': delivery_data['days_range'],
            'min_date': delivery_data['min_date'],
            'max_date': delivery_data['max_date'],
            'processing_start': delivery_data['processing_start']
        }


def get_delivery_estimates():
    """
    Convenience function to get delivery estimates for both areas.
    
    Returns:
        dict: Contains delivery estimates for both Dhaka and outside Dhaka
    """
    calculator = DeliveryCalculator()
    return calculator.get_all_delivery_estimates()


def get_formatted_delivery_estimates():
    """
    Get delivery estimates formatted for display in templates.
    
    Returns:
        dict: Formatted delivery estimates for both areas
    """
    calculator = DeliveryCalculator()
    
    return {
        'dhaka': calculator.get_formatted_delivery_info('dhaka'),
        'outside': calculator.get_formatted_delivery_info('outside'),
        'settings': {
            'today_date': calculator.get_today_date(),
            'current_time': calculator.get_current_time().strftime('%I:%M %p'),
            'cutoff_time': calculator.get_cutoff_time().strftime('%I:%M %p'),
            'is_after_cutoff': calculator.is_after_cutoff(),
            'custom_date_set': bool(calculator.settings and calculator.settings.custom_today_date)
        }
    }