import requests
import logging
import time
from typing import Optional, Dict, Any
try:
    from django.core.cache import cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedxFraudChecker:
    """Service class to handle RedX API fraud checking"""
    
    LOGIN_URL = "https://api.redx.com.bd/v4/auth/login"
    CUSTOMER_STATS_URL = "https://redx.com.bd/api/redx_se/admin/parcel/customer-success-return-rate"
    TIMEOUT = 30  # seconds
    CACHE_KEY = 'redx_access_token'
    CACHE_MINUTES = 50
    
    # RedX credentials
    PHONE = "01777173040"
    PASSWORD = "redx@3065"
    USE_MOCK_DATA = False  # Set to True for testing with mock data
    
    # Simple in-memory cache fallback
    _memory_cache = {}
    _cache_timestamps = {}
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json, text/plain, */*',
        })
    
    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get value from cache with fallback to in-memory cache"""
        if CACHE_AVAILABLE:
            try:
                return cache.get(key)
            except Exception as e:
                logger.warning(f"Cache error: {e}, falling back to memory cache")
        
        # Fallback to in-memory cache
        if key in self._memory_cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if time.time() - timestamp < (self.CACHE_MINUTES * 60):
                return self._memory_cache[key]
            else:
                # Cache expired
                self._memory_cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
        
        return None
    
    def _set_cache(self, key: str, value: str) -> None:
        """Set value in cache with fallback to in-memory cache"""
        if CACHE_AVAILABLE:
            try:
                cache.set(key, value, self.CACHE_MINUTES * 60)
                return
            except Exception as e:
                logger.warning(f"Cache error: {e}, falling back to memory cache")
        
        # Fallback to in-memory cache
        self._memory_cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def _delete_from_cache(self, key: str) -> None:
        """Delete value from cache with fallback to in-memory cache"""
        if CACHE_AVAILABLE:
            try:
                cache.delete(key)
            except Exception as e:
                logger.warning(f"Cache error: {e}, falling back to memory cache")
        
        # Fallback to in-memory cache
        self._memory_cache.pop(key, None)
        self._cache_timestamps.pop(key, None)
    
    def check_fraud(self, phone_number: str) -> Dict[str, Any]:
        """
        Check fraud status for a phone number using RedX API
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            Dict with fraud check results
        """
        # Clean phone number
        phone_number = self._clean_phone_number(phone_number)
        
        if not phone_number:
            return {
                'success': False,
                'error': 'Invalid phone number provided',
                'courier': 'redx'
            }
        
        try:
            logger.info(f"Making RedX fraud check for {phone_number}")
            
            if self.USE_MOCK_DATA:
                logger.info("Using mock data for RedX testing")
                customer_data = self._get_mock_data(phone_number)
            else:
                # Step 1: Get access token
                access_token = self._get_access_token()
                if not access_token:
                    return {
                        'success': False,
                        'error': 'Failed to authenticate with RedX',
                        'courier': 'redx'
                    }
                
                # Step 2: Get customer delivery stats
                customer_data = self._get_customer_delivery_stats(phone_number, access_token)
                if customer_data is None:
                    return {
                        'success': False,
                        'error': 'Failed to retrieve customer data from RedX',
                        'courier': 'redx'
                    }
                
                # Handle API errors
                if 'error' in customer_data:
                    return {
                        'success': False,
                        'error': customer_data['error'],
                        'courier': 'redx'
                    }
            
            # Calculate fraud score and risk level
            fraud_score = self._calculate_fraud_score(customer_data)
            risk_level = self._get_risk_level(fraud_score)
            risk_color = self._get_risk_color(risk_level)
            
            return {
                'success': True,
                'courier': 'redx',
                'phone_number': phone_number,
                'total_parcels': int(customer_data.get('total', 0)) if customer_data.get('total') else 0,
                'total_delivered': int(customer_data.get('success', 0)) if customer_data.get('success') else 0,
                'total_cancelled': int(customer_data.get('cancel', 0)) if customer_data.get('cancel') else 0,
                'fraud_score': fraud_score,
                'risk_level': risk_level,
                'risk_color': risk_color,
            }
            
        except Exception as e:
            logger.error(f"RedX fraud check failed for {phone_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'courier': 'redx'
            }
    
    def _get_access_token(self) -> Optional[str]:
        """Get access token from cache or login to RedX"""
        # Try to get cached token first
        token = self._get_from_cache(self.CACHE_KEY)
        if token:
            logger.info("Using cached RedX access token")
            return token
        
        try:
            logger.info("Logging in to RedX API")
            
            response = self.session.post(
                self.LOGIN_URL,
                json={
                    'phone': f'88{self.PHONE}',
                    'password': self.PASSWORD,
                },
                timeout=self.TIMEOUT
            )
            
            logger.debug(f"RedX login response status: {response.status_code}")
            
            if not response.ok:
                logger.error(f"RedX login failed with status {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            access_token = data.get('data', {}).get('accessToken', '').strip()
            
            if not access_token:
                logger.error("No access token received from RedX")
                return None
            
            # Cache the token for 50 minutes
            self._set_cache(self.CACHE_KEY, access_token)
            
            logger.info("Successfully logged in to RedX and cached token")
            return access_token
            
        except Exception as e:
            logger.error(f"RedX login error: {str(e)}")
            return None
    
    def _get_customer_delivery_stats(self, phone_number: str, access_token: str) -> Optional[Dict[str, Any]]:
        """Get customer delivery statistics from RedX"""
        try:
            logger.info(f"Getting customer delivery stats for {phone_number}")
            
            # Update headers with authorization
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            
            url = f"{self.CUSTOMER_STATS_URL}?phoneNumber=88{phone_number}"
            
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.TIMEOUT
            )
            
            logger.debug(f"RedX customer stats response status: {response.status_code}")
            
            if response.status_code == 401:
                # Token expired, clear cache
                self._delete_from_cache(self.CACHE_KEY)
                return {'error': 'Access token expired or invalid. Please retry.', 'status': 401}
            
            if not response.ok:
                logger.error(f"RedX customer stats failed with status {response.status_code}: {response.text}")
                # Return threshold hit message for rate limiting or other errors
                return {
                    'success': 'Threshold hit, wait a minute',
                    'cancel': 'Threshold hit, wait a minute',
                    'total': 'Threshold hit, wait a minute',
                }
            
            data = response.json()
            customer_data = data.get('data', {})
            
            if not customer_data:
                logger.warning("No customer data found in RedX response")
                return {
                    'success': 0,
                    'cancel': 0,
                    'total': 0,
                }
            
            delivered_parcels = int(customer_data.get('deliveredParcels', 0))
            total_parcels = int(customer_data.get('totalParcels', 0))
            cancelled_parcels = total_parcels - delivered_parcels
            
            result = {
                'success': delivered_parcels,
                'cancel': cancelled_parcels,
                'total': total_parcels,
            }
            
            logger.info(f"RedX customer stats retrieved: {result}")
            return result
            
        except Exception as e:
            logger.error(f"RedX customer stats error: {str(e)}")
            return None
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean and validate phone number"""
        if not phone_number:
            return ""
        
        # Remove all non-digit characters
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Validate length (assuming Bangladeshi numbers)
        if len(cleaned) == 11 and cleaned.startswith('01'):
            return cleaned
        elif len(cleaned) == 13 and cleaned.startswith('880'):
            return cleaned[2:]  # Remove country code
        elif len(cleaned) == 14 and cleaned.startswith('+880'):
            return cleaned[4:]  # Remove country code with +
        
        return cleaned if len(cleaned) >= 10 else ""
    
    def _calculate_fraud_score(self, customer_data: Dict[str, Any]) -> int:
        """Calculate a simple fraud risk score based on the data"""
        # Handle threshold hit responses
        if isinstance(customer_data.get('total'), str):
            return 0  # Return neutral score for rate limited responses
        
        # Ensure numeric values by converting strings to integers
        try:
            total_parcels = int(customer_data.get('total', 0))
            total_cancelled = int(customer_data.get('cancel', 0))
        except (ValueError, TypeError):
            total_parcels = 0
            total_cancelled = 0
        
        if total_parcels == 0:
            return 0  # No data available
        
        # Calculate cancellation rate
        cancellation_rate = (total_cancelled / total_parcels) * 100
        
        # Simple scoring logic
        score = 0
        if cancellation_rate > 50:
            score += 30  # High cancellation rate
        elif cancellation_rate > 30:
            score += 15  # Medium cancellation rate
        
        return min(score, 100)  # Cap at 100
    
    def _get_risk_level(self, fraud_score: int) -> str:
        """Get risk level based on fraud score"""
        if fraud_score >= 70:
            return 'HIGH'
        elif fraud_score >= 40:
            return 'MEDIUM'
        elif fraud_score >= 20:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _get_risk_color(self, risk_level: str) -> str:
        """Get color code for risk level"""
        risk_colors = {
            'HIGH': 'danger',
            'MEDIUM': 'warning', 
            'LOW': 'info',
            'MINIMAL': 'success'
        }
        return risk_colors.get(risk_level, 'secondary')
    
    def _get_mock_data(self, phone_number: str) -> Dict[str, Any]:
        """Return mock data for testing purposes"""
        # More realistic mock data based on phone number patterns
        if phone_number.endswith('966'):  # Like 01309055966 - High risk customer
            return {
                'success': 6,
                'cancel': 9,
                'total': 15
            }
        elif phone_number.endswith('678'):  # Different pattern - Medium risk
            return {
                'success': 9,
                'cancel': 6,
                'total': 15
            }
        elif phone_number.endswith('555'):  # Low risk customer
            return {
                'success': 17,
                'cancel': 3,
                'total': 20
            }
        else:  # Default mock data - Minimal risk
            return {
                'success': 11,
                'cancel': 4,
                'total': 15
            }
