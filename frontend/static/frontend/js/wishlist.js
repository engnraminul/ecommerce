document.addEventListener('DOMContentLoaded', function() {
    // Select all wishlist buttons on the page
    const wishlistButtons = document.querySelectorAll('.wishlist-btn');
    
    // Add click event listener to each wishlist button
    wishlistButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Check if user is authenticated
            const isAuthenticated = document.body.classList.contains('user-authenticated');
            
            console.log('Auth status:', isAuthenticated);
            
            if (!isAuthenticated) {
                // Redirect to login page with return URL
                const currentUrl = encodeURIComponent(window.location.href);
                window.location.href = `/accounts/login/?next=${currentUrl}`;
                return;
            }
            
            // Get product ID from the button's data attribute
            const productId = this.getAttribute('data-product-id');
            
            // Toggle the heart icon between filled and outline
            const heartIcon = this.querySelector('i');
            const isFilled = heartIcon.classList.contains('fas');
            
            // Toggle button active state
            if (isFilled) {
                heartIcon.classList.replace('fas', 'far');
                button.classList.remove('active');
            } else {
                heartIcon.classList.replace('far', 'fas');
                button.classList.add('active');
            }
            
            // Send request to the server
            toggleWishlistItem(productId, !isFilled, button);
        });
    });
    
    // Function to handle API communication for adding/removing wishlist items
    function toggleWishlistItem(productId, addToWishlist, buttonElement) {
        // Get CSRF token
        const csrftoken = getCookie('csrftoken');
        
        // Debug info
        console.log(`Sending wishlist toggle request for product ID: ${productId}`);
        console.log(`Action: ${addToWishlist ? 'add' : 'remove'}`);
        console.log(`CSRF token: ${csrftoken ? 'Present' : 'Missing'}`);
        
        const apiUrl = `/api/v1/products/${productId}/toggle-wishlist/`;
        
        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                action: addToWishlist ? 'add' : 'remove'
            }),
            credentials: 'include' // Include cookies in the request
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Check the server response to determine the actual action that was performed
            const wasAdded = data.in_wishlist === true;
            const wasRemoved = data.in_wishlist === false;
            
            // Show the appropriate success message based on server response
            if (wasAdded) {
                showNotification('Product added to wishlist!', 'success');
                
                // Make sure button state reflects that the item is in wishlist
                if (buttonElement) {
                    const icon = buttonElement.querySelector('i');
                    if (icon && !icon.classList.contains('fas')) {
                        icon.classList.replace('far', 'fas');
                    }
                    buttonElement.classList.add('active');
                }
                
            } else if (wasRemoved) {
                showNotification('Product removed from wishlist!', 'success');
                
                // Make sure button state reflects that the item is not in wishlist
                if (buttonElement) {
                    const icon = buttonElement.querySelector('i');
                    if (icon && !icon.classList.contains('far')) {
                        icon.classList.replace('fas', 'far');
                    }
                    buttonElement.classList.remove('active');
                }
            }
            
            // Update the wishlist count in header if exists
            const wishlistCount = document.querySelector('.wishlist-count');
            if (wishlistCount && data.wishlist_count !== undefined) {
                wishlistCount.textContent = data.wishlist_count;
                
                // If wishlist count is zero, hide the count badge
                if (data.wishlist_count === 0) {
                    wishlistCount.style.display = 'none';
                } else {
                    wishlistCount.style.display = 'inline-block';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            console.log('Error details:', error.message);
            
            // Show detailed error message for debugging
            if (error.message === 'Failed to fetch') {
                console.log('Network error - Check API endpoint URL and server status');
                showNotification('Network error. Please check your connection and try again.', 'error');
            } else {
                console.log('Other error:', error.message);
                showNotification('Something went wrong. Please try again.', 'error');
            }
            
            // Revert the heart icon and button state to its previous state
            if (buttonElement) {
                const heartIcon = buttonElement.querySelector('i');
                if (heartIcon) {
                    if (addToWishlist) {
                        heartIcon.classList.replace('fas', 'far');
                        buttonElement.classList.remove('active');
                    } else {
                        heartIcon.classList.replace('far', 'fas');
                        buttonElement.classList.add('active');
                    }
                }
            }
        });
    }
    
    // Initialize wishlist buttons to show the correct state
    function initWishlistButtons() {
        // Check if user is authenticated
        const isAuthenticated = document.body.classList.contains('user-authenticated');
        
        console.log('Init wishlist buttons, user authenticated:', isAuthenticated);
        
        if (!isAuthenticated) {
            console.log('User not authenticated, skipping wishlist fetch');
            return; // Don't fetch wishlist for non-authenticated users
        }
        
        // Use the correct API endpoint for wishlist
        console.log('Fetching wishlist items from API...');
        fetch('/api/v1/products/wishlist/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'include' // Include cookies in the request
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Wishlist data received:', data);
            // The response is directly an array of wishlist items
            if (Array.isArray(data)) {
                data.forEach(item => {
                    // The product ID is in item.product.id or item.product_id
                    const productId = item.product?.id || item.product_id;
                    if (productId) {
                        const button = document.querySelector(`.wishlist-btn[data-product-id="${productId}"]`);
                        if (button) {
                            const icon = button.querySelector('i');
                            if (icon) {
                                icon.classList.replace('far', 'fas');
                            }
                            // Add active class to the button
                            button.classList.add('active');
                        }
                    }
                });
            } else if (data.items && Array.isArray(data.items)) {
                // Alternative format with items property
                data.items.forEach(item => {
                    const button = document.querySelector(`.wishlist-btn[data-product-id="${item.product_id}"]`);
                    if (button) {
                        const icon = button.querySelector('i');
                        if (icon) {
                            icon.classList.replace('far', 'fas');
                        }
                        // Add active class to the button
                        button.classList.add('active');
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error fetching wishlist items:', error);
            console.log('Error message:', error.message);
            console.log('Make sure the /api/v1/products/wishlist/ endpoint exists and is returning proper data');
        });
    }
    
    // Helper function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Function to show notification
    function showNotification(message, type = 'success') {
        // Check if showNotification is already defined globally
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
        } else {
            // Create and show a notification if the global function doesn't exist
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${message}</span>
            `;
            
            // Add CSS styles for the animation
            if (!document.getElementById('notification-styles')) {
                const styleEl = document.createElement('style');
                styleEl.id = 'notification-styles';
                styleEl.textContent = `
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    @keyframes slideOut {
                        from { transform: translateX(0); opacity: 1; }
                        to { transform: translateX(100%); opacity: 0; }
                    }
                `;
                document.head.appendChild(styleEl);
            }
            
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? '#28a745' : '#dc3545'};
                color: white;
                padding: 15px 20px;
                border-radius: 5px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                z-index: 10000;
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                animation: slideIn 0.3s ease;
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }
    }
    
    // Initialize wishlist buttons when the page loads
    initWishlistButtons();
});
