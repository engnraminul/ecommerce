// Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard JS loaded');
    
    // Function to update recent orders if they're not properly displayed
    function updateRecentOrders() {
        const recentOrdersTable = document.querySelector('.recent-orders table');
        const emptyState = document.querySelector('.recent-orders .empty-state');
        
        if (recentOrdersTable && !recentOrdersTable.querySelector('tbody tr')) {
            console.log('No order rows found, fetching recent orders via API...');
            
            // Show loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading recent orders...';
            loadingDiv.style.textAlign = 'center';
            loadingDiv.style.padding = '2rem';
            
            // Replace the table body with loading indicator
            const tbody = recentOrdersTable.querySelector('tbody');
            if (tbody) {
                tbody.innerHTML = '';
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.setAttribute('colspan', '5');
                td.appendChild(loadingDiv);
                tr.appendChild(td);
                tbody.appendChild(tr);
            }
            
            // Fetch recent orders via API
            fetch('/api/v1/orders/recent/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch recent orders');
                }
                return response.json();
            })
            .then(data => {
                console.log('Recent orders fetched:', data);
                
                // If no orders, show empty state
                if (!data.orders || data.orders.length === 0) {
                    if (emptyState) {
                        emptyState.style.display = 'block';
                    }
                    if (recentOrdersTable) {
                        recentOrdersTable.style.display = 'none';
                    }
                    return;
                }
                
                // Hide empty state
                if (emptyState) {
                    emptyState.style.display = 'none';
                }
                
                // Show table
                if (recentOrdersTable) {
                    recentOrdersTable.style.display = 'table';
                }
                
                // Update table with orders
                const tbody = recentOrdersTable.querySelector('tbody');
                if (tbody) {
                    tbody.innerHTML = '';
                    
                    data.orders.forEach(order => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${order.order_number}</td>
                            <td>${new Date(order.created_at).toLocaleDateString()}</td>
                            <td>
                                <span class="status-badge status-${order.status.toLowerCase()}">
                                    ${order.status_display}
                                </span>
                            </td>
                            <td>$${order.total_amount}</td>
                            <td>
                                <a href="/order/${order.id}/" class="btn-sm btn-outline">
                                    View Details
                                </a>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching recent orders:', error);
                
                // Show error message in table
                const tbody = recentOrdersTable.querySelector('tbody');
                if (tbody) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="5" style="text-align: center; padding: 2rem;">
                                <div class="error-message">
                                    <i class="fas fa-exclamation-circle"></i>
                                    <p>Failed to load recent orders. Please refresh the page and try again.</p>
                                </div>
                            </td>
                        </tr>
                    `;
                }
            });
        }
    }
    
    // Update wishlist count if it's not displayed
    function updateWishlistCount() {
        const wishlistCountElement = document.querySelector('.summary-card .summary-details h3');
        if (wishlistCountElement && wishlistCountElement.textContent === '0' && window.isAuthenticated) {
            // Try to get wishlist count from API
            fetch('/api/v1/products/wishlist/api/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch wishlist count');
                }
                return response.json();
            })
            .then(data => {
                console.log('Wishlist data fetched:', data);
                const count = data.count || data.wishlist_count || (data.items ? data.items.length : 0);
                wishlistCountElement.textContent = count;
                
                // Store count in localStorage for persistence
                localStorage.setItem('wishlistCount', count.toString());
            })
            .catch(error => {
                console.error('Error fetching wishlist count:', error);
                // Try to get from localStorage if API fails
                const savedCount = localStorage.getItem('wishlistCount');
                if (savedCount) {
                    wishlistCountElement.textContent = savedCount;
                }
            });
        }
    }
    
    // Initialize dashboard elements
    function initializeDashboard() {
        // Check if user is authenticated
        window.isAuthenticated = document.body.classList.contains('user-authenticated');
        
        // Wait a bit to ensure other scripts have loaded
        setTimeout(() => {
            updateRecentOrders();
            updateWishlistCount();
        }, 500);
    }
    
    // Initialize dashboard
    initializeDashboard();
});
