from django.shortcuts import render
from django.http import HttpResponse

def test_checkout_template(request):
    """Test view to render checkout template directly"""
    return render(request, 'frontend/checkout.html', {
        'cart': None,  # Empty cart for testing
        'total_amount': 0,
    })