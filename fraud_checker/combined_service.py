import asyncio
import concurrent.futures
import logging
from typing import Dict, Any, List
from .services import PackzyFraudChecker
from .pathao_service import PathaoFraudChecker
from .redx_service import RedxFraudChecker

logger = logging.getLogger(__name__)


class CombinedFraudChecker:
    """Combined service to check fraud across multiple courier services"""
    
    def __init__(self):
        self.packzy_checker = PackzyFraudChecker()
        self.pathao_checker = PathaoFraudChecker()
        self.redx_checker = RedxFraudChecker()
    
    def check_fraud_all_couriers(self, phone_number: str) -> Dict[str, Any]:
        """
        Check fraud status across all courier services
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            Dict with results from all couriers
        """
        logger.info(f"Starting combined fraud check for {phone_number}")
        
        # Run all checks in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            packzy_future = executor.submit(self._check_packzy, phone_number)
            pathao_future = executor.submit(self._check_pathao, phone_number)
            redx_future = executor.submit(self._check_redx, phone_number)
            
            # Wait for all to complete
            packzy_result = packzy_future.result()
            pathao_result = pathao_future.result()
            redx_result = redx_future.result()
        
        # Combine results
        combined_result = {
            'success': True,
            'phone_number': phone_number,
            'couriers': {
                'steadfast': packzy_result,
                'pathao': pathao_result,
                'redx': redx_result,
            },
            'summary': self._generate_summary([packzy_result, pathao_result, redx_result])
        }
        
        logger.info(f"Combined fraud check completed for {phone_number}")
        return combined_result
    
    def _check_packzy(self, phone_number: str) -> Dict[str, Any]:
        """Check Packzy (Steadfast) fraud status"""
        try:
            result = self.packzy_checker.check_fraud(phone_number)
            result['courier_name'] = 'Steadfast'
            return result
        except Exception as e:
            logger.error(f"Packzy check failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'courier': 'steadfast',
                'courier_name': 'Steadfast',
                'total_parcels': 0,
                'total_delivered': 0,
                'total_cancelled': 0,
                'fraud_score': 0,
                'risk_level': 'UNKNOWN',
                'risk_color': 'secondary'
            }
    
    def _check_pathao(self, phone_number: str) -> Dict[str, Any]:
        """Check Pathao fraud status"""
        try:
            result = self.pathao_checker.check_fraud(phone_number)
            result['courier_name'] = 'Pathao'
            return result
        except Exception as e:
            logger.error(f"Pathao check failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'courier': 'pathao',
                'courier_name': 'Pathao',
                'total_parcels': 0,
                'total_delivered': 0,
                'total_cancelled': 0,
                'fraud_score': 0,
                'risk_level': 'UNKNOWN',
                'risk_color': 'secondary'
            }
    
    def _check_redx(self, phone_number: str) -> Dict[str, Any]:
        """Check RedX fraud status"""
        try:
            result = self.redx_checker.check_fraud(phone_number)
            result['courier_name'] = 'RedX'
            return result
        except Exception as e:
            logger.error(f"RedX check failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'courier': 'redx',
                'courier_name': 'RedX',
                'total_parcels': 0,
                'total_delivered': 0,
                'total_cancelled': 0,
                'fraud_score': 0,
                'risk_level': 'UNKNOWN',
                'risk_color': 'secondary'
            }
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a combined summary from all courier results"""
        total_parcels = 0
        total_delivered = 0
        total_cancelled = 0
        successful_checks = 0
        max_fraud_score = 0
        highest_risk = 'MINIMAL'
        
        risk_priority = {'MINIMAL': 0, 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'UNKNOWN': -1}
        
        for result in results:
            if result.get('success', False):
                successful_checks += 1
                # Ensure numeric values by converting to int
                try:
                    total_parcels += int(result.get('total_parcels', 0))
                    total_delivered += int(result.get('total_delivered', 0))
                    total_cancelled += int(result.get('total_cancelled', 0))
                except (ValueError, TypeError):
                    # Skip this result if conversion fails
                    continue
                
                fraud_score = result.get('fraud_score', 0)
                risk_level = result.get('risk_level', 'MINIMAL')
                
                if fraud_score > max_fraud_score:
                    max_fraud_score = fraud_score
                
                if risk_priority.get(risk_level, -1) > risk_priority.get(highest_risk, 0):
                    highest_risk = risk_level
        
        # Calculate overall cancellation rate
        overall_cancellation_rate = 0
        if total_parcels > 0:
            overall_cancellation_rate = (total_cancelled / total_parcels) * 100
        
        return {
            'total_parcels': total_parcels,
            'total_delivered': total_delivered,
            'total_cancelled': total_cancelled,
            'cancellation_rate': round(overall_cancellation_rate, 1),
            'max_fraud_score': max_fraud_score,
            'highest_risk_level': highest_risk,
            'successful_checks': successful_checks,
            'total_couriers': len(results),
            'risk_color': self._get_risk_color(highest_risk)
        }
    
    def _get_risk_color(self, risk_level: str) -> str:
        """Get color code for risk level"""
        risk_colors = {
            'HIGH': 'danger',
            'MEDIUM': 'warning', 
            'LOW': 'info',
            'MINIMAL': 'success',
            'UNKNOWN': 'secondary'
        }
        return risk_colors.get(risk_level, 'secondary')
