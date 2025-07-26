// Modern eCommerce Frontend JavaScript

// Global variables
let cart = JSON.parse(localStorage.getItem('cart')) || [];
let authToken = localStorage.getItem('authToken') || null;

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
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        showNotification('An error occurred. Please try again.', 'error');
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

// Cart Functions
function updateCartUI() {
    const cartCount = document.querySelector('.cart-count');
    if (cartCount) {
        cartCount.textContent = cart.reduce((total, item) => total + item.quantity, 0);
    }
    
    // Update cart page if we're on it
    const cartContainer = document.querySelector('.cart-items');
    if (cartContainer) {
        renderCartItems();
    }
}

function addToCart(productId, variantId = null, quantity = 1) {
    if (!authToken) {
        showNotification('Please log in to add items to cart', 'warning');
        return;
    }

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

    // Sync with backend
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
    if (!authToken) return;

    try {
        // Add each cart item to backend
        for (const item of cart) {
            await apiRequest('/cart/add/', {
                method: 'POST',
                body: JSON.stringify(item)
            });
        }
    } catch (error) {
        console.error('Cart sync error:', error);
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
    if (!authToken) {
        showNotification('Please log in to place an order', 'warning');
        return;
    }

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
    // Update cart UI on page load
    updateCartUI();
    
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
    showNotification
};
