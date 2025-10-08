#!/usr/bin/env python3
"""
Test the actual upload functionality with a problematic filename
"""

import requests
import os
from io import BytesIO
from PIL import Image

def create_test_image(filename):
    """Create a small test image"""
    # Create a simple 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Save to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    
    return img_buffer

def test_upload_with_problematic_filename():
    """Test upload with the specific problematic filename"""
    
    # The filename that was causing the error
    problematic_filename = "Manob bazar office_31f19885.jpg"
    
    print(f"Testing upload with filename: '{problematic_filename}'")
    
    # Create test image
    test_image = create_test_image(problematic_filename)
    
    # Prepare the upload
    files = {
        'file': (problematic_filename, test_image, 'image/jpeg')
    }
    
    data = {
        'directory': 'products'
    }
    
    # Test the upload (assuming server is running on localhost:8000)
    try:
        # You would need to be logged in and have CSRF token for this to work
        # This is just to demonstrate the API call structure
        response = requests.post(
            'http://127.0.0.1:8000/mb-admin/api/media/upload/',
            files=files,
            data=data,
            # headers={'X-CSRFToken': 'your-csrf-token'}  # Would need actual token
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    print("\nNote: This test requires authentication and CSRF token.")
    print("The important part is that the filename sanitization prevents the path traversal error.")

if __name__ == "__main__":
    test_upload_with_problematic_filename()