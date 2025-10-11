from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pages.models import PageCategory, PageTemplate, Page

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample pages and categories for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to assign as author (defaults to first admin user)',
        )

    def handle(self, *args, **options):
        # Get or create author
        if options['user_id']:
            try:
                author = User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} not found')
                )
                return
        else:
            author = User.objects.filter(is_staff=True).first()
            if not author:
                self.stdout.write(
                    self.style.ERROR('No admin user found. Please create an admin user first.')
                )
                return

        # Create categories
        categories_data = [
            {
                'name': 'Company',
                'description': 'Pages about the company'
            },
            {
                'name': 'Support',
                'description': 'Support and help pages'
            },
            {
                'name': 'Legal',
                'description': 'Legal documents and policies'
            },
            {
                'name': 'Blog',
                'description': 'Blog posts and articles'
            }
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = PageCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )

        # Create templates
        templates_data = [
            {
                'name': 'Default Template',
                'template_type': 'default',
                'template_file': 'page_detail.html',
                'description': 'Standard page template'
            },
            {
                'name': 'Landing Page Template',
                'template_type': 'landing',
                'template_file': 'landing.html',
                'description': 'Hero section with call-to-action'
            },
            {
                'name': 'Article Template',
                'template_type': 'article',
                'template_file': 'page_detail.html',
                'description': 'Template for blog articles'
            }
        ]

        templates = {}
        for temp_data in templates_data:
            template, created = PageTemplate.objects.get_or_create(
                name=temp_data['name'],
                defaults={
                    'template_type': temp_data['template_type'],
                    'template_file': temp_data['template_file'],
                    'description': temp_data['description']
                }
            )
            templates[temp_data['name']] = template
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )

        # Create sample pages
        pages_data = [
            {
                'title': 'About Us',
                'category': 'Company',
                'template': 'Default Template',
                'content': '''Welcome to our company! We are dedicated to providing exceptional products and services to our customers.

Our mission is to deliver high-quality solutions that meet and exceed customer expectations. With years of experience in the industry, we have built a reputation for reliability, innovation, and customer satisfaction.

## Our Story

Founded in 2020, our company has grown from a small startup to a leading provider in our field. We believe in continuous improvement and staying ahead of industry trends.

## Our Values

- Customer First: We prioritize our customers' needs and satisfaction
- Innovation: We embrace new technologies and creative solutions  
- Quality: We maintain the highest standards in everything we do
- Integrity: We conduct business with honesty and transparency

## Our Team

Our dedicated team of professionals brings diverse expertise and passion to every project. We work collaboratively to ensure the best outcomes for our clients.

Contact us today to learn more about how we can help you achieve your goals!''',
                'excerpt': 'Learn about our company mission, values, and the dedicated team behind our success.',
                'status': 'published',
                'show_in_menu': True,
                'menu_order': 1,
                'meta_title': 'About Us - Learn About Our Company',
                'meta_description': 'Discover our company story, mission, values, and the experienced team dedicated to delivering exceptional products and services.'
            },
            {
                'title': 'Contact Us',
                'category': 'Company',
                'template': 'Default Template',
                'content': '''Get in touch with us! We'd love to hear from you.

## Contact Information

**Address:**  
123 Business Street  
City, State 12345  
Country

**Phone:** +1 (555) 123-4567  
**Email:** info@company.com  
**Business Hours:** Monday - Friday, 9:00 AM - 6:00 PM

## Send Us a Message

Whether you have questions about our products, need support, or want to discuss a potential partnership, we're here to help.

For faster response times, please include:
- Your contact information
- Nature of your inquiry
- Any relevant details about your request

We typically respond to all inquiries within 24 hours during business days.

## Follow Us

Stay connected with us on social media for the latest updates, news, and insights.

Thank you for your interest in our company!''',
                'excerpt': 'Contact us for questions, support, or partnership opportunities. We\'re here to help!',
                'status': 'published',
                'show_in_menu': True,
                'menu_order': 2,
                'meta_title': 'Contact Us - Get in Touch',
                'meta_description': 'Contact our team for questions, support, or business inquiries. Find our contact information and business hours.'
            },
            {
                'title': 'Privacy Policy',
                'category': 'Legal',
                'template': 'Default Template',
                'content': '''# Privacy Policy

Last updated: [Date]

## Introduction

This Privacy Policy describes how we collect, use, and protect your personal information when you use our website and services.

## Information We Collect

### Personal Information
- Name and contact information
- Account credentials
- Payment information
- Communication history

### Automatically Collected Information
- IP address and device information
- Browser type and version
- Usage patterns and preferences
- Cookies and tracking data

## How We Use Your Information

We use your information to:
- Provide and improve our services
- Process transactions and orders
- Communicate with you about our services
- Comply with legal obligations
- Protect against fraud and abuse

## Information Sharing

We do not sell, trade, or rent your personal information to third parties. We may share information:
- With service providers who assist in our operations
- When required by law or to protect our rights
- In connection with business transfers
- With your explicit consent

## Data Security

We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.

## Your Rights

You have the right to:
- Access your personal information
- Correct inaccurate information
- Request deletion of your information
- Opt-out of marketing communications
- Withdraw consent where applicable

## Contact Us

If you have questions about this Privacy Policy, please contact us at privacy@company.com.

This policy is subject to change. We will notify you of any significant updates.''',
                'excerpt': 'Our privacy policy explains how we collect, use, and protect your personal information.',
                'status': 'published',
                'require_login': False,
                'meta_title': 'Privacy Policy - How We Protect Your Information',
                'meta_description': 'Read our privacy policy to understand how we collect, use, and protect your personal information when using our services.'
            },
            {
                'title': 'Terms of Service',
                'category': 'Legal',
                'template': 'Default Template',
                'content': '''# Terms of Service

Last updated: [Date]

## Acceptance of Terms

By accessing and using our website and services, you agree to be bound by these Terms of Service.

## Use of Services

### Permitted Use
- You may use our services for lawful purposes only
- You must provide accurate and complete information
- You are responsible for maintaining account security

### Prohibited Use
- Violating any applicable laws or regulations
- Infringing on intellectual property rights
- Attempting to harm or disrupt our services
- Using automated systems without permission

## Account Registration

To access certain features, you may need to create an account. You agree to:
- Provide accurate registration information
- Maintain the security of your account
- Notify us of any unauthorized access
- Accept responsibility for all account activity

## Intellectual Property

All content and materials on our website are protected by intellectual property laws. You may not:
- Copy, distribute, or modify our content without permission
- Use our trademarks or logos without authorization
- Reverse engineer or attempt to extract source code

## Payment Terms

- All fees are due as specified in your order
- Payments are processed securely through third-party providers
- Refunds are subject to our refund policy
- We reserve the right to change pricing with notice

## Limitation of Liability

To the maximum extent permitted by law, we shall not be liable for any indirect, incidental, special, or consequential damages.

## Termination

We may terminate or suspend your access to our services at any time for violation of these terms or other reasonable cause.

## Changes to Terms

We reserve the right to modify these terms at any time. Continued use of our services constitutes acceptance of updated terms.

## Contact Information

For questions about these Terms of Service, contact us at legal@company.com.''',
                'excerpt': 'Terms of service governing the use of our website and services.',
                'status': 'published',
                'require_login': False,
                'meta_title': 'Terms of Service - Service Usage Terms',
                'meta_description': 'Read our terms of service to understand the rules and guidelines for using our website and services.'
            },
            {
                'title': 'FAQ - Frequently Asked Questions',
                'category': 'Support',
                'template': 'Default Template',
                'content': '''# Frequently Asked Questions

Find answers to the most common questions about our products and services.

## General Questions

### Q: What products/services do you offer?
A: We offer a wide range of high-quality products and services designed to meet our customers' needs. Visit our products page for detailed information.

### Q: How can I place an order?
A: You can place an order through our website by adding items to your cart and proceeding to checkout. You can also contact us directly for assistance.

### Q: What payment methods do you accept?
A: We accept major credit cards, PayPal, and bank transfers. All payments are processed securely.

## Shipping & Delivery

### Q: How long does shipping take?
A: Standard shipping typically takes 3-7 business days. Expedited shipping options are available for faster delivery.

### Q: Do you ship internationally?
A: Yes, we ship to most countries worldwide. Shipping costs and delivery times vary by destination.

### Q: How can I track my order?
A: You'll receive a tracking number via email once your order ships. You can use this to track your package on our website.

## Returns & Refunds

### Q: What is your return policy?
A: We offer a 30-day return policy for most items. Items must be in original condition with all packaging.

### Q: How do I return an item?
A: Contact our customer service team to initiate a return. We'll provide you with return instructions and a prepaid shipping label.

### Q: When will I receive my refund?
A: Refunds are typically processed within 5-7 business days after we receive your returned item.

## Account & Support

### Q: How do I create an account?
A: Click the "Sign Up" button on our website and follow the registration process. You'll need to provide basic information and verify your email.

### Q: I forgot my password. How can I reset it?
A: Click "Forgot Password" on the login page and follow the instructions to reset your password via email.

### Q: How can I contact customer support?
A: You can reach our customer support team via:
- Email: support@company.com
- Phone: +1 (555) 123-4567
- Live chat on our website
- Contact form on our website

## Still Have Questions?

If you can't find the answer you're looking for, please don't hesitate to contact our customer support team. We're here to help!''',
                'excerpt': 'Find answers to frequently asked questions about our products, shipping, returns, and more.',
                'status': 'published',
                'show_in_menu': True,
                'menu_order': 3,
                'meta_title': 'FAQ - Frequently Asked Questions',
                'meta_description': 'Find answers to common questions about our products, shipping, returns, account management, and customer support.'
            }
        ]

        for page_data in pages_data:
            page, created = Page.objects.get_or_create(
                title=page_data['title'],
                defaults={
                    'category': categories.get(page_data['category']),
                    'template': templates.get(page_data['template']),
                    'content': page_data['content'],
                    'excerpt': page_data['excerpt'],
                    'status': page_data['status'],
                    'show_in_menu': page_data.get('show_in_menu', False),
                    'menu_order': page_data.get('menu_order', 0),
                    'require_login': page_data.get('require_login', False),
                    'meta_title': page_data.get('meta_title', ''),
                    'meta_description': page_data.get('meta_description', ''),
                    'author': author
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created page: {page.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSample data created successfully!\n'
                f'Categories: {len(categories)}\n'
                f'Templates: {len(templates)}\n'
                f'Pages: {len(pages_data)}\n'
                f'Author: {author.username}'
            )
        )