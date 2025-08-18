from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from products.models import Product, Category, Review, ReviewImage
from users.models import User
from cart.models import Cart, CartItem
from orders.models import Order


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
    
    context = {
        'cart': cart_obj,
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
        
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Login successful!')
            next_url = request.GET.get('next', 'frontend:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'frontend/auth/login.html')


def user_register(request):
    """User registration page."""
    if request.user.is_authenticated:
        return redirect('frontend:home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('frontend:login')
    
    return render(request, 'frontend/auth/register.html')


@login_required
def profile(request):
    """User profile page."""
    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.phone = request.POST.get('phone', '')
        request.user.save()
        
        # Update profile info
        profile = request.user.profile
        profile.date_of_birth = request.POST.get('date_of_birth') or None
        profile.gender = request.POST.get('gender', '')
        profile.bio = request.POST.get('bio', '')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('frontend:profile')
    
    context = {
        'user': request.user,
        'profile': request.user.profile,
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


@require_http_methods(["POST"])
def submit_review(request, product_id):
    """Submit a product review - supports both authenticated and guest users."""
    try:
        # Debug logging
        print(f"Received review submission for product {product_id}")
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"POST data: {request.POST}")
        print(f"FILES: {request.FILES}")
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get form data
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        guest_name = request.POST.get('guest_name', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        
        # Validation
        errors = {}
        
        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                errors['rating'] = 'Rating must be between 1 and 5.'
        except (ValueError, TypeError):
            errors['rating'] = 'Rating is required.'
        
        # Validate comment
        if not comment:
            errors['comment'] = 'Comment is required.'
        
        # For non-authenticated users, validate guest name
        if not request.user.is_authenticated:
            if not guest_name:
                errors['guest_name'] = 'Name is required for guest reviews.'
        
        if errors:
            print(f"Validation errors: {errors}")
            return JsonResponse({'success': False, 'errors': errors})
        
        # Check if authenticated user already reviewed this product
        if request.user.is_authenticated:
            if Review.objects.filter(user=request.user, product=product).exists():
                print("User already reviewed this product")
                return JsonResponse({
                    'success': False, 
                    'message': 'You have already reviewed this product.'
                })
        
        # Create review
        review_data = {
            'product': product,
            'rating': rating,
            'comment': comment,
        }
        
        if request.user.is_authenticated:
            review_data['user'] = request.user
            
            # Check if user has purchased this product (optional verification)
            try:
                from orders.models import OrderItem
                has_purchased = OrderItem.objects.filter(
                    order__user=request.user,
                    product=product,
                    order__status='delivered'
                ).exists()
                review_data['is_verified_purchase'] = has_purchased
            except:
                pass
        else:
            review_data['guest_name'] = guest_name
            if guest_email:
                review_data['guest_email'] = guest_email
        
        print(f"Creating review with data: {review_data}")
        # Set is_approved to False by default
        review_data['is_approved'] = False
        review = Review.objects.create(**review_data)
        print(f"Review created successfully with ID: {review.id}")
        
        # Handle image uploads
        uploaded_images = request.FILES.getlist('uploaded_images')
        print(f"Processing {len(uploaded_images)} images")
        
        for image in uploaded_images[:5]:  # Limit to 5 images
            review_image = ReviewImage.objects.create(review=review, image=image)
            print(f"Review image created with ID: {review_image.id}")
        
        print("Review submission successful")
        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully!',
            'review_id': review.id
        })
        
    except Exception as e:
        print(f"Error submitting review: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })
