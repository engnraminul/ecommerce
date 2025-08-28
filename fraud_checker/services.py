import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PackzyFraudChecker:
    """Simple service class to handle Packzy API fraud checking"""
    
    BASE_URL = "https://portal.packzy.com/api/v1/fraud_check"
    TIMEOUT = 30  # seconds
    USE_MOCK_DATA = False  # Set to True for testing with mock data
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def check_fraud(self, phone_number: str) -> Dict[str, Any]:
        """
        Check fraud status for a phone number using Packzy API
        
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
                'error': 'Invalid phone number provided'
            }
        
        # Make API call or use mock data
        try:
            logger.info(f"Making fraud check API call for {phone_number}")
            
            if self.USE_MOCK_DATA:
                logger.info("Using mock data for testing")
                response_data = self._get_mock_data(phone_number)
            else:
                response_data = self._make_api_call(phone_number)
            
            if response_data:
                # Calculate fraud score and risk level
                fraud_score = self._calculate_fraud_score(response_data)
                risk_level = self._get_risk_level(fraud_score)
                risk_color = self._get_risk_color(risk_level)
                
                return {
                    'success': True,
                    'phone_number': phone_number,
                    'total_parcels': int(response_data.get('total_parcels', 0)) if response_data.get('total_parcels') else 0,
                    'total_delivered': int(response_data.get('total_delivered', 0)) if response_data.get('total_delivered') else 0,
                    'total_cancelled': int(response_data.get('total_cancelled', 0)) if response_data.get('total_cancelled') else 0,
                    'total_fraud_reports': response_data.get('total_fraud_reports', []),
                    'fraud_score': fraud_score,
                    'risk_level': risk_level,
                    'risk_color': risk_color,
                }
            else:
                return {
                    'success': False,
                    'error': 'API call returned empty response'
                }
                
        except Exception as e:
            logger.error(f"Fraud check failed for {phone_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
    
    def _make_api_call(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Make the actual API call to Packzy"""
        url = f"{self.BASE_URL}/{phone_number}"
        
        try:
            logger.info(f"Making GET request to: {url}")
            response = self.session.get(url, timeout=self.TIMEOUT)
            
            logger.debug(f"API Response Status: {response.status_code}")
            logger.debug(f"API Response Body: {response.text}")
            
            if response.status_code == 200:
                if not response.text.strip():
                    logger.error(f"API returned empty response for {phone_number}")
                    return None
                    
                try:
                    json_data = response.json()
                    logger.info(f"Successfully parsed JSON response")
                    return json_data
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw response text: {response.text}")
                    return None
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"API call timed out for {phone_number}")
            raise Exception("API call timed out")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {phone_number}")
            raise Exception("Connection error to fraud check API")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {phone_number}: {e}")
            raise Exception(f"API request failed: {str(e)}")
    
    def _calculate_fraud_score(self, api_response: Dict[str, Any]) -> int:
        """Calculate a simple fraud risk score based on the data"""
        # Ensure numeric values by converting strings to integers
        try:
            total_parcels = int(api_response.get('total_parcels', 0))
            total_cancelled = int(api_response.get('total_cancelled', 0))
        except (ValueError, TypeError):
            total_parcels = 0
            total_cancelled = 0
            
        fraud_reports = api_response.get('total_fraud_reports', [])
        
        if total_parcels == 0:
            return 0  # No data available
        
        # Calculate cancellation rate
        cancellation_rate = (total_cancelled / total_parcels) * 100
        
        # Calculate fraud reports count
        fraud_reports_count = len(fraud_reports) if isinstance(fraud_reports, list) else 0
        
        # Simple scoring logic
        score = 0
        if cancellation_rate > 50:
            score += 30  # High cancellation rate
        elif cancellation_rate > 30:
            score += 15  # Medium cancellation rate
        
        if fraud_reports_count > 0:
            score += fraud_reports_count * 20  # Each fraud report adds 20 points
        
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
        # More realistic mock data matching your example format
        if phone_number.endswith('966'):  # Like 01309055966 - High risk
            return {
                'total_parcels': 10,
                'total_delivered': 5,
                'total_cancelled': 5,
                'total_fraud_reports': []
            }
        elif phone_number.endswith('678'):  # Different pattern - Medium risk
            return {
                'total_parcels': 12,
                'total_delivered': 8,
                'total_cancelled': 4,
                'total_fraud_reports': ['Multiple address changes']
            }
        elif phone_number.endswith('555'):  # Low risk customer
            return {
                'total_parcels': 8,
                'total_delivered': 7,
                'total_cancelled': 1,
                'total_fraud_reports': []
            }
        else:  # Default mock data - Minimal risk
            return {
                'total_parcels': 6,
                'total_delivered': 6,
                'total_cancelled': 0,
                'total_fraud_reports': []
            }