import requests
import json

def test_order_tracking_api():
    # Test order tracking by order number
    order_number = "MB1050"
    url = f"http://localhost:8000/api/v1/orders/{order_number}/track/"
    
    try:
        print(f"Testing order tracking API for order: {order_number}")
        response = requests.get(url, headers={'Accept': 'application/json'})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Order tracking data received successfully!")
            print(f"Order Number: {data.get('order_number')}")
            print(f"Status: {data.get('status')}")
            print(f"Items: {len(data.get('items', []))}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test find orders by phone
    print("\n" + "="*50)
    print("Testing find orders by phone API")
    
    phone_url = "http://localhost:8000/api/v1/orders/find-by-phone/"
    
    # Test with different phone formats
    test_phones = [
        "01777173040",
        "01777-173040", 
        "+8801777173040",
        "8801777173040"
    ]
    
    for test_phone in test_phones:
        print(f"\nTesting phone: {test_phone}")
        try:
            data = {"phone_number": test_phone}
            response = requests.post(
                phone_url, 
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                orders = response_data.get('orders', [])
                print(f"Found {len(orders)} orders for phone: {test_phone}")
                for order in orders:
                    print(f"  - Order: {order['order_number']} (Status: {order['status']})")
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Make sure Django server is running on localhost:8000")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_order_tracking_api()