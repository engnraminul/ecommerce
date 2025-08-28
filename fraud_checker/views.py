from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
import json
import logging

from .combined_service import CombinedFraudChecker

logger = logging.getLogger(__name__)


class FraudCheckView(LoginRequiredMixin, TemplateView):
    """Simple fraud check interface"""
    template_name = 'fraud_checker/fraud_check.html'


class FraudCheckAPIView(LoginRequiredMixin, View):
    """API endpoint for fraud checking"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number', '').strip()
            
            if not phone_number:
                return JsonResponse({
                    'success': False,
                    'error': 'Phone number is required'
                }, status=400)
            
            # Initialize combined fraud checker service
            fraud_service = CombinedFraudChecker()
            
            # Perform fraud check across all couriers
            result = fraud_service.check_fraud_all_couriers(phone_number)
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Fraud check API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)