from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import JsonResponse

from products.models import Product, ProductVariant, Category
from orders.models import Order, OrderItem, OrderStatusHistory

# Helper function to check if user is staff
def is_staff(user):
    return user.is_staff

# Dashboard home view
@login_required
@user_passes_test(is_staff)
def dashboard_home(request):
    """
    Main dashboard view showing summary statistics
    """
    # Get current date and 30 days ago for stats
    today = timezone.now().date()
    thirty_days_ago = today - timezone.timedelta(days=30)
    
    # Order statistics
    total_orders = Order.objects.count()
    recent_orders = Order.objects.filter(created_at__date__gte=thirty_days_ago).count()
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Revenue statistics
    total_revenue = Order.objects.filter(status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    recent_revenue = Order.objects.filter(
        status='delivered',
        created_at__date__gte=thirty_days_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Product statistics
    total_products = Product.objects.count()
    out_of_stock = Product.objects.filter(stock_quantity=0).count()
    low_stock = Product.objects.filter(stock_quantity__gt=0, stock_quantity__lt=10).count()
    
    # Chart data for orders by day (last 30 days)
    orders_by_day = []
    for i in range(30):
        date = today - timezone.timedelta(days=i)
        count = Order.objects.filter(created_at__date=date).count()
        orders_by_day.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Chart data for revenue by day (last 30 days)
    revenue_by_day = []
    for i in range(30):
        date = today - timezone.timedelta(days=i)
        revenue = Order.objects.filter(
            created_at__date=date,
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_by_day.append({
            'date': date.strftime('%Y-%m-%d'),
            'amount': float(revenue)
        })
    
    # Recent orders
    latest_orders = Order.objects.order_by('-created_at')[:5]
    
    context = {
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'recent_revenue': recent_revenue,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'orders_by_day': orders_by_day,
        'revenue_by_day': revenue_by_day,
        'latest_orders': latest_orders,
    }
    
    return render(request, 'dashboard/index.html', context)

# Order management views
@login_required
@user_passes_test(is_staff)
def order_list(request):
    """
    List all orders with filtering and search
    """
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status and status != 'all':
        orders = orders.filter(status=status)
    
    # Filter by date range if provided
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    # Search by order number or customer
    search_query = request.GET.get('q')
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(shipping_address__phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get status choices for dropdown
    status_choices = Order._meta.get_field('status').choices
    
    context = {
        'orders': page_obj,
        'status_choices': status_choices,
        'current_status': status,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'dashboard/orders/list.html', context)

@login_required
@user_passes_test(is_staff)
def order_detail(request, pk):
    """
    Display detailed information about an order
    """
    order = get_object_or_404(Order.objects.select_related(
        'user', 'shipping_address'
    ).prefetch_related('items__product', 'items__variant'), pk=pk)
    
    # Get order status history
    status_history = order.status_history.all().order_by('-created_at')
    
    context = {
        'order': order,
        'status_history': status_history,
    }
    
    return render(request, 'dashboard/orders/detail.html', context)

@login_required
@user_passes_test(is_staff)
def update_order_status(request, pk):
    """
    Update the status of an order
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('status')
        
        # Validate the status
        valid_statuses = dict(Order._meta.get_field('status').choices).keys()
        if new_status not in valid_statuses:
            messages.error(request, 'Invalid status selected')
            return redirect('dashboard:order_detail', pk=pk)
        
        # Update the status
        order.status = new_status
        order.save()
        
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=order,
            new_status=new_status,
            notes=request.POST.get('status_notes', ''),
            changed_by=request.user
        )
        
        messages.success(request, f'Order status updated to {new_status}')
        
        # If AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('dashboard:order_detail', pk=pk)
    
    # If not POST, redirect to order detail
    return redirect('dashboard:order_detail', pk=pk)

# Product management views
@login_required
@user_passes_test(is_staff)
def product_list(request):
    """
    List all products with filtering and search
    """
    products = Product.objects.all().select_related('category')
    
    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by stock status if provided
    stock_status = request.GET.get('stock_status')
    if stock_status == 'in_stock':
        products = products.filter(stock_quantity__gt=0)
    elif stock_status == 'out_of_stock':
        products = products.filter(stock_quantity=0)
    elif stock_status == 'low_stock':
        products = products.filter(stock_quantity__gt=0, stock_quantity__lt=10)
    
    # Search by name or description
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for dropdown
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'current_category': category_id,
        'current_stock_status': stock_status,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/products/list.html', context)

@login_required
@user_passes_test(is_staff)
def product_detail(request, pk):
    """
    Display detailed information about a product
    """
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    variants = product.variants.all()
    
    context = {
        'product': product,
        'variants': variants,
    }
    
    return render(request, 'dashboard/products/detail.html', context)

@login_required
@user_passes_test(is_staff)
def product_create(request):
    """
    Create a new product
    """
    if request.method == 'POST':
        # Process form submission (will be expanded later)
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        sku = request.POST.get('sku', '')
        stock_quantity = request.POST.get('stock_quantity', 0)
        
        try:
            category = Category.objects.get(id=category_id)
            
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                sku=sku,
                stock_quantity=stock_quantity,
                is_active=True
            )
            
            # Handle image uploads (will be expanded later)
            if 'main_image' in request.FILES:
                pass  # Process image
            
            messages.success(request, f'Product "{name}" created successfully')
            return redirect('dashboard:product_detail', pk=product.id)
        
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
    
    # Get categories for the form
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'dashboard/products/create.html', context)

@login_required
@user_passes_test(is_staff)
def product_edit(request, pk):
    """
    Edit an existing product
    """
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        # Process form submission (will be expanded later)
        product.name = request.POST.get('name')
        product.description = request.POST.get('description', '')
        product.price = request.POST.get('price')
        category_id = request.POST.get('category')
        product.category = Category.objects.get(id=category_id)
        product.sku = request.POST.get('sku', '')
        product.stock_quantity = request.POST.get('stock_quantity', 0)
        product.is_active = request.POST.get('is_active') == 'on'
        
        try:
            product.save()
            
            # Handle image uploads (will be expanded later)
            if 'main_image' in request.FILES:
                pass  # Process image
            
            messages.success(request, f'Product "{product.name}" updated successfully')
            return redirect('dashboard:product_detail', pk=product.id)
        
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    # Get categories for the form
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'product': product,
        'categories': categories,
    }
    
    return render(request, 'dashboard/products/edit.html', context)

@login_required
@user_passes_test(is_staff)
def product_delete(request, pk):
    """
    Delete a product
    """
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        
        # Instead of deleting, mark as inactive
        product.is_active = False
        product.save()
        
        messages.success(request, f'Product "{product_name}" has been deactivated')
        return redirect('dashboard:product_list')
    
    context = {
        'product': product,
    }
    
    return render(request, 'dashboard/products/delete.html', context)

# Product variant views
@login_required
@user_passes_test(is_staff)
def variant_list(request, product_id):
    """
    List all variants for a product
    """
    product = get_object_or_404(Product, pk=product_id)
    variants = product.variants.all()
    
    context = {
        'product': product,
        'variants': variants,
    }
    
    return render(request, 'dashboard/variants/list.html', context)

@login_required
@user_passes_test(is_staff)
def variant_create(request, product_id):
    """
    Create a new variant for a product
    """
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        # Process form submission (will be expanded later)
        try:
            variant = ProductVariant.objects.create(
                product=product,
                sku=request.POST.get('sku', ''),
                color=request.POST.get('color', ''),
                size=request.POST.get('size', ''),
                weight=request.POST.get('weight') or 0,
                price_adjustment=request.POST.get('price_adjustment') or 0,
                stock_quantity=request.POST.get('stock_quantity') or 0,
                is_active=True
            )
            
            # Handle image uploads (will be expanded later)
            if 'image' in request.FILES:
                pass  # Process image
            
            messages.success(request, f'Variant created successfully')
            return redirect('dashboard:variant_list', product_id=product.id)
        
        except Exception as e:
            messages.error(request, f'Error creating variant: {str(e)}')
    
    context = {
        'product': product,
    }
    
    return render(request, 'dashboard/variants/create.html', context)

@login_required
@user_passes_test(is_staff)
def variant_edit(request, pk):
    """
    Edit an existing product variant
    """
    variant = get_object_or_404(ProductVariant, pk=pk)
    product = variant.product
    
    if request.method == 'POST':
        # Process form submission (will be expanded later)
        try:
            variant.sku = request.POST.get('sku', '')
            variant.color = request.POST.get('color', '')
            variant.size = request.POST.get('size', '')
            variant.weight = request.POST.get('weight') or 0
            variant.price_adjustment = request.POST.get('price_adjustment') or 0
            variant.stock_quantity = request.POST.get('stock_quantity') or 0
            variant.is_active = request.POST.get('is_active') == 'on'
            variant.save()
            
            # Handle image uploads (will be expanded later)
            if 'image' in request.FILES:
                pass  # Process image
            
            messages.success(request, f'Variant updated successfully')
            return redirect('dashboard:variant_list', product_id=product.id)
        
        except Exception as e:
            messages.error(request, f'Error updating variant: {str(e)}')
    
    context = {
        'variant': variant,
        'product': product,
    }
    
    return render(request, 'dashboard/variants/edit.html', context)

@login_required
@user_passes_test(is_staff)
def variant_delete(request, pk):
    """
    Delete a product variant
    """
    variant = get_object_or_404(ProductVariant, pk=pk)
    product = variant.product
    
    if request.method == 'POST':
        # Instead of deleting, mark as inactive
        variant.is_active = False
        variant.save()
        
        messages.success(request, f'Variant has been deactivated')
        return redirect('dashboard:variant_list', product_id=product.id)
    
    context = {
        'variant': variant,
        'product': product,
    }
    
    return render(request, 'dashboard/variants/delete.html', context)
