#!/usr/bin/env python
"""Create test contact submissions for testing the dashboard"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from contact.models import Contact, ContactSetting

def create_test_contacts():
    """Create test contact submissions"""
    
    test_contacts = [
        {
            'name': 'John Smith',
            'email': 'john.smith@example.com',
            'phone': '+1234567890',
            'subject': 'Product Inquiry',
            'message': 'Hi, I am interested in your latest product range. Could you please send me more information about pricing and availability?',
            'status': 'new',
            'priority': 'medium',
            'submitted_at': timezone.now() - timedelta(hours=2)
        },
        {
            'name': 'Sarah Johnson',
            'email': 'sarah.j@example.com',
            'phone': '+1987654321',
            'subject': 'Support Request',
            'message': 'I am having trouble with my recent order. The product seems to be damaged during shipping. Please help me with a replacement.',
            'status': 'new',
            'priority': 'high',
            'submitted_at': timezone.now() - timedelta(hours=5)
        },
        {
            'name': 'Mike Davis',
            'email': 'mike.davis@company.com',
            'phone': '+1555123456',
            'subject': 'Bulk Order Inquiry',
            'message': 'Our company is interested in placing a bulk order for 500 units. Can you provide wholesale pricing and delivery timeline?',
            'status': 'read',
            'priority': 'urgent',
            'submitted_at': timezone.now() - timedelta(hours=8)
        },
        {
            'name': 'Lisa Anderson',
            'email': 'lisa@example.org',
            'phone': '+1777888999',
            'subject': 'Return Request',
            'message': 'I need to return a product I purchased last week. It doesn\'t meet my requirements. What is your return policy?',
            'status': 'replied',
            'priority': 'low',
            'submitted_at': timezone.now() - timedelta(days=1),
            'replied_at': timezone.now() - timedelta(hours=12)
        },
        {
            'name': 'Robert Wilson',
            'email': 'rwilson@email.com',
            'phone': '+1333444555',
            'subject': 'Technical Support',
            'message': 'The product manual is not clear about the installation process. Could you provide more detailed instructions or a video tutorial?',
            'status': 'new',
            'priority': 'medium',
            'submitted_at': timezone.now() - timedelta(days=2)
        },
        {
            'name': 'Emma Thompson',
            'email': 'emma.t@example.net',
            'phone': '+1666777888',
            'subject': 'Partnership Proposal',
            'message': 'We are a marketing agency and would like to discuss potential partnership opportunities. Please let us know if you are interested.',
            'status': 'resolved',
            'priority': 'high',
            'submitted_at': timezone.now() - timedelta(days=3),
            'replied_at': timezone.now() - timedelta(days=2)
        },
        {
            'name': 'David Brown',
            'email': 'david.brown@test.com',
            'phone': '+1999000111',
            'subject': 'Website Feedback',
            'message': 'Your website is very user-friendly, but I noticed some pages load slowly. Thought you might want to know.',
            'status': 'new',
            'priority': 'low',
            'submitted_at': timezone.now() - timedelta(days=4)
        },
        {
            'name': 'Jennifer Lee',
            'email': 'jen.lee@domain.com',
            'phone': '+1444555666',
            'subject': 'Career Inquiry',
            'message': 'Are you currently hiring? I am interested in joining your team and would like to know about available positions.',
            'status': 'read',
            'priority': 'medium',
            'submitted_at': timezone.now() - timedelta(days=5)
        }
    ]
    
    created_count = 0
    
    for contact_data in test_contacts:
        # Check if contact already exists
        existing = Contact.objects.filter(
            email=contact_data['email'],
            subject=contact_data['subject']
        ).first()
        
        if not existing:
            contact = Contact.objects.create(
                name=contact_data['name'],
                email=contact_data['email'],
                phone=contact_data['phone'],
                subject=contact_data['subject'],
                message=contact_data['message'],
                status=contact_data['status'],
                priority=contact_data['priority'],
                ip_address='127.0.0.1',
                user_agent='Test Browser'
            )
            
            # Update timestamps if specified
            if 'submitted_at' in contact_data:
                contact.submitted_at = contact_data['submitted_at']
            if 'replied_at' in contact_data:
                contact.replied_at = contact_data['replied_at']
            
            contact.save(update_fields=['submitted_at', 'replied_at'])
            created_count += 1
            print(f"Created contact: {contact.name} - {contact.subject}")
    
    print(f"\nCreated {created_count} test contacts")
    print(f"Total contacts in database: {Contact.objects.count()}")

def create_contact_settings():
    """Create default contact settings"""
    
    contact_settings = {
        'business_name': 'Ecommerce Store',
        'address': '123 Business Street, Commerce City, CC 12345',
        'phone': '+1 (555) 123-4567',
        'email': 'contact@ecommercestore.com',
        'business_hours': 'Monday - Friday: 9:00 AM - 6:00 PM\nSaturday: 10:00 AM - 4:00 PM\nSunday: Closed',
        'social_media': {
            'facebook': 'https://facebook.com/ecommercestore',
            'twitter': 'https://twitter.com/ecommercestore',
            'instagram': 'https://instagram.com/ecommercestore',
            'linkedin': 'https://linkedin.com/company/ecommercestore'
        },
        'map_embed_url': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3024.123456789',
        'additional_info': 'We are committed to providing excellent customer service and high-quality products. Feel free to reach out to us with any questions or concerns.'
    }
    
    setting, created = ContactSetting.objects.get_or_create(
        key='contact_details',
        defaults={
            'value': contact_settings,
            'description': 'Contact page settings including business information, address, phone, email, and social media links'
        }
    )
    
    if created:
        print("Created contact settings")
    else:
        print("Contact settings already exist")

if __name__ == '__main__':
    print("Creating test contact data...")
    create_test_contacts()
    create_contact_settings()
    print("Test data creation completed!")