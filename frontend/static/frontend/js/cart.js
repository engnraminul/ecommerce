// Cart Management
class CartManager {
    constructor() {
        this.initializeCart();
    }

    async initializeCart() {
        await this.updateCartDisplay();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for cart updates
        document.addEventListener('cartUpdated', () => {
            this.updateCartDisplay();
        });
    }

    async updateCartDisplay() {
        try {
            // Get cart data
            const response = await fetch('/api/v1/cart/');
            if (!response.ok) throw new Error('Failed to fetch cart data');
            
            const cartData = await response.json();
            
            // Get cart summary
            const summaryResponse = await fetch('/api/v1/cart/summary/');
            if (!summaryResponse.ok) throw new Error('Failed to fetch cart summary');
            
            const summaryData = await summaryResponse.json();
            
            // Update the UI with both cart data and summary
            this.updateUI(cartData, summaryData);
        } catch (error) {
            console.error('Error updating cart display:', error);
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
            element.textContent = `$${summaryData.total_amount}`;
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
                                <span class="price">$${item.unit_price}</span>
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

        // Toggle visibility of cart badge based on item count
        const cartBadges = document.querySelectorAll('.action-badge.cart-count');
        cartBadges.forEach(badge => {
            badge.style.display = summaryData.total_items > 0 ? 'flex' : 'none';
        });

        // Update total amount
        const totalAmountElements = document.querySelectorAll('.total-amount');
        totalAmountElements.forEach(element => {
            element.textContent = `$${summaryData.total_amount}`;
        });
    }

    async removeFromCart(itemId) {
        try {
            const response = await fetch(`/api/v1/cart/items/${itemId}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
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

// Initialize cart manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    CartManager.getInstance();
});

// Export for global access
window.cartManager = CartManager.getInstance();
