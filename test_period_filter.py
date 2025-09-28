#!/usr/bin/env python
"""
Test script for the new period filter functionality in statistics dashboard.
This script tests the different period options: This Week, This Month, Last Month, This Year, and Custom Range.
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://127.0.0.1:8000"
STATISTICS_API_URL = f"{BASE_URL}/mb-admin/api/statistics/"

def test_period_filter():
    """Test different period filter options"""
    
    periods_to_test = [
        ("week", "This Week"),
        ("month", "This Month"), 
        ("last_month", "Last Month"),
        ("year", "This Year"),
    ]
    
    print("🔍 Testing Period Filter Functionality")
    print("=" * 50)
    
    for period_value, period_name in periods_to_test:
        print(f"📊 Testing {period_name} ({period_value})...")
        
        try:
            response = requests.get(STATISTICS_API_URL, params={"period": period_value})
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {period_name}: Success")
                print(f"   📈 Total Sales: ${data.get('total_sales', 0):.2f}")
                print(f"   🛍️  Orders Count: {data.get('orders_count', 0)}")
                print(f"   💰 Total Revenue: ${data.get('total_revenue', 0):.2f}")
            else:
                print(f"❌ {period_name}: Failed (HTTP {response.status_code})")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ {period_name}: Error - {str(e)}")
        
        print()
    
    # Test custom date range
    print("📅 Testing Custom Date Range...")
    today = datetime.now()
    last_week = today - timedelta(days=7)
    
    custom_params = {
        "period": "custom",
        "date_from": last_week.strftime("%Y-%m-%d"),
        "date_to": today.strftime("%Y-%m-%d")
    }
    
    try:
        response = requests.get(STATISTICS_API_URL, params=custom_params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Custom Range: Success")
            print(f"   📅 Date Range: {custom_params['date_from']} to {custom_params['date_to']}")
            print(f"   📈 Total Sales: ${data.get('total_sales', 0):.2f}")
            print(f"   🛍️  Orders Count: {data.get('orders_count', 0)}")
            print(f"   💰 Total Revenue: ${data.get('total_revenue', 0):.2f}")
        else:
            print(f"❌ Custom Range: Failed (HTTP {response.status_code})")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Custom Range: Error - {str(e)}")

def test_invalid_custom_range():
    """Test invalid custom date range handling"""
    
    print("\n🧪 Testing Invalid Date Range Handling")
    print("=" * 50)
    
    # Test invalid date format
    invalid_params = {
        "period": "custom",
        "date_from": "invalid-date",
        "date_to": "2025-09-28"
    }
    
    try:
        response = requests.get(STATISTICS_API_URL, params=invalid_params)
        
        if response.status_code == 400:
            print("✅ Invalid date format handling: Success")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Invalid date format handling: Unexpected response (HTTP {response.status_code})")
            
    except Exception as e:
        print(f"❌ Invalid date format test: Error - {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Period Filter Tests")
    print("Make sure the Django server is running at http://127.0.0.1:8000")
    print()
    
    try:
        test_period_filter()
        test_invalid_custom_range()
        
        print("\n🎉 Testing Complete!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")