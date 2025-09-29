from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from products.models import Product, Category
from .models import (
    IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress,
    IncompleteOrderHistory, RecoveryEmailLog
)
from .services import IncompleteOrderService

User = get_user_model()


class IncompleteOrderModelTest(TestCase):
    """Test cases for IncompleteOrder model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a category and product for testing
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            stock_quantity=10
        )
    
    def test_incomplete_order_creation(self):
        """Test creating an incomplete order"""
        incomplete_order = IncompleteOrder.objects.create(
            user=self.user,
            customer_email='test@example.com',
            subtotal=100.00,
            total_amount=100.00
        )
        
        self.assertTrue(incomplete_order.incomplete_order_id.startswith('INC-'))
        self.assertEqual(incomplete_order.status, 'pending')
        self.assertIsNotNone(incomplete_order.expires_at)
        self.assertTrue(incomplete_order.can_convert)
    
    def test_incomplete_order_auto_id_generation(self):
        """Test automatic ID generation"""
        order1 = IncompleteOrder.objects.create(user=self.user)
        order2 = IncompleteOrder.objects.create(user=self.user)
        
        self.assertNotEqual(order1.incomplete_order_id, order2.incomplete_order_id)
        self.assertTrue(order1.incomplete_order_id.startswith('INC-'))
        self.assertTrue(order2.incomplete_order_id.startswith('INC-'))
    
    def test_incomplete_order_expiry(self):
        """Test order expiry logic"""
        # Create expired order
        expired_order = IncompleteOrder.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        self.assertTrue(expired_order.is_expired)
        self.assertFalse(expired_order.can_convert)
    
    def test_mark_as_abandoned(self):
        """Test marking order as abandoned"""
        incomplete_order = IncompleteOrder.objects.create(user=self.user)
        
        incomplete_order.mark_as_abandoned('Test reason')
        
        self.assertEqual(incomplete_order.status, 'abandoned')
        self.assertEqual(incomplete_order.abandonment_reason, 'Test reason')
        self.assertIsNotNone(incomplete_order.abandoned_at)
    
    def test_total_calculation(self):
        """Test total amount calculation"""
        incomplete_order = IncompleteOrder.objects.create(user=self.user)
        
        # Add items
        IncompleteOrderItem.objects.create(
            incomplete_order=incomplete_order,
            product=self.product,
            quantity=2,
            unit_price=100.00
        )
        
        incomplete_order.calculate_totals()
        
        self.assertEqual(incomplete_order.subtotal, 200.00)
        self.assertEqual(incomplete_order.total_amount, 200.00)
        self.assertEqual(incomplete_order.total_items, 2)


class IncompleteOrderItemTest(TestCase):
    """Test cases for IncompleteOrderItem model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            stock_quantity=10
        )
        
        self.incomplete_order = IncompleteOrder.objects.create(user=self.user)
    
    def test_item_creation(self):
        """Test creating an incomplete order item"""
        item = IncompleteOrderItem.objects.create(
            incomplete_order=self.incomplete_order,
            product=self.product,
            quantity=2,
            unit_price=100.00
        )
        
        self.assertEqual(item.product_name, 'Test Product')
        self.assertEqual(item.total_price, 200.00)
    
    def test_item_total_price(self):
        """Test total price calculation"""
        item = IncompleteOrderItem.objects.create(
            incomplete_order=self.incomplete_order,
            product=self.product,
            quantity=3,
            unit_price=50.00
        )
        
        self.assertEqual(item.total_price, 150.00)


class IncompleteOrderServiceTest(TestCase):
    """Test cases for IncompleteOrderService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            stock_quantity=10
        )
    
    def test_create_from_cart(self):
        """Test creating incomplete order from cart items"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = {'session_key': 'test-session'}
        request.META = {'HTTP_USER_AGENT': 'Test Browser'}
        
        # Mock cart items
        cart_items = [{
            'product_id': self.product.id,
            'quantity': 2,
            'unit_price': 100.00
        }]
        
        customer_data = {
            'email': 'customer@example.com',
            'phone': '1234567890'
        }
        
        incomplete_order = IncompleteOrderService.create_from_cart(
            request, cart_items, customer_data
        )
        
        self.assertEqual(incomplete_order.user, self.user)
        self.assertEqual(incomplete_order.customer_email, 'customer@example.com')
        self.assertEqual(incomplete_order.items.count(), 1)
        self.assertEqual(incomplete_order.total_amount, 200.00)
    
    def test_get_recovery_candidates(self):
        """Test getting recovery candidates"""
        # Create order that needs recovery
        old_order = IncompleteOrder.objects.create(
            user=self.user,
            customer_email='test@example.com',
            created_at=timezone.now() - timedelta(hours=3),
            recovery_attempts=0
        )
        
        # Create order that doesn't need recovery (too new)
        new_order = IncompleteOrder.objects.create(
            user=self.user,
            customer_email='test2@example.com',
            created_at=timezone.now() - timedelta(minutes=30),
            recovery_attempts=0
        )
        
        candidates = IncompleteOrderService.get_recovery_candidates(hours_since_creation=2)
        
        self.assertIn(old_order, candidates)
        self.assertNotIn(new_order, candidates)
    
    def test_auto_expire_orders(self):
        """Test auto-expiring old orders"""
        # Create old order
        old_order = IncompleteOrder.objects.create(
            user=self.user,
            created_at=timezone.now() - timedelta(days=35)
        )
        
        # Create recent order
        recent_order = IncompleteOrder.objects.create(
            user=self.user,
            created_at=timezone.now() - timedelta(days=5)
        )
        
        expired_count = IncompleteOrderService.auto_expire_orders(days_old=30)
        
        old_order.refresh_from_db()
        recent_order.refresh_from_db()
        
        self.assertEqual(expired_count, 1)
        self.assertEqual(old_order.status, 'expired')
        self.assertEqual(recent_order.status, 'pending')


class IncompleteOrderAPITest(APITestCase):
    """Test cases for IncompleteOrder API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            stock_quantity=10
        )
        
        self.incomplete_order = IncompleteOrder.objects.create(
            user=self.user,
            customer_email='test@example.com',
            subtotal=100.00,
            total_amount=100.00
        )
        
        IncompleteOrderItem.objects.create(
            incomplete_order=self.incomplete_order,
            product=self.product,
            quantity=1,
            unit_price=100.00
        )
    
    def test_list_incomplete_orders_authenticated(self):
        """Test listing incomplete orders as authenticated user"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/v1/incomplete-orders/api/incomplete-orders/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_convert_to_order(self):
        """Test converting incomplete order to complete order"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/v1/incomplete-orders/api/incomplete-orders/{self.incomplete_order.id}/convert_to_order/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('order_number', response.data)
        
        # Check that incomplete order status changed
        self.incomplete_order.refresh_from_db()
        self.assertEqual(self.incomplete_order.status, 'converted')
    
    def test_mark_abandoned(self):
        """Test marking incomplete order as abandoned"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/v1/incomplete-orders/api/incomplete-orders/{self.incomplete_order.id}/mark_abandoned/',
            {'reason': 'Test abandonment'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that order was marked as abandoned
        self.incomplete_order.refresh_from_db()
        self.assertEqual(self.incomplete_order.status, 'abandoned')
        self.assertEqual(self.incomplete_order.abandonment_reason, 'Test abandonment')
    
    def test_statistics_endpoint(self):
        """Test statistics endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/v1/incomplete-orders/api/incomplete-orders/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_incomplete_orders', response.data)
        self.assertIn('conversion_rate', response.data)
    
    def test_send_recovery_email(self):
        """Test sending recovery email"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/api/v1/incomplete-orders/api/incomplete-orders/{self.incomplete_order.id}/send_recovery_email/',
            {'email_type': 'abandoned_cart'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that recovery attempt was incremented
        self.incomplete_order.refresh_from_db()
        self.assertEqual(self.incomplete_order.recovery_attempts, 1)
        
        # Check that recovery email log was created
        self.assertTrue(
            RecoveryEmailLog.objects.filter(
                incomplete_order=self.incomplete_order
            ).exists()
        )
