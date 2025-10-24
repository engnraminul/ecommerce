// Cart Management
class CartManager {
    constructor() {
        // We'll initialize manually to have better control
    }

    async initializeCart() {
        try {
            await this.updateCartDisplay();
            this.setupEventListeners();
            console.log('Cart manager initialized successfully');
        } catch (error) {
            console.error('Error initializing cart manager:', error);
            // Still set up event listeners even if initial display fails
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        // Listen for cart updates
        document.addEventListener('cartUpdated', () => {
            this.updateCartDisplay();
        });
    }

    async updateCartDisplay() {
        try {
            console.log('Updating cart display...');
            // Prepare headers with CSRF token
            const headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            };
            
            // Get cart data - handle both API endpoints for compatibility
            let cartData;
            try {
                // Try the new API endpoint first
                const response = await fetch('/api/v1/cart/', { 
                    headers,
                    // Add cache busting parameter
                    cache: 'no-store'
                });
                if (!response.ok) throw new Error(`Failed to fetch cart data: ${response.status}`);
                cartData = await response.json();
                console.log('Cart data from v1 API:', cartData);
            } catch (error) {
                console.error('Failed to fetch cart data:', error);
                // Default empty cart if API fails
                cartData = { items: [] };
            }
            
            // Get cart summary - handle both endpoints for compatibility
            let summaryData;
            try {
                const summaryResponse = await fetch('/api/v1/cart/summary/', { 
                    headers,
                    cache: 'no-store'
                });
                if (!summaryResponse.ok) throw new Error(`Failed to fetch cart summary: ${summaryResponse.status}`);
                summaryData = await summaryResponse.json();
                console.log('Summary data:', summaryData);
            } catch (error) {
                console.warn('Failed to fetch summary, using fallback:', error);
                // Calculate summary from cart data as fallback
                summaryData = {
                    total_items: cartData.items ? cartData.items.reduce((total, item) => total + (item.quantity || 0), 0) : 0,
                    total_amount: cartData.items ? cartData.items.reduce((sum, item) => 
                        sum + ((item.price || item.unit_price || 0) * (item.quantity || 0)), 0).toFixed(2) : '0.00'
                };
            }
            
            // Update the UI with both cart data and summary
            this.updateUI(cartData, summaryData);
            
            // Notify app.js that cart data is updated
            window.cart = cartData.items || [];
            localStorage.setItem('cart', JSON.stringify(window.cart));
            
        } catch (error) {
            console.error('Critical error updating cart display:', error);
            // Show empty cart as fallback
            this.updateUI({ items: [] }, { total_items: 0, total_amount: '0.00' });
            
            // Show user-friendly error if notification function exists
            if (typeof showNotification === 'function') {
                showNotification('Failed to load cart data. Please try again.', 'error');
            }
        }
    }

    updateUI(cartData, summaryData) {
        // Update all cart count displays
        const cartCountElements = document.querySelectorAll('.cart-count');
        cartCountElements.forEach(element => {
            element.textContent = summaryData.total_items || '0';
        });

        // Update cart total
        const cartTotalElements = document.querySelectorAll('.cart-total');
        cartTotalElements.forEach(element => {
            element.textContent = `৳${summaryData.total_amount}`;
        });

        // Update items count in dropdown
        const cartItemsCountElements = document.querySelectorAll('.cart-items-count');
        cartItemsCountElements.forEach(element => {
            element.textContent = `${summaryData.total_items || 0} items`;
        });

        // Update cart dropdown content
        const cartDropdownBody = document.querySelector('.cart-dropdown-body');
        if (cartDropdownBody) {
            if (cartData.items && cartData.items.length > 0) {
                const cartItemsHtml = cartData.items.map(item => `
                    <div class="cart-item">
                        <div class="cart-item-image">
                            ${item.product_image ? 
                                `<img src="${item.product_image}" alt="${item.product_name}">` :
                                '<div class="placeholder-image"><i class="fas fa-image"></i></div>'
                            }
                        </div>
                        <div class="cart-item-details">
                            <h6>${item.product_name}</h6>
                            ${item.variant_name ? 
                                `<p class="cart-item-variant">${item.variant_name}</p>` : 
                                ''
                            }
                            <div class="cart-item-price">
                                <span class="quantity">${item.quantity}×</span>
                                <span class="price">৳${item.unit_price}</span>
                            </div>
                        </div>
                        <button class="cart-item-remove" onclick="cartManager.removeFromCart(${item.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `).join('');
                
                cartDropdownBody.innerHTML = cartItemsHtml;
            } else {
                cartDropdownBody.innerHTML = `
                    <div class="empty-cart">
                        <i class="fas fa-shopping-cart"></i>
                        <p>Your cart is empty</p>
                        <a href="/products/" class="btn-shop-now">Shop Now</a>
                    </div>
                `;
            }
        }

        // Always show cart badge, even when count is zero
        const cartBadges = document.querySelectorAll('.action-badge.cart-count');
        cartBadges.forEach(badge => {
            badge.style.display = 'flex'; // Always show the badge
        });

        // Update total amount
        const totalAmountElements = document.querySelectorAll('.total-amount');
        totalAmountElements.forEach(element => {
            element.textContent = `৳${summaryData.total_amount}`;
        });
    }

    async removeFromCart(itemId) {
        try {
            const response = await fetch(`/api/v1/cart/items/${itemId}/remove/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to remove item from cart');
            }

            // Update the cart display after removing the item
            await this.updateCartDisplay();

            // Show success message if notification function exists
            if (typeof showNotification === 'function') {
                showNotification('Item removed from cart', 'success');
            }
        } catch (error) {
            console.error('Error removing item from cart:', error);
            if (typeof showNotification === 'function') {
                showNotification('Failed to remove item from cart', 'error');
            }
        }
    }

    static getInstance() {
        if (!CartManager.instance) {
            CartManager.instance = new CartManager();
        }
        return CartManager.instance;
    }
}

// CSRF token extraction helper
function getCSRFToken() {
    // First try to get from cookie
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    // Then try from meta tag
    if (!cookieValue) {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) return metaTag.getAttribute('content');
    }
    
    // Then try from hidden input
    if (!cookieValue) {
        const inputTag = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (inputTag) return inputTag.value;
    }
    
    // Finally try from window variable
    return cookieValue || window.csrfToken || '';
}

// Make sure cart manager is initialized as soon as possible
(function() {
    // Create and initialize cart manager immediately
    try {
        console.log('Initializing CartManager...');
        const cartManager = CartManager.getInstance();
        window.cartManager = cartManager;
        
        // When DOM is ready, set up event listeners
        document.addEventListener('DOMContentLoaded', () => {
            cartManager.initializeCart().catch(error => {
                console.error('Error during cart initialization:', error);
            });
            
            // Dispatch a custom event that cart system is ready
            document.dispatchEvent(new CustomEvent('cartManagerReady'));
        });
    } catch (error) {
        console.error('Critical error setting up CartManager:', error);
    }
})();
