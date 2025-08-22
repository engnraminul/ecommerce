document.addEventListener('DOMContentLoaded', function() {
    console.log('Wishlist JS loaded, handling page reload persistence');
    
    // Ensure wishlist count badge is always visible
    const wishlistCount = document.querySelector('.wishlist-count');
    if (wishlistCount) {
        // Always try to get count from localStorage first for immediate display
        const savedCount = localStorage.getItem('wishlistCount');
        if (savedCount) {
            console.log('Retrieved wishlist count from localStorage:', savedCount);
            wishlistCount.textContent = savedCount;
            
            // Also update the items text if it exists
            const wishlistItems = document.querySelector('.wishlist-items');
            if (wishlistItems) {
                wishlistItems.textContent = savedCount + ' items';
            }
        } else {
            console.log('No wishlist count found in localStorage');
        }
        
        // Always make the badge visible
        wishlistCount.style.display = 'flex';
        wishlistCount.style.visibility = 'visible';
        wishlistCount.style.opacity = '1';
    } else {
        console.error('Wishlist count badge element not found');
    }
    
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
                window.location.href = `/login/?next=${currentUrl}`;
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
                // Store in localStorage for persistence
                localStorage.setItem('wishlistCount', data.wishlist_count.toString());
                
                wishlistCount.textContent = data.wishlist_count;
                
                // Always show the badge, even when count is zero
                wishlistCount.style.display = 'flex';
                wishlistCount.style.visibility = 'visible';
                
                // Also update the "X items" text if it exists
                const wishlistItems = document.querySelector('.wishlist-items');
                if (wishlistItems) {
                    wishlistItems.textContent = data.wishlist_count + ' items';
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
        // Helper function to try multiple wishlist endpoints
        function tryFetchWishlist() {
            // Use endpoints that actually return JSON data in your application
            const endpoints = [
                '/api/v1/products/wishlist/api/',  // New API endpoint we just created
            ];
            
            return new Promise((resolve, reject) => {
                // Try each endpoint in sequence
                let currentEndpointIndex = 0;
                
                function tryNextEndpoint() {
                    if (currentEndpointIndex >= endpoints.length) {
                        console.error("All wishlist endpoints failed");
                        reject(new Error("All wishlist endpoints failed"));
                        return;
                    }
                    
                    const endpoint = endpoints[currentEndpointIndex];
                    console.log(`Trying wishlist endpoint: ${endpoint}`);
                    
                    fetch(endpoint, {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        credentials: 'include' // Include cookies in the request
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Endpoint ${endpoint} failed with status ${response.status}`);
                        }
                        
                        // Check if response is JSON before resolving
                        const contentType = response.headers.get('content-type');
                        if (!contentType || !contentType.includes('application/json')) {
                            throw new Error(`Endpoint ${endpoint} returned non-JSON content type: ${contentType}`);
                        }
                        
                        // Return the successful response
                        resolve(response);
                    })
                    .catch(error => {
                        console.error(`Error with endpoint ${endpoint}:`, error);
                        currentEndpointIndex++;
                        tryNextEndpoint();
                    });
                }
                
                tryNextEndpoint();
            });
        }
        
        // Before attempting API calls, set the count from localStorage if available
        const savedCount = localStorage.getItem('wishlistCount');
        if (savedCount) {
            const wishlistCount = document.querySelector('.wishlist-count');
            if (wishlistCount) {
                wishlistCount.textContent = savedCount;
                wishlistCount.style.display = 'flex';
                wishlistCount.style.visibility = 'visible';
                
                const wishlistItems = document.querySelector('.wishlist-items');
                if (wishlistItems) {
                    wishlistItems.textContent = savedCount + ' items';
                }
            }
        }
        
        // Now try the API endpoints
        tryFetchWishlist()
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            // Check content type to make sure we're getting JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Response is not JSON data');
            }
            return response.json();
        })
        .then(data => {
            console.log('Wishlist data received:', data);
            
            // Update the wishlist count badge
            const wishlistCount = document.querySelector('.wishlist-count');
            if (wishlistCount) {
                let count = 0;
                
                // Determine the count based on the data structure
                if (Array.isArray(data)) {
                    count = data.length;
                } else if (data.items && Array.isArray(data.items)) {
                    count = data.items.length;
                } else if (data.count !== undefined) {
                    count = data.count;
                } else if (data.wishlist_count !== undefined) {
                    count = data.wishlist_count;
                }
                
                // Store count in localStorage for persistence after page reload
                localStorage.setItem('wishlistCount', count.toString());
                
                // Update the badge text and always display it
                wishlistCount.textContent = count;
                wishlistCount.style.display = 'flex';
                wishlistCount.style.visibility = 'visible';
                
                // Also update the "X items" text if it exists
                const wishlistItems = document.querySelector('.wishlist-items');
                if (wishlistItems) {
                    wishlistItems.textContent = count + ' items';
                }
            }
            
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
            console.log('Make sure the /api/v1/products/wishlist/api/ endpoint exists and is returning proper JSON data');
            
            // Attempt to create a direct count request as a fallback
            console.log('Attempting alternative approach for wishlist count...');
            
            // Try a simple AJAX request to get just the count
            fetch('/api/v1/products/wishlist/api/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Fallback request failed');
                }
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Response is not JSON data');
                }
                return response.json();
            })
            .then(data => {
                console.log('Fallback request succeeded:', data);
                const count = data.wishlist_count || data.count || 0;
                
                // Save to localStorage for future use
                localStorage.setItem('wishlistCount', count.toString());
                
                // Update the UI
                updateWishlistUIWithCount(count);
            })
            .catch(fallbackError => {
                console.error('Fallback approach also failed:', fallbackError);
                
                // As a last resort, use localStorage
                console.log('Using localStorage as final fallback...');
                const savedCount = localStorage.getItem('wishlistCount') || '0';
                console.log('Retrieved count from localStorage:', savedCount);
                
                // Update the UI using the localStorage value
                updateWishlistUIWithCount(savedCount);
            });
        });
    }
    
    // Helper function to update the wishlist UI with a count
    function updateWishlistUIWithCount(count) {
        // Update the badge
        const wishlistBadge = document.querySelector('.wishlist-count');
        if (wishlistBadge) {
            wishlistBadge.textContent = count;
            wishlistBadge.style.display = 'flex';
            wishlistBadge.style.visibility = 'visible';
            wishlistBadge.style.opacity = '1';
        }
        
        // Update the "X items" text
        const wishlistItems = document.querySelector('.wishlist-items');
        if (wishlistItems) {
            wishlistItems.textContent = count + ' items';
        }
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
    
    // Ensure wishlist count badge is always visible
    window.addEventListener('load', function() {
        const wishlistCount = document.querySelector('.wishlist-count');
        if (wishlistCount) {
            wishlistCount.style.display = 'flex';
            wishlistCount.style.visibility = 'visible';
            wishlistCount.style.opacity = '1';
            
            // Load count from localStorage if available
            const savedCount = localStorage.getItem('wishlistCount');
            if (savedCount) {
                wishlistCount.textContent = savedCount;
                
                // Update items text too
                const wishlistItems = document.querySelector('.wishlist-items');
                if (wishlistItems) {
                    wishlistItems.textContent = savedCount + ' items';
                }
            }
        }
    });
});
