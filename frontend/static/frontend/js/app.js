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

// Initialize CSRF token
let csrftoken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || '';
console.log('Initial CSRF token:', csrftoken ? 'Found' : 'Not found');

// API Helper Functions
async function apiRequest(url, options = {}) {
    // Get CSRF token from cookie if not already defined
    if (!csrftoken) {
        csrftoken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || '';
        console.log('Retrieved CSRF token:', csrftoken ? 'Found' : 'Not found');
    }
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
    };

    if (authToken) {
        defaultOptions.headers['Authorization'] = `Bearer ${authToken}`;
        console.log('Using existing auth token for request');
    }

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    // For login requests, ensure we're sending the right content type
    if (url.includes('login') || url.includes('token')) {
        console.log('Auth request detected, ensuring Content-Type is set');
        finalOptions.headers['Content-Type'] = 'application/json';
    }

    try {
        // Debug log for request details
        console.log('API Request URL:', `${API_BASE_URL}${url}`);
        console.log('API Request Options:', JSON.stringify({
            method: finalOptions.method,
            headers: finalOptions.headers,
            body: finalOptions.body ? '(data present)' : '(no data)'
        }));
        
        // Special handling for auth endpoints - log full body for debugging
        if (url.includes('/auth/') || url.includes('/login')) {
            try {
                const bodyData = JSON.parse(finalOptions.body);
                console.log('Auth request data:', {
                    ...bodyData,
                    password: bodyData.password ? '********' : undefined // Mask password
                });
            } catch (e) {
                console.log('Could not parse request body for logging:', finalOptions.body);
            }
        }
        
        console.log(`Sending ${finalOptions.method} request to ${API_BASE_URL}${url}`);
        const response = await fetch(`${API_BASE_URL}${url}`, finalOptions);
        console.log('Response status:', response.status, response.statusText);
        
        // Check for redirects (this could happen if CSRF protection kicks in)
        if (response.redirected) {
            console.log('Request was redirected to:', response.url);
            if (url.includes('/auth/') || url.includes('/login')) {
                throw new Error('Authentication request was redirected. Possible CSRF or session issue.');
            }
        }
        
        if (!response.ok) {
            // Try to parse error response as JSON
            let errorData = {};
            let responseErrorMessage = '';
            
            const contentType = response.headers.get('content-type');
            console.log('Error response content type:', contentType);
            
            if (contentType && contentType.includes('application/json')) {
                try {
                    errorData = await response.json();
                    console.log('Error response JSON data:', errorData);
                } catch (e) {
                    console.log('Failed to parse JSON error response:', e);
                }
            } else {
                try {
                    const textResponse = await response.text();
                    console.log('Error response text:', textResponse);
                    responseErrorMessage = `Server error: ${response.status} ${response.statusText}`;
                } catch (textErr) {
                    console.log('Could not get error response text:', textErr);
                    responseErrorMessage = `Request failed with status: ${response.status}`;
                }
            }
            
            // Special handling for auth errors
            if (response.status === 401 || response.status === 403) {
                console.log('Authentication error detected');
                // Clear token if auth error
                if (url.includes('/auth/') || url.includes('/login')) {
                    localStorage.removeItem('authToken');
                    authToken = null;
                    
                    // Don't show notifications here - let Django handle error messages
                    responseErrorMessage = 'Authentication failed';
                }
            }
            
            // Extract error message from various formats
            let errorMessage = responseErrorMessage || '';  // Start with any error message we already have
            console.log('Error response data:', errorData);
            
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
                
                // Special handling for password_confirm field
                if (errorData.password_confirm) {
                    const pwError = Array.isArray(errorData.password_confirm) ? 
                        errorData.password_confirm.join(', ') : errorData.password_confirm;
                    errorMessage = pwError;
                } else if (fieldErrors.length > 0) {
                    errorMessage = fieldErrors.join('; ');
                } else if (!errorMessage) {
                    errorMessage = `HTTP error! status: ${response.status}`;
                }
            }
            
                // For login failures, make sure we have a user-friendly error message
                if (url.includes('/auth/token/') || url.includes('/login')) {
                    // Log the specific error but don't override Django's messages
                    console.error(`Login error details: ${errorMessage}`);
                    // Don't change error message - let Django handle it
                }            throw new Error(errorMessage);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        // Don't show notification here - let the calling function handle specific error notifications
        throw error;
    }
}

// Notification System - expose globally
window.showNotification = function(message, type = 'info', duration = 5000) {
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
            cartTotal.textContent = `৳${total.toFixed(2)}`;
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
                    <span class="price-current">৳${product.discounted_price || product.price}</span>
                    ${product.discounted_price ? `<span class="price-original">৳${product.price}</span>` : ''}
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
// Make login function available globally
window.login = async function(email, password) {
    try {
        console.log('Login attempt with email:', email);
        showNotification('Logging in...', 'info', 2000);
        
        // First try the JWT token endpoint
        try {
            console.log('Attempting JWT token login...');
            const tokenData = await apiRequest('/auth/token/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    username: email, // Django Simple JWT expects username field
                    password: password
                })
            });
            
            console.log('JWT login response:', tokenData);
            
            if (!tokenData || !tokenData.access) {
                console.error('JWT login succeeded but no access token received');
                throw new Error('No access token received');
            }
            
            // Store the JWT token
            authToken = tokenData.access;
            localStorage.setItem('authToken', authToken);
            console.log('Token stored successfully:', authToken.substring(0, 10) + '...');
            
            showNotification('Login successful!', 'success');
            
            // Redirect to dashboard or home page
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
            return true;
        } catch (tokenError) {
            console.error('JWT token login failed, error details:', tokenError);
            // Fall back to traditional login if token auth fails
        }
        
        // Try traditional login endpoint as fallback
        console.log('Attempting traditional login...');
        const loginData = await apiRequest('/users/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                email: email, 
                password: password 
            })
        });
        
        console.log('Traditional login response:', loginData);
        
        // If we reach here, traditional login succeeded
        if (loginData.tokens && loginData.tokens.access) {
            authToken = loginData.tokens.access;
            localStorage.setItem('authToken', authToken);
            console.log('Token stored from traditional login');
        } else {
            console.log('No token in traditional login response');
        }
        
        showNotification('Login successful!', 'success');
        
        // Redirect to dashboard or home page
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        // Don't show notifications here - let Django handle error messages for login forms
        throw error; // Re-throw to allow the calling code to handle it
    }
}

async function register(userData) {
    try {
        // Make sure password_confirm is always explicitly set
        // Create a new object with both password fields to ensure they're included
        const processedData = {
            ...userData,
            password_confirm: userData.password_confirm || userData.password
        };
        
        // Log the data before sending (for debugging)
        console.log('Sending registration data:', JSON.stringify(processedData));
        
        // Make direct fetch request to frontend endpoint (not API endpoint)
        const response = await fetch('/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(processedData)
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            // Show error animation
            if (window.showRegisterError) {
                window.showRegisterError();
            }
            throw new Error(data.message || 'Registration failed');
        }
        
        // Show success animation
        if (window.showRegisterSuccess) {
            window.showRegisterSuccess();
        }
        
        showNotification('Registration successful! Please log in.', 'success');
        
        // Delay redirect to show success animation
        setTimeout(() => {
            window.location.href = '/login/';
        }, 2000);
    } catch (error) {
        console.error('Registration error:', error);
        
        // Show error animation
        if (window.showRegisterError) {
            window.showRegisterError();
        }
        
        // Get detailed error messages if available
        let errorMessage = 'Registration failed: ' + (error.message || '');
        
        // Handle specific error messages more elegantly
        if (error.message.includes("password") && error.message.includes("match")) {
            errorMessage = "Passwords don't match. Please try again.";
        }
        
        // Show the error notification
        showNotification(errorMessage, 'error');
    }
}

function logout() {
    // This function is kept for backwards compatibility
    // But the actual logout is now handled by the event listeners on logout links
    
    // Clear client-side authentication tokens
    authToken = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    
    // Clear cart data
    localStorage.removeItem('cart');
    cart = [];
    
    // Show notification
    showNotification('Logging out...', 'info');
    
    // Return true to allow the default link behavior
    return true;
}

// Form Handlers
function setupForms() {
    // Helper function for email validation
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Login form - COMPLETELY DISABLED: Let Django handle all login form submission
    // The login.html template has its own handler for pure Django form submission
    // Do not interfere with Django login forms at all
    console.log('Login form handling disabled - Django handles all login forms');

    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(registerForm);
            const email = formData.get('email').trim();
            const firstName = formData.get('first_name').trim();
            const lastName = formData.get('last_name').trim();
            const phone = formData.get('phone').trim();
            const password = String(formData.get('password') || '');
            const passwordConfirm = String(formData.get('password_confirm') || '');
            const termsAccepted = formData.get('terms_accepted');
            
            // Clear previous error styling
            document.querySelectorAll('.form-control').forEach(input => {
                input.classList.remove('error');
            });
            
            // Validation
            let isValid = true;
            
            if (!firstName) {
                document.getElementById('first_name').classList.add('error');
                showNotification('First name is required', 'error');
                isValid = false;
            }
            
            if (!lastName) {
                document.getElementById('last_name').classList.add('error');
                showNotification('Last name is required', 'error');
                isValid = false;
            }
            
            if (!email || !isValidEmail(email)) {
                document.getElementById('email').classList.add('error');
                showNotification('Please enter a valid email address', 'error');
                isValid = false;
            }
            
            // Bangladesh phone validation
            const bdPhoneRegex = /(^(\+8801|8801|01)[3-9]{1}[0-9]{8}$)/;
            if (!phone || !bdPhoneRegex.test(phone)) {
                document.getElementById('phone').classList.add('error');
                showNotification('Please enter a valid Bangladesh phone number', 'error');
                isValid = false;
            }
            
            if (!password || password.length < 8) {
                document.getElementById('password').classList.add('error');
                showNotification('Password must be at least 8 characters long', 'error');
                isValid = false;
            }
            
            if (password !== passwordConfirm) {
                document.getElementById('password_confirm').classList.add('error');
                showNotification('Passwords do not match', 'error');
                isValid = false;
            }
            
            if (!termsAccepted) {
                showNotification('Please accept the Terms of Service', 'error');
                isValid = false;
            }
            
            if (!isValid) {
                return false;
            }
            
            // Create user data object
            const userData = {
                email: email,
                password: password,
                password_confirm: passwordConfirm,
                first_name: firstName,
                last_name: lastName,
                phone: phone
            };
            
            console.log('Registration data being sent:', userData);
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
    logout, // This function exists but wasn't properly connected
    createOrder,
    showNotification,
    renderCartItems, // Add the compatibility function
    // Add reference to cart manager functions
    getCartManager: function() {
        return window.cartManager;
    }
};
