from django.urls import path
from . import views

app_name = 'fraud_checker'

urlpatterns = [
    # Main fraud check interface
    path('', views.FraudCheckView.as_view(), name='fraud_check'),
    
    # API endpoint for checking
    path('api/check/', views.FraudCheckAPIView.as_view(), name='api_check'),
]