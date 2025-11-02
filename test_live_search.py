"""
Test script to verify live search functionality
"""
import requests
import json

def test_live_search_api():
    """Test the live search API endpoint"""
    base_url = "http://127.0.0.1:8000"
    
    test_cases = [
        {"q": "test", "category": ""},
        {"q": "product", "category": ""},
        {"q": "phone", "category": ""},
        {"q": "laptop", "category": ""},
        {"q": "a", "category": ""},  # Too short query
    ]
    
    print("Testing Live Search API...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: Query='{test_case['q']}', Category='{test_case['category']}'")
        
        try:
            # Make API request
            response = requests.get(
                f"{base_url}/api/live-search/",
                params=test_case,
                headers={
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response Keys: {list(data.keys())}")
                print(f"Products: {len(data.get('products', []))}")
                print(f"Categories: {len(data.get('categories', []))}")
                print(f"Suggestions: {len(data.get('suggestions', []))}")
                
                # Show first product if available
                if data.get('products'):
                    product = data['products'][0]
                    print(f"First Product: {product.get('name', 'N/A')}")
                    
                # Show first category if available
                if data.get('categories'):
                    category = data['categories'][0]
                    print(f"First Category: {category.get('name', 'N/A')}")
                    
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response.text}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_live_search_api()