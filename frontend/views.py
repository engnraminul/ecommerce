from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import logging

from products.models import Product, Category, Review
from users.models import User
from cart.models import Cart, CartItem
from orders.models import Order
from pages.models import Page

logger = logging.getLogger(__name__)


def home(request):
    """Homepage view with featured products and categories."""
    featured_products = Product.objects.filter(
        is_featured=True, 
        is_active=True
    ).select_related('category').prefetch_related('images')[:8]
    
    featured_categories = Category.objects.filter(
        is_active=True, 
        parent=None
    )[:6]
    
    context = {
        'featured_products': featured_products,
        'featured_categories': featured_categories,
    }
    return render(request, 'frontend/home.html', context)



def products(request):
    """Products listing page with filters."""
    products_list = Product.objects.filter(is_active=True).select_related(
        'category'
    ).prefetch_related('images')
    
    # Get all categories for filter dropdown
    categories = Category.objects.filter(is_active=True)
    
    # Apply filters
    category_slug = request.GET.get('category')
    if category_slug:
        products_list = products_list.filter(category__slug=category_slug)
    
    min_price = request.GET.get('min_price')
    if min_price:
        try:
            products_list = products_list.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    max_price = request.GET.get('max_price')
    if max_price:
        try:
            products_list = products_list.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    min_rating = request.GET.get('min_rating')
    if min_rating:
        try:
            products_list = products_list.filter(average_rating__gte=float(min_rating))
        except ValueError:
            pass
    
    available_only = request.GET.get('available_only')
    if available_only:
        products_list = products_list.filter(is_active=True, stock_quantity__gt=0)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Ordering
    ordering = request.GET.get('ordering', '-created_at')
    if ordering in ['price', '-price', 'name', '-name', 'rating', '-rating', 'created_at', '-created_at']:
        if ordering in ['rating', '-rating']:
            ordering = ordering.replace('rating', 'average_rating')
        products_list = products_list.order_by(ordering)
    
    # Pagination
    paginator = Paginator(products_list, 12)  # 12 products per page
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    
    context = {
        'products': products_page,
        'categories': categories,
    }
    return render(request, 'frontend/products.html', context)


def product_detail(request, slug):
    """Product detail page."""
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related(
            'images', 'variants', 'reviews__user'
        ), 
        slug=slug,
        is_active=True
    )
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Get all approved reviews for the product
    all_approved_reviews = product.reviews.filter(is_approved=True).select_related('user').prefetch_related('images').order_by('-created_at')
    
    # Get total count of approved reviews
    total_approved_reviews = all_approved_reviews.count()
    
    # Get first 5 reviews for initial display
    initial_reviews = all_approved_reviews[:5]
    
    # Calculate rating distribution
    one_star_count = all_approved_reviews.filter(rating=1).count()
    two_star_count = all_approved_reviews.filter(rating=2).count()
    three_star_count = all_approved_reviews.filter(rating=3).count()
    four_star_count = all_approved_reviews.filter(rating=4).count()
    five_star_count = all_approved_reviews.filter(rating=5).count()
    
    # Calculate percentages for the progress bars
    if total_approved_reviews > 0:
        one_star_percentage = (one_star_count / total_approved_reviews) * 100
        two_star_percentage = (two_star_count / total_approved_reviews) * 100
        three_star_percentage = (three_star_count / total_approved_reviews) * 100
        four_star_percentage = (four_star_count / total_approved_reviews) * 100
        five_star_percentage = (five_star_count / total_approved_reviews) * 100
    else:
        one_star_percentage = two_star_percentage = three_star_percentage = four_star_percentage = five_star_percentage = 0
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': initial_reviews,
        'total_approved_reviews': total_approved_reviews,
        # Add rating distribution data
        'one_star_count': one_star_count,
        'two_star_count': two_star_count,
        'three_star_count': three_star_count,
        'four_star_count': four_star_count,
        'five_star_count': five_star_count,
        'one_star_percentage': one_star_percentage,
        'two_star_percentage': two_star_percentage,
        'three_star_percentage': three_star_percentage,
        'four_star_percentage': four_star_percentage,
        'five_star_percentage': five_star_percentage,
    }
    return render(request, 'frontend/product_detail.html', context)


def categories(request):
    """Categories page."""
    categories_list = Category.objects.filter(
        is_active=True, 
        parent=None
    ).prefetch_related('subcategories', 'products')
    
    # Calculate total products
    total_products = Product.objects.filter(is_active=True).count()
    
    context = {
        'categories': categories_list,
        'total_products': total_products,
    }
    return render(request, 'frontend/categories.html', context)


def category_products(request, slug):
    """Products in a specific category."""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get products in this category or its subcategories
    category_ids = [category.id]
    category_ids.extend(category.subcategories.values_list('id', flat=True))
    
    products_list = Product.objects.filter(
        category_id__in=category_ids,
        is_active=True
    ).select_related('category').prefetch_related('images')
    
    # Apply same filters as products view
    min_price = request.GET.get('min_price')
    if min_price:
        try:
            products_list = products_list.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    max_price = request.GET.get('max_price')
    if max_price:
        try:
            products_list = products_list.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Ordering (updated parameter name from 'ordering' to 'sort' for consistency)
    sort = request.GET.get('sort', '-created_at')
    if sort in ['price', '-price', 'name', '-name', 'rating', '-rating', 'created_at', '-created_at']:
        if sort in ['rating', '-rating']:
            sort = sort.replace('rating', 'average_rating')
        products_list = products_list.order_by(sort)
    
    # Pagination (using 12 products per page which gives 3 rows of 4 on desktop)
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': products_page,
        'is_paginated': products_page.has_other_pages(),
        'page_obj': products_page,
    }
    return render(request, 'frontend/category_products.html', context)


def search(request):
    """Search results page."""
    query = request.GET.get('q', '')
    products_list = Product.objects.none()
    
    if query:
        products_list = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category').prefetch_related('images').distinct()
    
    # Pagination
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'products': products_page,
    }
    return render(request, 'frontend/search.html', context)


def cart(request):
    """Shopping cart page - supports both authenticated and guest users."""
    if request.user.is_authenticated:
        cart_obj, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For guests, get cart by session
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        cart_obj, created = Cart.objects.get_or_create(
            session_id=session_id,
            user=None
        )
    
    context = {
        'cart': cart_obj,
    }
    return render(request, 'frontend/cart.html', context)


def checkout(request):
    """Checkout page - supports both authenticated and guest users."""
    if request.user.is_authenticated:
        cart_obj, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For guests, get cart by session
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        cart_obj, created = Cart.objects.get_or_create(
            session_id=session_id,
            user=None
        )
    
    # Redirect to cart if empty
    if not cart_obj.items.exists():
        messages.warning(request, 'Your cart is empty. Add items before checkout.')
        return redirect('frontend:cart')
    
    # Calculate totals
    cart_items = cart_obj.items.all()
    subtotal = sum(item.total_price for item in cart_items)
    shipping_cost = 0  # You can implement shipping calculation logic here
    total = subtotal + shipping_cost
    
    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
        'is_guest': not request.user.is_authenticated,
    }
    return render(request, 'frontend/checkout.html', context)


def user_login(request):
    """User login page."""
    if request.user.is_authenticated:
        return redirect('frontend:home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'
        
        # First check if user exists and validate credentials
        try:
            existing_user = User.objects.get(email=email)
            
            # Check if password is correct first
            if not existing_user.check_password(password):
                # Wrong password
                logger.warning(f"Wrong password for user {email}")
                messages.error(request, 'Invalid email or password. Please try again.')
                return render(request, 'frontend/auth/login.html')
            
            # Password is correct, now check if email is verified
            if not existing_user.is_email_verified:
                # User exists and password is correct, but email not verified
                logger.info(f"Login attempt with unverified email: {email}")
                messages.error(request, 'Account is not active, please check your email and activate account.')
                return render(request, 'frontend/auth/login.html')
            
            # Both password and email verification are valid, proceed with authentication
            user = authenticate(request, username=email, password=password)
            if user:
                # Authentication successful
                login(request, user)
                
                # Set session expiry based on remember_me
                if not remember_me:
                    # Session expires when browser closes
                    request.session.set_expiry(0)
                else:
                    # Session expires in 30 days (in seconds)
                    request.session.set_expiry(30 * 24 * 60 * 60)
                    
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next', 'frontend:dashboard')
                return redirect(next_url)
            else:
                # This shouldn't happen since we already verified password and email
                logger.error(f"Authentication failed unexpectedly for verified user {email}")
                messages.error(request, 'Authentication error. Please try again.')
                
        except User.DoesNotExist:
            # User doesn't exist
            logger.warning(f"Login attempt with non-existent email: {email}")
            messages.error(request, 'Invalid email or password. Please try again.')
    
    return render(request, 'frontend/auth/login.html')


def user_register(request):
    """User registration page."""
    if request.user.is_authenticated:
        return redirect('frontend:home')
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX request
            import json
            try:
                # Parse JSON data
                data = json.loads(request.body)
                email = data.get('email', '').strip()
                password = data.get('password', '')
                confirm_password = data.get('password_confirm', '')
                first_name = data.get('first_name', '').strip()
                last_name = data.get('last_name', '').strip()
                phone = data.get('phone', '').strip()
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
        else:
            # Handle regular form submission
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone = request.POST.get('phone')
        
        newsletter_subscription = request.POST.get('newsletter_subscription') == 'on'
        terms_accepted = request.POST.get('terms_accepted') == 'on'
        
        # Validation
        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if not terms_accepted and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors.append('You must accept the Terms of Service and Privacy Policy.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if User.objects.filter(email=email).exists():
            errors.append('This email is already registered. Please log in instead.')
        
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': ' '.join(errors)})
            else:
                for error in errors:
                    messages.error(request, error)
        else:
            try:
                # Generate a username from email (before @ symbol)
                username = email.split('@')[0]
                
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create user (inactive until email is verified)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    is_active=True,  # Keep active for login, but require email verification
                    is_email_verified=False  # This prevents login until verified
                )
                
                # Generate email verification token
                user.generate_email_verification_token()
                from django.utils import timezone
                user.email_verification_sent_at = timezone.now()
                user.save(update_fields=['email_verification_sent_at'])
                
                # Send verification email using dashboard email service
                try:
                    from dashboard.email_service import email_service
                    
                    email_sent = email_service.send_activation_email(user)
                    
                    if email_sent:
                        logger.info(f"Email verification sent to {user.email}")
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': True, 
                                'message': 'Registration successful! Please activate your account through the verification email sent to your inbox before logging in.',
                                'redirect_url': f'/email-verification-sent/?email={user.email}',
                                'user_email': user.email
                            })
                        else:
                            from django.http import HttpResponseRedirect
                            from urllib.parse import urlencode
                            return HttpResponseRedirect(f'/email-verification-sent/?{urlencode({"email": user.email})}')
                    else:
                        logger.error(f"Failed to send verification email to {user.email}")
                        # Delete user if email failed to send
                        user.delete()
                        error_msg = 'Registration failed: Unable to send activation email. Please try again.'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'message': error_msg})
                        else:
                            messages.error(request, error_msg)
                            
                except Exception as e:
                    logger.error(f"Error sending verification email: {str(e)}")
                    # Delete user if email failed to send
                    user.delete()
                    error_msg = 'Registration failed: Activation email service error. Please try again.'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': error_msg})
                    else:
                        messages.error(request, error_msg)
                
                # Update newsletter preference if profile model exists
                if hasattr(user, 'profile'):
                    user.profile.newsletter_subscribed = newsletter_subscription
                    user.profile.save()
            except Exception as e:
                error_msg = f'Registration failed. Please try again. Error: {str(e)}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                else:
                    messages.error(request, error_msg)
    
    return render(request, 'frontend/auth/register.html')


@login_required
def dashboard(request):
    """User dashboard page."""
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
    # Get recent orders with select_related to optimize queries
    recent_orders = Order.objects.filter(user=request.user).select_related('shipping_address').order_by('-created_at')[:5]
    
    # Get stats
    order_count = Order.objects.filter(user=request.user).count()
    wishlist_count = request.user.wishlist_items.all().count() if hasattr(request.user, 'wishlist_items') else 0
    
    # Get cart items count
    from cart.models import Cart
    cart_obj, created = Cart.objects.get_or_create(user=request.user)
    cart_items_count = cart_obj.items.count()
    
    # Get recent activities (could be order status changes, etc.)
    recent_activities = []
    for order in recent_orders:
        recent_activities.append({
            'type': 'order',
            'date': order.created_at,
            'message': f'You placed order #{order.order_number}'
        })
    
    context = {
        'recent_orders': recent_orders,
        'order_count': order_count,
        'wishlist_count': wishlist_count,
        'cart_items_count': cart_items_count,
        'recent_activities': sorted(recent_activities, key=lambda x: x['date'], reverse=True)[:5]
    }
    
    return render(request, 'frontend/dashboard.html', context)

@login_required
def profile(request):
    """User profile page with personal info, addresses, security and preferences."""
    from users.models import Address
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm
    from orders.models import Order
    from products.models import Review
    
    # Get counts for statistics
    order_count = Order.objects.filter(user=request.user).count()
    address_count = Address.objects.filter(user=request.user).count()
    reviews_count = Review.objects.filter(user=request.user).count()
    
    # Get addresses
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # Handle personal information form
        if form_type == 'personal':
            # Update user info
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.phone = request.POST.get('phone', '')
            
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                request.user.profile_picture = request.FILES['profile_picture']
                
            # Update date of birth if provided
            date_of_birth = request.POST.get('date_of_birth')
            if date_of_birth:
                request.user.date_of_birth = date_of_birth
                
            request.user.save()
            
            messages.success(request, 'Personal information updated successfully!')
            
        # Handle password change form
        elif form_type == 'password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_new_password')
            
            # Check if current password is correct
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('frontend:profile')
            
            # Check if new passwords match
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return redirect('frontend:profile')
                
            # Validate password complexity
            if (len(new_password) < 8 or
                not any(c.isupper() for c in new_password) or
                not any(c.islower() for c in new_password) or
                not any(c.isdigit() for c in new_password) or
                not any(c in '!@#$%^&*(),.?":{}|<>' for c in new_password)):
                messages.error(request, 'Password does not meet complexity requirements.')
                return redirect('frontend:profile')
                
            # Update password
            request.user.set_password(new_password)
            request.user.save()
            
            # Update session to prevent logout
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Password updated successfully!')
            
        # Handle address form
        elif form_type == 'address':
            address_id = request.POST.get('address_id')
            address_type = request.POST.get('address_type')
            is_default = request.POST.get('is_default') == 'on'
            
            address_data = {
                'address_type': address_type,
                'address_line_1': request.POST.get('address_line_1'),
                'address_line_2': request.POST.get('address_line_2', ''),
                'city': request.POST.get('city'),
                'state': request.POST.get('state'),
                'postal_code': request.POST.get('postal_code'),
                'country': request.POST.get('country'),
                'is_default': is_default,
            }
            
            # If it's default, reset other addresses of same type
            if is_default:
                Address.objects.filter(
                    user=request.user, 
                    address_type=address_type, 
                    is_default=True
                ).update(is_default=False)
            
            # Update existing or create new address
            if address_id:
                address = Address.objects.get(id=address_id, user=request.user)
                for key, value in address_data.items():
                    setattr(address, key, value)
                address.save()
                messages.success(request, 'Address updated successfully!')
            else:
                address_data['user'] = request.user
                Address.objects.create(**address_data)
                messages.success(request, 'Address added successfully!')
                
        # Handle set default address form
        elif form_type == 'set_default_address':
            address_id = request.POST.get('address_id')
            if address_id:
                address = Address.objects.get(id=address_id, user=request.user)
                
                # Reset default for other addresses of same type
                Address.objects.filter(
                    user=request.user, 
                    address_type=address.address_type, 
                    is_default=True
                ).update(is_default=False)
                
                # Set this address as default
                address.is_default = True
                address.save()
                
                messages.success(request, f'Default {address.get_address_type_display()} address updated!')
        
        # Handle delete address form
        elif form_type == 'delete_address':
            address_id = request.POST.get('address_id')
            if address_id:
                address = Address.objects.get(id=address_id, user=request.user)
                
                # Don't allow deletion of default address
                if address.is_default:
                    messages.error(request, 'Cannot delete default address.')
                else:
                    address_type = address.get_address_type_display()
                    address.delete()
                    messages.success(request, f'{address_type} address deleted successfully!')
        
        # Handle preferences form
        elif form_type == 'preferences':
            profile = request.user.profile
            profile.newsletter_subscription = request.POST.get('newsletter_subscription') == 'on'
            profile.email_notifications = request.POST.get('email_notifications') == 'on'
            profile.sms_notifications = request.POST.get('sms_notifications') == 'on'
            profile.preferred_currency = request.POST.get('preferred_currency', 'USD')
            profile.preferred_language = request.POST.get('preferred_language', 'en')
            profile.save()
            
            messages.success(request, 'Preferences updated successfully!')
        
        return redirect('frontend:profile')
    
    context = {
        'user': request.user,
        'addresses': addresses,
        'order_count': order_count,
        'address_count': address_count,
        'reviews_count': reviews_count
    }
    
    return render(request, 'frontend/profile.html', context)


def orders(request):
    """User orders page."""
    if not request.user.is_authenticated:
        # Redirect to login if user is not authenticated
        return redirect('frontend:login')
    
    orders_list = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders_list, 10)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    context = {
        'orders': orders_page,
    }
    return render(request, 'frontend/orders.html', context)


@login_required
def order_detail(request, order_id):
    """Order detail page."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'), 
        id=order_id, 
        user=request.user
    )
    
    context = {
        'order': order,
    }
    return render(request, 'frontend/order_detail.html', context)


def order_confirmation(request, order_number):
    """Order confirmation page - accessible without login."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'), 
        order_number=order_number
    )
    
    context = {
        'order': order,
    }
    return render(request, 'frontend/order_confirmation.html', context)


@login_required
def wishlist(request):
    """User wishlist page."""
    wishlist_items = request.user.wishlist_items.all().select_related(
        'product__category'
    ).prefetch_related('product__images')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'frontend/wishlist.html', context)


def about(request):
    """About page."""
    return render(request, 'frontend/about.html')


def contact(request):
    """Contact page."""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('frontend:contact')
    
    return render(request, 'frontend/contact.html')


def track_order(request):
    """Order tracking page with API endpoint."""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Handle AJAX request
        order_number = request.GET.get('order_number')
        
        try:
            order = Order.objects.select_related(
                'user', 'shipping_address'
            ).prefetch_related(
                'items__product__images',
                'items__variant',
                'status_history'
            ).get(order_number=order_number)
            
            # Prepare order data for JSON response
            order_data = {
                'id': order.id,
                'order_number': order.order_number,
                'created_at': order.created_at.isoformat(),
                'status': order.status,
                'subtotal': float(order.subtotal),
                'shipping_cost': float(order.shipping_cost) if order.shipping_cost else 0.00,
                'tax_amount': float(order.tax_amount) if order.tax_amount else 0.00,
                'total_amount': float(order.total_amount),
                'status_history': [{
                    'status': status.status or status.new_status,
                    'title': status.get_display_title(),
                    'description': status.get_display_description(),
                    'tracking_number': status.tracking_number,
                    'carrier': status.carrier,
                    'carrier_url': status.carrier_url,
                    'location': status.location,
                    'estimated_delivery': status.estimated_delivery.isoformat() if status.estimated_delivery else None,
                    'is_milestone': status.is_milestone,
                    'is_customer_visible': status.is_customer_visible,
                    'created_at': status.created_at.isoformat(),
                    'is_current': status == order.status_history.first()
                } for status in order.status_history.filter(is_customer_visible=True)],
                'items': [{
                    'product': {
                        'name': item.product.name,
                        'image_url': item.product.images.first().image.url if item.product.images.exists() else None
                    },
                    'variant': {
                        'color': item.variant.color if item.variant else None,
                        'size': item.variant.size if item.variant else None
                    } if item.variant else None,
                    'quantity': item.quantity,
                    'total_price': float(item.total_price)
                } for item in order.items.all()],
                'can_cancel': order.can_cancel if hasattr(order, 'can_cancel') else False
            }
            
            return JsonResponse(order_data)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found. Please check your order number and try again.'})
        except Exception as e:
            return JsonResponse({'error': 'An error occurred while retrieving the order information.'})
    
    # Regular page load - show the tracking form
    return render(request, 'frontend/order_tracking_form.html')


def order_tracking(request):
    """Enhanced order tracking page with professional design."""
    return render(request, 'frontend/order_tracking.html')


def load_more_reviews(request, product_id):
    """Load more reviews for a product - used by AJAX for pagination."""
    product = get_object_or_404(
        Product.objects.prefetch_related('reviews__user', 'reviews__images'), 
        id=product_id,
        is_active=True
    )
    
    # Get all approved reviews for the product
    reviews_list = product.reviews.filter(is_approved=True).select_related('user').prefetch_related('images').order_by('-created_at')
    
    # Get total count for accurate display
    total_reviews_count = reviews_list.count()
    
    # Paginate the reviews - 5 per page
    paginator = Paginator(reviews_list, 5)
    page_number = request.GET.get('page', 2)  # Default to page 2 since page 1 is already shown
    
    try:
        page_obj = paginator.get_page(page_number)
    except Exception:
        # Return empty response on error
        return render(request, 'frontend/partials/review_items.html', {
            'reviews': [],
            'has_next': False,
            'total_reviews': total_reviews_count
        })
    
    context = {
        'reviews': page_obj,
        'has_next': page_obj.has_next(),
        'total_reviews': total_reviews_count
    }
    
    return render(request, 'frontend/partials/review_items.html', context)


def find_orders_by_phone(request):
    """API endpoint to find orders by phone number."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            import json
            data = json.loads(request.body)
            phone_number = data.get('phone_number', '').strip()
            
            if not phone_number:
                return JsonResponse({'error': 'Phone number is required'}, status=400)
            
            # Search in both customer_phone and guest phone fields
            orders = Order.objects.filter(
                Q(customer_phone=phone_number) | 
                Q(shipping_address__phone=phone_number)
            ).select_related(
                'shipping_address'
            ).prefetch_related(
                'items__product__images'
            ).order_by('-created_at')
            
            # Prepare orders data for JSON response
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'created_at': order.created_at.isoformat(),
                    'status': order.status,
                    'total_amount': float(order.total_amount),
                    'items': [{
                        'product': {
                            'name': item.product.name,
                            'image_url': item.product.images.first().image.url if item.product.images.exists() else None
                        },
                        'quantity': item.quantity,
                    } for item in order.items.all()]
                })
            
            return JsonResponse({'orders': orders_data})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred while searching for orders'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def load_more_reviews_api(request, product_slug):
    """API endpoint to load more reviews for a product."""
    if request.method == 'GET':
        try:
            print(f"Loading reviews for product: {product_slug}")
            product = get_object_or_404(Product, slug=product_slug, is_active=True)
            print(f"Product found: {product.name}")
            
            # Get pagination parameters
            offset = int(request.GET.get('offset', 5))  # Default to skip first 5
            limit = int(request.GET.get('limit', 5))    # Default to load 5 more
            print(f"Offset: {offset}, Limit: {limit}")
            
            # Get reviews with offset and limit
            reviews = Review.objects.filter(
                product=product, 
                is_approved=True
            ).select_related('user').prefetch_related('images').order_by('-created_at')[offset:offset+limit]
            print(f"Found {reviews.count()} reviews")
            
            # Check if there are more reviews after this batch
            total_reviews = Review.objects.filter(product=product, is_approved=True).count()
            has_more = (offset + limit) < total_reviews
            print(f"Total reviews: {total_reviews}, Has more: {has_more}")
            
            # Prepare reviews data
            reviews_data = []
            for review in reviews:
                try:
                    # Get first image URL if review has images
                    image_url = None
                    if hasattr(review, 'images') and review.images.exists():
                        first_image = review.images.first()
                        if hasattr(first_image, 'image'):
                            image_url = first_image.image.url
                    
                    review_data = {
                        'id': review.id,
                        'user_name': review.user.get_full_name() if review.user else review.guest_name,
                        'rating': review.rating,
                        'comment': review.comment,
                        'created_at': review.created_at.strftime('%B %d, %Y'),
                        'image_url': image_url,
                    }
                    reviews_data.append(review_data)
                    print(f"Added review {review.id}")
                except Exception as e:
                    print(f"Error processing review {review.id}: {e}")
                    continue
            
            print(f"Returning {len(reviews_data)} reviews")
            return JsonResponse({
                'success': True,
                'reviews': reviews_data,
                'has_more': has_more,
                'total_loaded': offset + len(reviews_data),
                'total_reviews': total_reviews
            })
            
        except ValueError as e:
            print(f"ValueError: {e}")
            return JsonResponse({'error': 'Invalid offset or limit parameter'}, status=400)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({'error': 'An error occurred while loading reviews'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@require_http_methods(["POST"])
def submit_review(request, product_id):
    """Submit a review for a product (supports both authenticated and guest users)."""
    try:
        # Get the product
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get form data
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        guest_name = request.POST.get('guest_name', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        
        # Validate required fields
        if not rating:
            return JsonResponse({'success': False, 'errors': {'rating': 'Rating is required'}}, status=400)
        
        if not comment:
            return JsonResponse({'success': False, 'errors': {'comment': 'Comment is required'}}, status=400)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({'success': False, 'errors': {'rating': 'Rating must be between 1 and 5'}}, status=400)
        except ValueError:
            return JsonResponse({'success': False, 'errors': {'rating': 'Invalid rating value'}}, status=400)
        
        # For guest users, require name
        if not request.user.is_authenticated and not guest_name:
            return JsonResponse({'success': False, 'errors': {'guest_name': 'Name is required for guest reviews'}}, status=400)
        
        # Check if authenticated user has already reviewed this product
        if request.user.is_authenticated:
            if Review.objects.filter(user=request.user, product=product).exists():
                return JsonResponse({'success': False, 'errors': {'general': 'You have already reviewed this product'}}, status=400)
        
        # Create the review
        review_data = {
            'product': product,
            'rating': rating,
            'comment': comment,
            'is_approved': True,  # Auto-approve for now
        }
        
        if request.user.is_authenticated:
            review_data['user'] = request.user
            # Check if this is a verified purchase
            from orders.models import OrderItem
            has_purchased = OrderItem.objects.filter(
                order__user=request.user,
                product=product,
                order__status='delivered'
            ).exists()
            review_data['is_verified_purchase'] = has_purchased
        else:
            review_data['guest_name'] = guest_name
            review_data['guest_email'] = guest_email
        
        print(f"Creating review with data: {review_data}")
        # Set is_approved to False by default
        review_data['is_approved'] = False
        
        review = Review.objects.create(**review_data)
        
        # Handle image uploads if any
        uploaded_images = request.FILES.getlist('uploaded_images')
        if uploaded_images:
            from products.models import ReviewImage  # Import here to avoid circular imports
            for image_file in uploaded_images[:5]:  # Limit to 5 images
                if image_file.size <= 5 * 1024 * 1024:  # 5MB limit
                    ReviewImage.objects.create(review=review, image=image_file)
        
        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully! Thank you for your feedback.',
            'review_id': review.id
        })
        
    except Exception as e:
        print(f"Error submitting review: {e}")
        return JsonResponse({
            'success': False, 
            'errors': {'general': 'An error occurred while submitting your review. Please try again.'}
        }, status=500)


def page_detail(request, slug):
    """Page detail view for displaying custom pages."""
    page = get_object_or_404(Page, slug=slug, status='published')
    
    # Check if login is required
    if page.require_login and not request.user.is_authenticated:
        messages.warning(request, 'You need to login to view this page.')
        return redirect('frontend:login')
    
    # Increment view count
    page.view_count += 1
    page.save(update_fields=['view_count'])
    
    # Get related pages from the same category
    related_pages = Page.objects.filter(
        category=page.category,
        status='published'
    ).exclude(id=page.id)[:3] if page.category else []
    
    context = {
        'page': page,
        'related_pages': related_pages,
    }
    
    return render(request, 'frontend/page_detail.html', context)


def forgot_password(request):
    """Forgot password page - send password reset email."""
    if request.user.is_authenticated:
        return redirect('frontend:home')
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX request
            email = request.POST.get('email', '').strip()
            
            if not email:
                return JsonResponse({'success': False, 'message': 'Email address is required'})
            
            try:
                user = User.objects.get(email=email)
                
                # Generate password reset token
                user.generate_password_reset_token()
                user.password_reset_sent_at = timezone.now()
                user.save(update_fields=['password_reset_sent_at'])
                
                # Send password reset email using dashboard email service
                try:
                    from dashboard.email_service import email_service
                    
                    # Create reset URL
                    reset_url = request.build_absolute_uri(
                        f'/reset-password/{user.password_reset_token}/'
                    )
                    
                    # Send email using template
                    email_sent = email_service.send_template_email(
                        template_type='password_reset',
                        recipient_email=user.email,
                        user=user,
                        context={
                            'user': user,
                            'reset_url': reset_url,
                            'reset_token': user.password_reset_token,
                            'site_name': 'Professional eCommerce',
                            'expiry_hours': 24
                        }
                    )
                    
                    if email_sent:
                        logger.info(f"Password reset email sent to {user.email}")
                        return JsonResponse({
                            'success': True, 
                            'message': 'Password reset link has been sent to your email address.'
                        })
                    else:
                        logger.error(f"Failed to send password reset email to {user.email}")
                        return JsonResponse({
                            'success': False, 
                            'message': 'Failed to send reset email. Please try again later.'
                        })
                        
                except Exception as e:
                    logger.error(f"Error sending password reset email: {str(e)}")
                    return JsonResponse({
                        'success': False, 
                        'message': 'Failed to send reset email. Please try again later.'
                    })
                    
            except User.DoesNotExist:
                # Don't reveal that user doesn't exist for security
                return JsonResponse({
                    'success': True, 
                    'message': 'If an account with this email exists, a password reset link has been sent.'
                })
            except Exception as e:
                logger.error(f"Error in forgot password: {str(e)}")
                return JsonResponse({
                    'success': False, 
                    'message': 'An error occurred. Please try again later.'
                })
        
        else:
            # Handle regular form submission
            email = request.POST.get('email', '').strip()
            
            if not email:
                messages.error(request, 'Email address is required.')
                return render(request, 'frontend/auth/forgot_password.html')
            
            try:
                user = User.objects.get(email=email)
                
                # Generate password reset token
                user.generate_password_reset_token()
                user.password_reset_sent_at = timezone.now()
                user.save(update_fields=['password_reset_sent_at'])
                
                # Send password reset email
                try:
                    from dashboard.email_service import email_service
                    
                    reset_url = request.build_absolute_uri(
                        f'/reset-password/{user.password_reset_token}/'
                    )
                    
                    email_sent = email_service.send_template_email(
                        template_type='password_reset',
                        recipient_email=user.email,
                        user=user,
                        context={
                            'user': user,
                            'reset_url': reset_url,
                            'reset_token': user.password_reset_token,
                            'site_name': 'Professional eCommerce',
                            'expiry_hours': 24
                        }
                    )
                    
                    if email_sent:
                        messages.success(request, 'Password reset link has been sent to your email address.')
                    else:
                        messages.error(request, 'Failed to send reset email. Please try again later.')
                        
                except Exception as e:
                    logger.error(f"Error sending password reset email: {str(e)}")
                    messages.error(request, 'Failed to send reset email. Please try again later.')
                    
            except User.DoesNotExist:
                # Don't reveal that user doesn't exist for security
                messages.success(request, 'If an account with this email exists, a password reset link has been sent.')
            except Exception as e:
                logger.error(f"Error in forgot password: {str(e)}")
                messages.error(request, 'An error occurred. Please try again later.')
            
            return render(request, 'frontend/auth/forgot_password.html')
    
    return render(request, 'frontend/auth/forgot_password.html')


def reset_password(request, token):
    """Reset password page with token validation."""
    # Validate token
    valid_token = False
    user = None
    
    try:
        # Find user with this token
        user = User.objects.get(password_reset_token=token)
        
        # Check if token is not expired (24 hours)
        if user.password_reset_sent_at:
            expiry_time = user.password_reset_sent_at + timedelta(hours=24)
            if timezone.now() <= expiry_time:
                valid_token = True
            else:
                logger.info(f"Password reset token expired for user {user.email}")
        else:
            logger.warning(f"Password reset token sent time is None for user {user.email}")
            
    except User.DoesNotExist:
        logger.warning(f"Invalid password reset token: {token}")
    except Exception as e:
        logger.error(f"Error validating reset token: {str(e)}")
    
    if request.method == 'POST' and valid_token:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX request
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validate passwords
            if not new_password or not confirm_password:
                return JsonResponse({
                    'success': False, 
                    'message': 'Both password fields are required'
                })
            
            if new_password != confirm_password:
                return JsonResponse({
                    'success': False, 
                    'message': 'Passwords do not match'
                })
            
            # Validate password complexity
            if (len(new_password) < 8 or
                not any(c.isupper() for c in new_password) or
                not any(c.islower() for c in new_password) or
                not any(c.isdigit() for c in new_password)):
                return JsonResponse({
                    'success': False, 
                    'message': 'Password must be at least 8 characters with uppercase, lowercase, and number'
                })
            
            # Update password
            try:
                user.set_password(new_password)
                user.save()  # Save the password change first
                user.clear_password_reset_token()  # Then clear the token (this saves again)
                
                logger.info(f"Password reset successful for user {user.email}")
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Password reset successfully!'
                })
                
            except Exception as e:
                logger.error(f"Error resetting password: {str(e)}")
                return JsonResponse({
                    'success': False, 
                    'message': 'Failed to reset password. Please try again.'
                })
        
        else:
            # Handle regular form submission
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validate passwords
            if not new_password or not confirm_password:
                messages.error(request, 'Both password fields are required.')
            elif new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
            elif (len(new_password) < 8 or
                  not any(c.isupper() for c in new_password) or
                  not any(c.islower() for c in new_password) or
                  not any(c.isdigit() for c in new_password)):
                messages.error(request, 'Password must be at least 8 characters with uppercase, lowercase, and number.')
            else:
                # Update password
                try:
                    user.set_password(new_password)
                    user.save()  # Save the password change first
                    user.clear_password_reset_token()  # Then clear the token (this saves again)
                    
                    messages.success(request, 'Password reset successfully! You can now login with your new password.')
                    return redirect('frontend:login')
                    
                except Exception as e:
                    logger.error(f"Error resetting password: {str(e)}")
                    messages.error(request, 'Failed to reset password. Please try again.')
    
    context = {
        'valid_token': valid_token,
        'token': token
    }
    
    return render(request, 'frontend/auth/reset_password.html', context)


# Email Verification Views
def email_verification_sent(request):
    """Display email verification sent page"""
    email = request.GET.get('email', '')
    return render(request, 'frontend/auth/email_verification_sent.html', {
        'user_email': email
    })


def verify_email(request, token):
    """Handle email verification link"""
    try:
        user = User.objects.get(email_verification_token=token)
        
        # Check if token is still valid (24 hours)
        if user.is_email_verification_expired():
            logger.warning(f"Expired verification token used for {user.email}")
            messages.error(request, 'This activation link has expired. Please request a new activation email.')
            return redirect('frontend:email_verification_sent')
        
        # Verify the email
        user.verify_email()
        
        logger.info(f"Email verified successfully for {user.email}")
        
        # Show success page
        return render(request, 'frontend/auth/email_verified_success.html', {
            'user': user
        })
        
    except User.DoesNotExist:
        logger.warning(f"Invalid verification token used: {token}")
        messages.error(request, 'Invalid activation link. Please register again or request a new activation email.')
        return redirect('frontend:register')


@require_http_methods(["POST"])
def resend_verification_email(request):
    """Resend email verification"""
    try:
        email = request.POST.get('email')
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email address is required.'
            })
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User with this email address does not exist.'
            })
        
        # Check if email is already verified
        if user.is_email_verified:
            return JsonResponse({
                'success': False,
                'message': 'Your account is already activated. You can login now.'
            })
        
        # Check rate limiting (don't allow resend within 1 minute)
        if user.email_verification_sent_at:
            time_since_last_send = timezone.now() - user.email_verification_sent_at
            if time_since_last_send.total_seconds() < 60:
                remaining_seconds = 60 - int(time_since_last_send.total_seconds())
                return JsonResponse({
                    'success': False,
                    'message': f'Please wait {remaining_seconds} seconds before requesting another verification email.'
                })
        
        # Generate new token and send email
        user.generate_email_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_sent_at'])
        
        # Send verification email
        try:
            from dashboard.email_service import email_service
            
            email_sent = email_service.send_activation_email(user)
            
            if email_sent:
                logger.info(f"Verification email resent to {user.email}")
                return JsonResponse({
                    'success': True,
                    'message': 'Activation email sent successfully! Please check your inbox and click the activation link.'
                })
            else:
                logger.error(f"Failed to resend verification email to {user.email}")
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to send activation email. Please try again later.'
                })
                
        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Email service error. Please try again later.'
            })
    
    except Exception as e:
        logger.error(f"Error in resend_verification_email: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        })
