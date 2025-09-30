"""
Middleware for tracking checkout abandonment and creating incomplete orders
"""
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.sessions.models import Session
from django.utils import timezone
from .services import IncompleteOrderService


class CheckoutAbandonmentMiddleware(MiddlewareMixin):
    """Middleware to track checkout abandonment"""
    
    def process_request(self, request):
        """Process incoming requests to track checkout data"""
        
        # Handle AJAX requests for saving checkout data
        if (request.path == '/api/incomplete-orders/save-checkout-data/' and 
            request.method == 'POST'):
            
            try:
                # Parse the JSON data
                data = json.loads(request.body.decode('utf-8'))
                
                # Store checkout data in session
                request.session['checkout_data'] = data
                request.session['checkout_timestamp'] = str(timezone.now())
                
                return HttpResponse(json.dumps({'status': 'saved'}), 
                                  content_type='application/json')
                                  
            except Exception as e:
                return HttpResponse(json.dumps({'error': str(e)}), 
                                  content_type='application/json', 
                                  status=400)
        
        # Handle checkout abandonment tracking
        if (request.path == '/api/incomplete-orders/track-abandonment/' and 
            request.method == 'POST'):
            
            return self._handle_abandonment_tracking(request)
        
        return None
    
    def _handle_abandonment_tracking(self, request):
        """Handle checkout abandonment and create incomplete order"""
        try:
            from django.utils import timezone
            from cart.models import Cart
            from .services import IncompleteOrderService
            
            # Get checkout data from session
            checkout_data = request.session.get('checkout_data')
            if not checkout_data:
                return HttpResponse(json.dumps({'status': 'no_data'}), 
                                  content_type='application/json')
            
            # Get user's cart
            if request.user.is_authenticated:
                try:
                    cart = Cart.objects.get(user=request.user)
                except Cart.DoesNotExist:
                    return HttpResponse(json.dumps({'status': 'no_cart'}), 
                                      content_type='application/json')
            else:
                # Guest user
                session_id = request.session.session_key
                if not session_id:
                    return HttpResponse(json.dumps({'status': 'no_session'}), 
                                      content_type='application/json')
                
                try:
                    cart = Cart.objects.get(session_id=session_id, user=None)
                except Cart.DoesNotExist:
                    return HttpResponse(json.dumps({'status': 'no_cart'}), 
                                      content_type='application/json')
            
            # Check if cart has items
            if not cart.items.exists():
                return HttpResponse(json.dumps({'status': 'empty_cart'}), 
                                  content_type='application/json')
            
            # Check if incomplete order already exists for this cart/session
            from .models import IncompleteOrder
            
            # For authenticated users, check by user
            if request.user.is_authenticated:
                existing_incomplete = IncompleteOrder.objects.filter(
                    user=request.user,
                    status='pending'
                ).first()
            else:
                # For guests, check by session
                existing_incomplete = IncompleteOrder.objects.filter(
                    session_id=session_id,
                    user=None,
                    status='pending'
                ).first()
            
            # If incomplete order already exists, update it
            if existing_incomplete:
                # Update with new checkout data
                self._update_incomplete_order(existing_incomplete, checkout_data)
                incomplete_order = existing_incomplete
            else:
                # Create new incomplete order
                incomplete_order = self._create_incomplete_order(request, cart, checkout_data)
            
            return HttpResponse(json.dumps({
                'status': 'created',
                'incomplete_order_id': incomplete_order.incomplete_order_id
            }), content_type='application/json')
            
        except Exception as e:
            import traceback
            print(f"Error in abandonment tracking: {str(e)}")
            print(traceback.format_exc())
            
            return HttpResponse(json.dumps({'error': str(e)}), 
                              content_type='application/json', 
                              status=500)
    
    def _create_incomplete_order(self, request, cart, checkout_data):
        """Create a new incomplete order from cart and checkout data"""
        from .models import IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress
        from django.utils import timezone
        
        # Prepare customer data
        customer_data = {
            'email': checkout_data.get('email', ''),
            'phone': checkout_data.get('phone_number', ''),
            'notes': checkout_data.get('order_instruction', ''),
        }
        
        # Prepare shipping data
        shipping_data = {}
        if checkout_data.get('full_name'):
            name_parts = checkout_data['full_name'].split(' ', 1)
            shipping_data['first_name'] = name_parts[0]
            shipping_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        
        shipping_data.update({
            'phone': checkout_data.get('phone_number', ''),
            'address_line_1': checkout_data.get('address', ''),
            'city': 'Not specified',  # You might want to add this field to your form
            'postal_code': '',  # You might want to add this field to your form
            'country': 'Bangladesh',  # Default or from form
        })
        
        # Create incomplete order
        order_data = {
            'user': request.user if request.user.is_authenticated else None,
            'is_guest_order': not request.user.is_authenticated,
            'session_id': request.session.session_key,
            'customer_email': customer_data['email'],
            'customer_phone': customer_data['phone'],
            'customer_notes': customer_data['notes'],
            'guest_email': customer_data['email'] if not request.user.is_authenticated else '',
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self._get_client_ip(request),
            'referrer_url': request.META.get('HTTP_REFERER', ''),
        }
        
        incomplete_order = IncompleteOrder.objects.create(**order_data)
        
        # Add cart items to incomplete order
        for cart_item in cart.items.all():
            IncompleteOrderItem.objects.create(
                incomplete_order=incomplete_order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )
        
        # Add shipping address if we have enough data
        if shipping_data.get('first_name') and shipping_data.get('address_line_1'):
            IncompleteShippingAddress.objects.create(
                incomplete_order=incomplete_order,
                **shipping_data
            )
        
        # Calculate totals
        incomplete_order.calculate_totals()
        
        # Mark as abandoned
        incomplete_order.mark_as_abandoned('checkout_form_abandonment')
        
        return incomplete_order
    
    def _update_incomplete_order(self, incomplete_order, checkout_data):
        """Update existing incomplete order with new checkout data"""
        # Update customer data
        if checkout_data.get('email'):
            incomplete_order.customer_email = checkout_data['email']
            if not incomplete_order.user:
                incomplete_order.guest_email = checkout_data['email']
        
        if checkout_data.get('phone_number'):
            incomplete_order.customer_phone = checkout_data['phone_number']
        
        if checkout_data.get('order_instruction'):
            incomplete_order.customer_notes = checkout_data['order_instruction']
        
        incomplete_order.save()
        
        # Update shipping address if exists
        if hasattr(incomplete_order, 'shipping_address'):
            shipping_address = incomplete_order.shipping_address
            
            if checkout_data.get('full_name'):
                name_parts = checkout_data['full_name'].split(' ', 1)
                shipping_address.first_name = name_parts[0]
                shipping_address.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            if checkout_data.get('phone_number'):
                shipping_address.phone = checkout_data['phone_number']
            
            if checkout_data.get('address'):
                shipping_address.address_line_1 = checkout_data['address']
            
            shipping_address.save()
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', '')