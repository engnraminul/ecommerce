import requests
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class PathaoFraudChecker:
    """Service class to handle Pathao API fraud checking"""
    
    LOGIN_URL = "https://merchant.pathao.com/api/v1/login"
    SUCCESS_URL = "https://merchant.pathao.com/api/v1/user/success"
    TIMEOUT = 30  # seconds
    
    # Pathao credentials
    USERNAME = "info.aminul3065@gmail.com"
    PASSWORD = "Pathao@3065"
    USE_MOCK_DATA = False  # Set to False for real API calls
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
    
    def check_fraud(self, phone_number: str) -> Dict[str, Any]:
        """
        Check fraud status for a phone number using Pathao API
        
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
                'courier': 'pathao'
            }
        
        try:
            logger.info(f"Making Pathao fraud check for {phone_number}")
            
            if self.USE_MOCK_DATA:
                logger.info("Using mock data for Pathao testing")
                customer_data = self._get_mock_data(phone_number)
            else:
                # Step 1: Login to get access token
                access_token = self._login()
                if not access_token:
                    return {
                        'success': False,
                        'error': 'Failed to authenticate with Pathao',
                        'courier': 'pathao'
                    }
                
                # Step 2: Get customer data
                customer_data = self._get_customer_data(phone_number, access_token)
                if not customer_data:
                    return {
                        'success': False,
                        'error': 'Failed to retrieve customer data from Pathao',
                        'courier': 'pathao'
                    }
            
            # Calculate fraud score and risk level
            fraud_score = self._calculate_fraud_score(customer_data)
            risk_level = self._get_risk_level(fraud_score)
            risk_color = self._get_risk_color(risk_level)
            
            return {
                'success': True,
                'courier': 'pathao',
                'phone_number': phone_number,
                'total_parcels': int(customer_data.get('total', 0)) if customer_data.get('total') else 0,
                'total_delivered': int(customer_data.get('success', 0)) if customer_data.get('success') else 0,
                'total_cancelled': int(customer_data.get('cancel', 0)) if customer_data.get('cancel') else 0,
                'fraud_score': fraud_score,
                'risk_level': risk_level,
                'risk_color': risk_color,
            }
            
        except Exception as e:
            logger.error(f"Pathao fraud check failed for {phone_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'courier': 'pathao'
            }
    
    def _login(self) -> Optional[str]:
        """Login to Pathao and get access token"""
        try:
            logger.info("Logging in to Pathao API")
            
            response = self.session.post(
                self.LOGIN_URL,
                json={
                    'username': self.USERNAME,
                    'password': self.PASSWORD,
                },
                timeout=self.TIMEOUT
            )
            
            logger.debug(f"Pathao login response status: {response.status_code}")
            
            if not response.ok:
                logger.error(f"Pathao login failed with status {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            access_token = data.get('access_token', '').strip()
            
            if not access_token:
                logger.error("No access token received from Pathao")
                return None
            
            logger.info("Successfully logged in to Pathao")
            return access_token
            
        except Exception as e:
            logger.error(f"Pathao login error: {str(e)}")
            return None
    
    def _get_customer_data(self, phone_number: str, access_token: str) -> Optional[Dict[str, Any]]:
        """Get customer delivery data from Pathao"""
        try:
            logger.info(f"Getting customer data for {phone_number}")
            
            response = self.session.post(
                self.SUCCESS_URL,
                json={
                    'phone': phone_number,
                },
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                },
                timeout=self.TIMEOUT
            )
            
            logger.debug(f"Pathao customer data response status: {response.status_code}")
            
            if not response.ok:
                logger.error(f"Pathao customer data failed with status {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            customer_info = data.get('data', {}).get('customer', {})
            
            if not customer_info:
                logger.warning("No customer data found in Pathao response")
                return {
                    'success': 0,
                    'cancel': 0,
                    'total': 0,
                }
            
            total_delivery = customer_info.get('total_delivery', 0)
            successful_delivery = customer_info.get('successful_delivery', 0)
            cancelled_delivery = total_delivery - successful_delivery
            
            result = {
                'success': successful_delivery,
                'cancel': cancelled_delivery,
                'total': total_delivery,
            }
            
            logger.info(f"Pathao customer data retrieved: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Pathao customer data error: {str(e)}")
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
                'success': 8,
                'cancel': 7,
                'total': 15
            }
        elif phone_number.endswith('678'):  # Different pattern - Medium risk
            return {
                'success': 10,
                'cancel': 5,
                'total': 15
            }
        elif phone_number.endswith('555'):  # Low risk customer
            return {
                'success': 18,
                'cancel': 2,
                'total': 20
            }
        else:  # Default mock data - Minimal risk
            return {
                'success': 12,
                'cancel': 3,
                'total': 15
            }
