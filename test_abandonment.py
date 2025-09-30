import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from cart.models import Cart

def test_checkout_abandonment():
    print('🧪 Testing checkout abandonment API...')
    
    # Create test client
    client = Client()
    
    # Get user and login
    User = get_user_model()
    user = User.objects.first()
    
    if user:
        client.force_login(user)
        print(f'✅ Logged in as {user.email}')
    else:
        print('❌ No user found')
        return
    
    # Test data to save
    checkout_data = {
        'full_name': 'John Doe',
        'email': 'john.doe@example.com',
        'phone_number': '01234567890',
        'address': '123 Test Street, Dhaka',
        'order_instruction': 'Please ring the bell twice'
    }
    
    print('📝 Simulating checkout form data entry...')
    
    # Step 1: Save checkout data (simulating user typing in form)
    response = client.post('/api/incomplete-orders/save-checkout-data/', 
                          json.dumps(checkout_data),
                          content_type='application/json')
    
    if response.status_code == 200:
        print('✅ Checkout data saved to session')
    else:
        print(f'❌ Failed to save checkout data: {response.status_code}')
        print(response.content)
        return
    
    # Step 2: Track abandonment (simulating user leaving page)
    response = client.post('/api/incomplete-orders/track-abandonment/')
    
    if response.status_code == 200:
        result = json.loads(response.content)
        if result.get('status') == 'created':
            print(f'✅ Incomplete order created: {result.get("incomplete_order_id")}')
        else:
            print(f'⚠️  Response: {result}')
    else:
        print(f'❌ Failed to track abandonment: {response.status_code}')
        print(response.content)
    
    print()
    print('🔍 Checking incomplete orders after test...')

if __name__ == '__main__':
    test_checkout_abandonment()