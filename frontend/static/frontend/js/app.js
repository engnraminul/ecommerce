// Modern eCommerce Frontend JavaScript

// Global variables
let cart = JSON.parse(localStorage.getItem('cart')) || [];
let authToken = localStorage.getItem('authToken') || null;

// Compatibility function for older code still calling renderCartItems
function renderCartItems() {
    console.log("Legacy renderCartItems called, using CartManager instead");
    document.dispatchEvent(new CustomEvent('cartUpdated'));
}

// API Base URL
const API_BASE_URL = '/api/v1';

// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// CSRF token
const csrftoken = getCookie('csrftoken');

// API Helper Functions
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
    };

    if (authToken) {
        defaultOptions.headers['Authorization'] = `Bearer ${authToken}`;
    }

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, finalOptions);
        
        if (!response.ok) {
            // Try to parse error response as JSON
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                // If not JSON, just use an empty object
                errorData = {};
            }
            
            // Extract error message from various formats
            let errorMessage = '';
            if (errorData.message) {
                errorMessage = errorData.message;
            } else if (errorData.error) {
                errorMessage = errorData.error;
            } else if (errorData.detail) {
                errorMessage = errorData.detail;
            } else if (errorData.non_field_errors) {
                errorMessage = errorData.non_field_errors.join(', ');
            } else {
                // For validation errors that are field-specific
                const fieldErrors = [];
                for (const field in errorData) {
                    if (typeof errorData[field] === 'string' || Array.isArray(errorData[field])) {
                        const errorText = Array.isArray(errorData[field]) ? 
                            errorData[field].join(', ') : errorData[field];
                        fieldErrors.push(`${field}: ${errorText}`);
                    }
                }
                
                if (fieldErrors.length > 0) {
                    errorMessage = fieldErrors.join('; ');
                } else {
                    errorMessage = `HTTP error! status: ${response.status}`;
                }
            }
            
            throw new Error(errorMessage);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        // Don't show notification here - let the calling function handle specific error notifications
        throw error;
    }
}

// Notification System
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification fade-in`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.style.maxWidth = '500px';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()">×</button>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, duration);
}

// Helper function to safely update cart UI with CartManager
function safelyUpdateCart() {
    // If CartManager is available, let it handle the update
    if (window.cartManager && typeof window.cartManager.updateCartDisplay === 'function') {
        window.cartManager.updateCartDisplay();
        return;
    }

    // Fallback to basic UI updates if CartManager isn't available
    try {
        // Basic cart count update from local storage
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            const cartItems = JSON.parse(localStorage.getItem('cart') || '[]');
            const totalItems = cartItems.reduce((total, item) => total + (item.quantity || 0), 0);
            cartCount.textContent = totalItems || '0';
        }
    } catch (error) {
        console.error('Error in cart fallback:', error);
    }
}

// Cart Functions
function updateCartUI() {
    try {
        // Update cart count
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            const totalItems = cart.reduce((total, item) => total + (item.quantity || 0), 0);
            cartCount.textContent = totalItems;
        }
        
        // Update cart total display
        const cartTotal = document.querySelector('.cart-total');
        if (cartTotal) {
            const total = cart.reduce((sum, item) => sum + ((item.price || 0) * (item.quantity || 0)), 0);
            cartTotal.textContent = `$${total.toFixed(2)}`;
        }
        
        // Update cart items count display
        const cartItemsCount = document.querySelector('.cart-items-count');
        if (cartItemsCount) {
            const totalItems = cart.reduce((total, item) => total + (item.quantity || 0), 0);
            cartItemsCount.textContent = `${totalItems} items`;
        }
        
        // Trigger cart updated event to refresh navbar
        document.dispatchEvent(new CustomEvent('cartUpdated'));
    } catch (error) {
        console.error('Error updating cart UI:', error);
    }
}

function addToCart(productId, variantId = null, quantity = 1) {
    const existingItem = cart.find(item => 
        item.product_id === productId && item.variant_id === variantId
    );

    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            product_id: productId,
            variant_id: variantId,
            quantity: quantity
        });
    }

    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI();
    showNotification('Item added to cart!', 'success');

    // Sync with backend (works for both authenticated and guest users)
    syncCartWithBackend();
}

function removeFromCart(productId, variantId = null) {
    cart = cart.filter(item => 
        !(item.product_id === productId && item.variant_id === variantId)
    );
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI();
    showNotification('Item removed from cart', 'info');

    // Sync with backend
    syncCartWithBackend();
}

function updateCartQuantity(productId, variantId, quantity) {
    const item = cart.find(item => 
        item.product_id === productId && item.variant_id === variantId
    );
    
    if (item) {
        if (quantity <= 0) {
            removeFromCart(productId, variantId);
        } else {
            item.quantity = quantity;
            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartUI();
            syncCartWithBackend();
        }
    }
}

async function syncCartWithBackend() {
    try {
        // First verify cart items have the correct format
        for (const item of cart) {
            // Make sure all required fields are present
            if (!item.product_id || isNaN(parseInt(item.product_id))) {
                console.error('Invalid cart item:', item);
                continue; // Skip invalid items
            }

            // Create a properly formatted payload for the API
            const payload = {
                product_id: parseInt(item.product_id),
                quantity: item.quantity || 1
            };
            
            // Only include variant_id if it exists and is not null
            if (item.variant_id) {
                payload.variant_id = parseInt(item.variant_id);
            }
            
            // Send the request to add the item
            console.log('Syncing cart item:', payload);
            await apiRequest('/cart/add/', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        }
        
        // After successful sync, trigger cart UI update
        document.dispatchEvent(new CustomEvent('cartUpdated'));
    } catch (error) {
        console.error('Cart sync error:', error);
        
        // Check for specific error messages from the server
        let errorMsg = 'Failed to sync cart with server. Please try again.';
        if (error.message && error.message.includes('Product not found')) {
            errorMsg = 'One or more products in your cart are no longer available.';
        } else if (error.message && error.message.includes('out of stock')) {
            errorMsg = 'Some items in your cart are out of stock.';
        }
        
        showNotification(errorMsg, 'error');
    }
}

// Product Functions
async function loadProducts(filters = {}) {
    const queryParams = new URLSearchParams(filters).toString();
    const url = `/products/${queryParams ? '?' + queryParams : ''}`;
    
    try {
        const data = await apiRequest(url);
        renderProducts(data.results);
    } catch (error) {
        console.error('Failed to load products:', error);
    }
}

function renderProducts(products) {
    const productGrid = document.querySelector('.product-grid');
    if (!productGrid) return;

    productGrid.innerHTML = products.map(product => `
        <div class="product-card fade-in">
            <img src="${product.images[0]?.image || '/static/frontend/images/placeholder.jpg'}" 
                 alt="${product.name}" class="product-image">
            <div class="product-info">
                <h3 class="product-title">${product.name}</h3>
                <p class="product-description">${product.description}</p>
                <div class="product-price">
                    <span class="price-current">$${product.discounted_price || product.price}</span>
                    ${product.discounted_price ? `<span class="price-original">$${product.price}</span>` : ''}
                </div>
                <div class="product-rating">
                    <div class="stars">
                        ${generateStars(product.average_rating)}
                    </div>
                    <span class="rating-count">(${product.review_count})</span>
                </div>
                <div class="product-actions">
                    <button class="btn btn-primary btn-sm" onclick="addToCart(${product.id})">
                        Add to Cart
                    </button>
                    <a href="/products/${product.slug}/" class="btn btn-outline btn-sm">
                        View Details
                    </a>
                </div>
            </div>
        </div>
    `).join('');
}

function generateStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    let stars = '';

    for (let i = 0; i < fullStars; i++) {
        stars += '★';
    }
    
    if (hasHalfStar) {
        stars += '☆';
    }
    
    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
        stars += '☆';
    }
    
    return stars;
}

// Search Functions
function setupSearch() {
    const searchForm = document.querySelector('.search-bar');
    const searchInput = document.querySelector('.search-bar input');
    
    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/products/search/?q=${encodeURIComponent(query)}`;
            }
        });
    }
}

// Authentication Functions
async function login(email, password) {
    try {
        const data = await apiRequest('/auth/token/', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        authToken = data.access;
        localStorage.setItem('authToken', authToken);
        showNotification('Login successful!', 'success');
        
        // Redirect to dashboard or previous page
        window.location.href = '/dashboard/';
    } catch (error) {
        showNotification('Login failed. Please check your credentials.', 'error');
    }
}

async function register(userData) {
    try {
        const data = await apiRequest('/users/register/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        
        showNotification('Registration successful! Please log in.', 'success');
        window.location.href = '/login/';
    } catch (error) {
        showNotification('Registration failed. Please try again.', 'error');
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('cart');
    cart = [];
    showNotification('Logged out successfully', 'info');
    window.location.href = '/';
}

// Form Handlers
function setupForms() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const email = formData.get('email');
            const password = formData.get('password');
            await login(email, password);
        });
    }

    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(registerForm);
            const userData = {
                email: formData.get('email'),
                password: formData.get('password'),
                first_name: formData.get('first_name'),
                last_name: formData.get('last_name'),
                phone: formData.get('phone')
            };
            await register(userData);
        });
    }
}

// Product Filtering
function setupFilters() {
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('change', () => {
            const formData = new FormData(filterForm);
            const filters = {};
            
            for (const [key, value] of formData.entries()) {
                if (value) {
                    filters[key] = value;
                }
            }
            
            loadProducts(filters);
        });
    }
}

// Wishlist Functions
async function addToWishlist(productId) {
    if (!authToken) {
        showNotification('Please log in to add items to wishlist', 'warning');
        return;
    }

    try {
        await apiRequest('/products/wishlist/', {
            method: 'POST',
            body: JSON.stringify({ product_id: productId })
        });
        showNotification('Added to wishlist!', 'success');
    } catch (error) {
        showNotification('Failed to add to wishlist', 'error');
    }
}

// Order Functions
async function createOrder(orderData) {
    try {
        const data = await apiRequest('/orders/create/', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
        
        showNotification('Order placed successfully!', 'success');
        localStorage.removeItem('cart');
        cart = [];
        updateCartUI();
        
        window.location.href = `/orders/${data.id}/`;
    } catch (error) {
        showNotification('Failed to place order. Please try again.', 'error');
    }
}

// Loading States
function showLoading() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.id = 'loadingSpinner';
    document.body.appendChild(spinner);
}

function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Update cart UI on page load - use safe version
    safelyUpdateCart();
    
    // Setup event listeners
    setupSearch();
    setupForms();
    setupFilters();
    
    // Check authentication status
    if (authToken) {
        // Load user data and sync cart
        syncCartWithBackend();
        
        // Update UI for authenticated user
        const loginLinks = document.querySelectorAll('.login-link');
        const logoutLinks = document.querySelectorAll('.logout-link');
        
        loginLinks.forEach(link => link.style.display = 'none');
        logoutLinks.forEach(link => link.style.display = 'block');
    }
    
    // Load initial data based on page
    const productGrid = document.querySelector('.product-grid');
    if (productGrid) {
        loadProducts();
    }
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add fade-in animation to elements as they come into view
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.product-card, .category-card').forEach(el => {
        observer.observe(el);
    });
});

// Handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    // Reload current page content
    window.location.reload();
});

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showNotification('An unexpected error occurred', 'error');
});

// Export functions for global access
window.ecommerceApp = {
    addToCart,
    removeFromCart,
    updateCartQuantity,
    addToWishlist,
    login,
    logout,
    createOrder,
    showNotification,
    renderCartItems, // Add the compatibility function
    // Add reference to cart manager functions
    getCartManager: function() {
        return window.cartManager;
    }
};
