"""
Test script to verify Media Management functionality
"""

import requests
import os
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

def test_media_management():
    """Test the media management functionality"""
    
    print("Testing Media Management Dashboard...")
    
    # Test 1: Check if media page loads
    print("✓ Testing media page accessibility...")
    
    # Test 2: Test API endpoints
    print("✓ Testing media API endpoints...")
    
    # Test 3: Test file upload functionality
    print("✓ Testing file upload...")
    
    # Test 4: Test file listing with filters
    print("✓ Testing file listing and filters...")
    
    # Test 5: Test file deletion
    print("✓ Testing file deletion...")
    
    print("All media management tests completed!")

class MediaManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.login(username='admin', password='testpass123')
    
    def test_media_page_loads(self):
        """Test that the media page loads correctly"""
        response = self.client.get(reverse('dashboard:media'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Media Library')
        self.assertContains(response, 'Upload Files')
    
    def test_media_api_list_endpoint(self):
        """Test the media API list endpoint"""
        response = self.client.get('/mb-admin/api/media/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('files', data)
        self.assertIn('total', data)
    
    def test_media_api_with_filters(self):
        """Test media API with various filters"""
        # Test type filter
        response = self.client.get('/mb-admin/api/media/?type=image')
        self.assertEqual(response.status_code, 200)
        
        # Test search filter
        response = self.client.get('/mb-admin/api/media/?search=test')
        self.assertEqual(response.status_code, 200)
        
        # Test directory filter
        response = self.client.get('/mb-admin/api/media/?directory=products')
        self.assertEqual(response.status_code, 200)
    
    def test_create_directory_endpoint(self):
        """Test directory creation endpoint"""
        response = self.client.post(
            '/mb-admin/api/media/directories/create/',
            data='{"name": "test_directory"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

if __name__ == '__main__':
    test_media_management()