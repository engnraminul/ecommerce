"""
Meta Conversions API (CAPI) Service for Server-Side Event Tracking
This service handles sending events directly to Facebook from the server
for better tracking accuracy and iOS 14.5+ compatibility.
"""

import hashlib
import hmac
import time
import json
import requests
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.http import HttpRequest
import logging

logger = logging.getLogger(__name__)


class MetaConversionsAPI:
    """
    Meta Conversions API service for sending server-side events to Facebook.
    """
    
    def __init__(self, pixel_id: str, access_token: str):
        self.pixel_id = pixel_id
        self.access_token = access_token
        self.api_url = f"https://graph.facebook.com/v18.0/{pixel_id}/events"
        
    def _hash_data(self, data: str) -> str:
        """Hash sensitive data with SHA256"""
        if not data:
            return None
        return hashlib.sha256(data.lower().strip().encode()).hexdigest()
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _get_user_agent(self, request: HttpRequest) -> str:
        """Extract user agent from request"""
        return request.META.get('HTTP_USER_AGENT', '')
    
    def _create_user_data(self, request: HttpRequest, email: str = None, phone: str = None, 
                         first_name: str = None, last_name: str = None, 
                         city: str = None, state: str = None, country: str = None, 
                         zip_code: str = None) -> Dict:
        """Create user data payload for CAPI"""
        user_data = {
            'client_ip_address': self._get_client_ip(request),
            'client_user_agent': self._get_user_agent(request),
        }
        
        # Add hashed PII data
        if email:
            user_data['em'] = self._hash_data(email)
        if phone:
            # Remove non-numeric characters and hash
            clean_phone = ''.join(filter(str.isdigit, phone))
            user_data['ph'] = self._hash_data(clean_phone)
        if first_name:
            user_data['fn'] = self._hash_data(first_name)
        if last_name:
            user_data['ln'] = self._hash_data(last_name)
        if city:
            user_data['ct'] = self._hash_data(city)
        if state:
            user_data['st'] = self._hash_data(state)
        if country:
            user_data['country'] = self._hash_data(country)
        if zip_code:
            user_data['zp'] = self._hash_data(zip_code)
            
        # Add Facebook Click ID if available
        fbp = request.COOKIES.get('_fbp')
        if fbp:
            user_data['fbp'] = fbp
            
        fbc = request.COOKIES.get('_fbc')
        if fbc:
            user_data['fbc'] = fbc
        
        return user_data
    
    def _create_custom_data(self, **kwargs) -> Dict:
        """Create custom data payload"""
        custom_data = {}
        
        # Standard e-commerce fields
        if 'currency' in kwargs:
            custom_data['currency'] = kwargs['currency']
        if 'value' in kwargs:
            custom_data['value'] = float(kwargs['value'])
        if 'content_ids' in kwargs:
            custom_data['content_ids'] = kwargs['content_ids']
        if 'content_type' in kwargs:
            custom_data['content_type'] = kwargs['content_type']
        if 'content_name' in kwargs:
            custom_data['content_name'] = kwargs['content_name']
        if 'content_category' in kwargs:
            custom_data['content_category'] = kwargs['content_category']
        if 'num_items' in kwargs:
            custom_data['num_items'] = int(kwargs['num_items'])
        if 'contents' in kwargs:
            custom_data['contents'] = kwargs['contents']
        
        # Add any additional custom parameters
        for key, value in kwargs.items():
            if key not in custom_data and key not in ['currency', 'value', 'content_ids', 
                                                     'content_type', 'content_name', 
                                                     'content_category', 'num_items', 'contents']:
                custom_data[key] = value
        
        return custom_data
    
    def send_event(self, event_name: str, request: HttpRequest, 
                   email: str = None, phone: str = None, 
                   first_name: str = None, last_name: str = None,
                   city: str = None, state: str = None, country: str = None,
                   zip_code: str = None, custom_data: Dict = None,
                   event_id: str = None, **kwargs) -> bool:
        """
        Send a single event to Meta Conversions API
        
        Args:
            event_name: Facebook event name (Purchase, AddToCart, etc.)
            request: Django HttpRequest object
            email: User email
            phone: User phone number
            first_name: User first name
            last_name: User last name
            city: User city
            state: User state
            country: User country
            zip_code: User zip code
            custom_data: Additional custom data dictionary
            event_id: Unique event ID for deduplication
            **kwargs: Additional custom data fields
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create user data
            user_data = self._create_user_data(
                request, email, phone, first_name, last_name,
                city, state, country, zip_code
            )
            
            # Create custom data
            if custom_data:
                kwargs.update(custom_data)
            event_custom_data = self._create_custom_data(**kwargs)
            
            # Create event payload
            event_data = {
                'event_name': event_name,
                'event_time': int(time.time()),
                'action_source': 'website',
                'event_source_url': request.build_absolute_uri(),
                'user_data': user_data,
            }
            
            if event_custom_data:
                event_data['custom_data'] = event_custom_data
            
            if event_id:
                event_data['event_id'] = event_id
            
            # Create API payload
            payload = {
                'data': [event_data],
                'access_token': self.access_token,
            }
            
            # Send to Facebook
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('events_received', 0) > 0:
                    logger.info(f"Successfully sent {event_name} event to Meta CAPI")
                    return True
                else:
                    logger.error(f"Meta CAPI error: {result}")
                    return False
            else:
                logger.error(f"Meta CAPI HTTP error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Meta CAPI exception: {str(e)}")
            return False
    
    def send_purchase_event(self, request: HttpRequest, order_data: Dict,
                           user_data: Dict = None, event_id: str = None) -> bool:
        """
        Send a purchase event to Meta CAPI
        
        Args:
            request: Django HttpRequest object
            order_data: Dictionary containing order information
            user_data: Dictionary containing user information
            event_id: Unique event ID for deduplication
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract order information
            currency = order_data.get('currency', 'BDT')
            value = order_data.get('total_amount', 0)
            order_id = order_data.get('order_id', '')
            
            # Prepare content data for products
            contents = []
            content_ids = []
            
            if 'items' in order_data:
                for item in order_data['items']:
                    content_ids.append(str(item.get('product_id', '')))
                    contents.append({
                        'id': str(item.get('product_id', '')),
                        'quantity': item.get('quantity', 1),
                        'item_price': float(item.get('price', 0))
                    })
            
            # Prepare custom data
            custom_data = {
                'currency': currency,
                'value': value,
                'content_ids': content_ids,
                'content_type': 'product',
                'num_items': len(contents),
                'contents': contents,
                'order_id': order_id,
            }
            
            # Extract user data
            email = user_data.get('email') if user_data else None
            phone = user_data.get('phone') if user_data else None
            first_name = user_data.get('first_name') if user_data else None
            last_name = user_data.get('last_name') if user_data else None
            city = user_data.get('city') if user_data else None
            state = user_data.get('state') if user_data else None
            country = user_data.get('country', 'BD') if user_data else 'BD'
            zip_code = user_data.get('zip_code') if user_data else None
            
            return self.send_event(
                'Purchase',
                request,
                email=email,
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                city=city,
                state=state,
                country=country,
                zip_code=zip_code,
                custom_data=custom_data,
                event_id=event_id
            )
            
        except Exception as e:
            logger.error(f"Failed to send purchase event: {str(e)}")
            return False
    
    def send_add_to_cart_event(self, request: HttpRequest, product_data: Dict,
                              user_data: Dict = None, event_id: str = None) -> bool:
        """Send AddToCart event to Meta CAPI"""
        try:
            custom_data = {
                'currency': product_data.get('currency', 'BDT'),
                'value': product_data.get('price', 0),
                'content_ids': [str(product_data.get('product_id', ''))],
                'content_type': 'product',
                'content_name': product_data.get('product_name', ''),
                'content_category': product_data.get('category', ''),
            }
            
            email = user_data.get('email') if user_data else None
            phone = user_data.get('phone') if user_data else None
            
            return self.send_event(
                'AddToCart',
                request,
                email=email,
                phone=phone,
                custom_data=custom_data,
                event_id=event_id
            )
            
        except Exception as e:
            logger.error(f"Failed to send AddToCart event: {str(e)}")
            return False
    
    def send_initiate_checkout_event(self, request: HttpRequest, cart_data: Dict,
                                   user_data: Dict = None, event_id: str = None) -> bool:
        """Send InitiateCheckout event to Meta CAPI"""
        try:
            contents = []
            content_ids = []
            total_value = 0
            
            for item in cart_data.get('items', []):
                content_ids.append(str(item.get('product_id', '')))
                contents.append({
                    'id': str(item.get('product_id', '')),
                    'quantity': item.get('quantity', 1),
                    'item_price': float(item.get('price', 0))
                })
                total_value += float(item.get('price', 0)) * item.get('quantity', 1)
            
            custom_data = {
                'currency': cart_data.get('currency', 'BDT'),
                'value': total_value,
                'content_ids': content_ids,
                'content_type': 'product',
                'num_items': len(contents),
                'contents': contents,
            }
            
            email = user_data.get('email') if user_data else None
            phone = user_data.get('phone') if user_data else None
            
            return self.send_event(
                'InitiateCheckout',
                request,
                email=email,
                phone=phone,
                custom_data=custom_data,
                event_id=event_id
            )
            
        except Exception as e:
            logger.error(f"Failed to send InitiateCheckout event: {str(e)}")
            return False


# Helper function to get Meta CAPI instance
def get_meta_capi_instance():
    """Get configured Meta CAPI instance"""
    try:
        from settings.models import IntegrationSettings
        
        settings = IntegrationSettings.get_active_settings()
        if not settings or not settings.meta_capi_enabled:
            return None
        
        if not settings.meta_pixel_id or not settings.meta_access_token:
            logger.warning("Meta CAPI enabled but Pixel ID or Access Token missing")
            return None
        
        return MetaConversionsAPI(settings.meta_pixel_id, settings.meta_access_token)
        
    except Exception as e:
        logger.error(f"Failed to initialize Meta CAPI: {str(e)}")
        return None


# Helper functions for common events
def send_purchase_event(request: HttpRequest, order_data: Dict, user_data: Dict = None):
    """Helper function to send purchase event"""
    capi = get_meta_capi_instance()
    if capi:
        event_id = f"purchase_{order_data.get('order_id', '')}_{int(time.time())}"
        return capi.send_purchase_event(request, order_data, user_data, event_id)
    return False


def send_add_to_cart_event(request: HttpRequest, product_data: Dict, user_data: Dict = None):
    """Helper function to send add to cart event"""
    capi = get_meta_capi_instance()
    if capi:
        event_id = f"add_to_cart_{product_data.get('product_id', '')}_{int(time.time())}"
        return capi.send_add_to_cart_event(request, product_data, user_data, event_id)
    return False


def send_initiate_checkout_event(request: HttpRequest, cart_data: Dict, user_data: Dict = None):
    """Helper function to send initiate checkout event"""
    capi = get_meta_capi_instance()
    if capi:
        event_id = f"initiate_checkout_{int(time.time())}"
        return capi.send_initiate_checkout_event(request, cart_data, user_data, event_id)
    return False