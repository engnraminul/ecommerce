#!/usr/bin/env python
"""
Quick test for statistics API using Django shell
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Create Django test client
client = Client()

# Get an admin user
admin_user = User.objects.filter(is_staff=True).first()
if not admin_user:
    print("❌ No admin user found")
    exit(1)

print(f"✅ Found admin user: {admin_user.username}")

# Login as admin
client.force_login(admin_user)

# Make the request
response = client.get('/mb-admin/api/statistics/')

print(f"📊 Response Status: {response.status_code}")

if response.status_code == 200:
    try:
        data = response.json()
        print("✅ Statistics API working!")
        print(f"📈 Total Sales: ${data.get('total_sales', 0)}")
        print(f"📦 Total Orders: {data.get('orders_count', 0)}")
        print(f"💰 Total Revenue: ${data.get('total_revenue', 0)}")
        print(f"💸 Total Expenses: ${data.get('total_expenses', 0)}")
        print(f"📊 Profit Margin: {data.get('profit_margin', 0)}%")
    except Exception as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"Response: {response.content}")
else:
    print(f"❌ Error: {response.status_code}")
    if hasattr(response, 'content'):
        print(f"Response content (first 500 chars): {response.content[:500]}")