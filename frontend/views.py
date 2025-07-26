from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from products.models import Product, Category, Review
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
    
    context = {
        'product': product,
        'related_products': related_products,
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


@login_required
def cart(request):
    """Shopping cart page."""
    cart_obj, created = Cart.objects.get_or_create(user=request.user)
    
    context = {
        'cart': cart_obj,
    }
    return render(request, 'frontend/cart.html', context)


@login_required
def checkout(request):
    """Checkout page."""
    cart_obj, created = Cart.objects.get_or_create(user=request.user)
    
    # Redirect to cart if empty
    if not cart_obj.items.exists():
        messages.warning(request, 'Your cart is empty. Add items before checkout.')
        return redirect('frontend:cart')
    
    context = {
        'cart': cart_obj,
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
