// Professional Navbar JavaScript

class NavbarManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupMobileMenu();
        this.setupDropdowns();
        this.setupSearch();
        this.setupScrollEffect();
        this.setupCartPreview();
        this.setupSearchSuggestions();
    }

    // Mobile Menu Management
    setupMobileMenu() {
        const menuToggle = document.querySelector('.menu-toggle-btn');
        const mobileMenuOverlay = document.querySelector('.mobile-menu-overlay');
        const mobileMenuClose = document.querySelector('.mobile-menu-close');

        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                this.toggleMobileMenu();
            });
        }

        if (mobileMenuClose) {
            mobileMenuClose.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }

        if (mobileMenuOverlay) {
            mobileMenuOverlay.addEventListener('click', (e) => {
                if (e.target === mobileMenuOverlay) {
                    this.closeMobileMenu();
                }
            });
        }

        // Close mobile menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeMobileMenu();
            }
        });
    }

    toggleMobileMenu() {
        const overlay = document.querySelector('.mobile-menu-overlay');
        const body = document.body;
        
        if (overlay) {
            overlay.classList.toggle('active');
            body.style.overflow = overlay.classList.contains('active') ? 'hidden' : '';
        }
    }

    closeMobileMenu() {
        const overlay = document.querySelector('.mobile-menu-overlay');
        const body = document.body;
        
        if (overlay) {
            overlay.classList.remove('active');
            body.style.overflow = '';
        }
    }

    // Dropdown Management
    setupDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown, .category-menu, .user-dropdown, .cart');
        
        dropdowns.forEach(dropdown => {
            let hoverTimeout;
            
            dropdown.addEventListener('mouseenter', () => {
                clearTimeout(hoverTimeout);
                this.showDropdown(dropdown);
            });
            
            dropdown.addEventListener('mouseleave', () => {
                hoverTimeout = setTimeout(() => {
                    this.hideDropdown(dropdown);
                }, 300);
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.dropdown, .category-menu, .user-dropdown, .cart')) {
                this.hideAllDropdowns();
            }
        });
    }

    showDropdown(dropdown) {
        const menu = dropdown.querySelector('.dropdown-menu, .category-dropdown, .user-menu, .cart-dropdown');
        if (menu) {
            menu.style.opacity = '1';
            menu.style.visibility = 'visible';
            menu.style.transform = 'translateY(0)';
        }
    }

    hideDropdown(dropdown) {
        const menu = dropdown.querySelector('.dropdown-menu, .category-dropdown, .user-menu, .cart-dropdown');
        if (menu) {
            menu.style.opacity = '0';
            menu.style.visibility = 'hidden';
            menu.style.transform = 'translateY(-10px)';
        }
    }

    hideAllDropdowns() {
        const menus = document.querySelectorAll('.dropdown-menu, .category-dropdown, .user-menu, .cart-dropdown');
        menus.forEach(menu => {
            menu.style.opacity = '0';
            menu.style.visibility = 'hidden';
            menu.style.transform = 'translateY(-10px)';
        });
    }

    // Search Functionality
    setupSearch() {
        const searchForm = document.querySelector('.search-form');
        const searchInput = document.querySelector('.search-input');
        const categorySelect = document.querySelector('.category-select');

        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.performSearch();
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });
            
            searchInput.addEventListener('focus', () => {
                this.showSearchSuggestions();
            });
        }

        if (categorySelect) {
            categorySelect.addEventListener('change', () => {
                this.updateSearchPlaceholder();
            });
        }
    }

    performSearch() {
        const searchInput = document.querySelector('.search-input');
        const categorySelect = document.querySelector('.category-select');
        
        if (searchInput && searchInput.value.trim()) {
            const query = searchInput.value.trim();
            const category = categorySelect ? categorySelect.value : '';
            
            // Build search URL
            const params = new URLSearchParams();
            params.append('q', query);
            if (category) {
                params.append('category', category);
            }
            
            // Redirect to search results
            window.location.href = `/search/?${params.toString()}`;
        }
    }

    handleSearchInput(value) {
        if (value.length >= 2) {
            this.fetchSearchSuggestions(value);
        } else {
            this.hideSearchSuggestions();
        }
    }

    updateSearchPlaceholder() {
        const searchInput = document.querySelector('.search-input');
        const categorySelect = document.querySelector('.category-select');
        
        if (searchInput && categorySelect) {
            const category = categorySelect.selectedOptions[0]?.text || 'All Categories';
            searchInput.placeholder = `Search in ${category}...`;
        }
    }

    // Search Suggestions
    setupSearchSuggestions() {
        // Create suggestions container if it doesn't exist
        let suggestionsContainer = document.querySelector('.search-suggestions');
        if (!suggestionsContainer) {
            suggestionsContainer = document.createElement('div');
            suggestionsContainer.className = 'search-suggestions';
            
            const searchWrapper = document.querySelector('.search-input-wrapper');
            if (searchWrapper) {
                searchWrapper.appendChild(suggestionsContainer);
            }
        }
    }

    async fetchSearchSuggestions(query) {
        try {
            const response = await fetch(`/api/search/suggestions/?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const suggestions = await response.json();
                this.displaySearchSuggestions(suggestions);
            }
        } catch (error) {
            console.error('Error fetching search suggestions:', error);
        }
    }

    displaySearchSuggestions(suggestions) {
        const container = document.querySelector('.search-suggestions');
        if (!container) return;

        container.innerHTML = '';
        
        if (suggestions.length > 0) {
            suggestions.forEach(suggestion => {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.innerHTML = `
                    <i class="fas fa-search"></i>
                    <span>${suggestion.name}</span>
                `;
                
                item.addEventListener('click', () => {
                    document.querySelector('.search-input').value = suggestion.name;
                    this.performSearch();
                });
                
                container.appendChild(item);
            });
            
            this.showSearchSuggestions();
        } else {
            this.hideSearchSuggestions();
        }
    }

    showSearchSuggestions() {
        const container = document.querySelector('.search-suggestions');
        if (container) {
            container.style.display = 'block';
        }
    }

    hideSearchSuggestions() {
        const container = document.querySelector('.search-suggestions');
        if (container) {
            container.style.display = 'none';
        }
    }

    // Scroll Effects
    setupScrollEffect() {
        let lastScrollY = window.scrollY;
        const navbar = document.querySelector('.navbar-wrapper');
        
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            
            if (navbar) {
                if (currentScrollY > 100) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
                
                // Hide/show navbar on scroll
                if (currentScrollY > lastScrollY && currentScrollY > 200) {
                    navbar.style.transform = 'translateY(-100%)';
                } else {
                    navbar.style.transform = 'translateY(0)';
                }
            }
            
            lastScrollY = currentScrollY;
        });
    }

    // Cart Preview Management
    setupCartPreview() {
        this.updateCartDisplay();
        
        // Listen for cart updates
        document.addEventListener('cartUpdated', () => {
            this.updateCartDisplay();
        });
    }

    async updateCartDisplay() {
        try {
            const response = await fetch('/api/v1/cart/summary/');
            if (response.ok) {
                const cartData = await response.json();
                this.renderCartPreview(cartData);
            }
        } catch (error) {
            console.error('Error updating cart display:', error);
        }
    }

    renderCartPreview(cartData) {
        // Update cart count
        const cartCount = document.querySelector('.cart .action-count');
        const cartBadge = document.querySelector('.cart .action-badge');
        
        if (cartCount) {
            cartCount.textContent = `${cartData.total_items || 0} items`;
        }
        
        if (cartBadge) {
            cartBadge.textContent = cartData.total_items || 0;
            cartBadge.style.display = (cartData.total_items > 0) ? 'flex' : 'none';
        }

        // Update cart dropdown
        const cartBody = document.querySelector('.cart-dropdown-body');
        const cartTotal = document.querySelector('.cart-total-display');
        
        if (cartBody) {
            if (cartData.items && cartData.items.length > 0) {
                cartBody.innerHTML = cartData.items.map(item => `
                    <div class="cart-item" data-item-id="${item.id}">
                        <div class="cart-item-image">
                            <img src="${item.image}" alt="${item.name}">
                        </div>
                        <div class="cart-item-details">
                            <h6>${item.name}</h6>
                            <p class="cart-item-variant">${item.variant}</p>
                            <div class="cart-item-price">
                                <span class="quantity">${item.quantity}x</span>
                                <span class="price">$${item.price}</span>
                            </div>
                        </div>
                        <button class="cart-item-remove" onclick="removeFromCart(${item.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `).join('');
            } else {
                cartBody.innerHTML = `
                    <div class="empty-cart">
                        <i class="fas fa-shopping-bag"></i>
                        <p>Your cart is empty</p>
                        <a href="/products/" class="btn-shop-now">Shop Now</a>
                    </div>
                `;
            }
        }
        
        if (cartTotal) {
            cartTotal.innerHTML = `
                <span>Total: <strong>$${cartData.total}</strong></span>
            `;
        }
    }

    // Active Navigation Management
    setActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    // Currency and Language Handlers
    setupCurrencyLanguage() {
        const currencySelect = document.querySelector('.currency-selector select');
        const languageSelect = document.querySelector('.language-selector select');
        
        if (currencySelect) {
            currencySelect.addEventListener('change', (e) => {
                this.updateCurrency(e.target.value);
            });
        }
        
        if (languageSelect) {
            languageSelect.addEventListener('change', (e) => {
                this.updateLanguage(e.target.value);
            });
        }
    }

    updateCurrency(currency) {
        // Update currency preference
        localStorage.setItem('preferred_currency', currency);
        
        // Reload page to apply new currency
        window.location.reload();
    }

    updateLanguage(language) {
        // Update language preference
        localStorage.setItem('preferred_language', language);
        
        // Redirect to language-specific URL
        window.location.href = `/${language}${window.location.pathname}`;
    }
}

// Global cart functions
window.removeFromCart = async function(itemId) {
    try {
        const response = await fetch(`/api/cart/remove/${itemId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                'Content-Type': 'application/json',
            },
        });
        
        if (response.ok) {
            // Trigger cart update event
            document.dispatchEvent(new CustomEvent('cartUpdated'));
            
            // Show success message
            showNotification('Item removed from cart', 'success');
        }
    } catch (error) {
        console.error('Error removing item from cart:', error);
        showNotification('Error removing item from cart', 'error');
    }
};

// Notification system
window.showNotification = function(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}"></i>
        <span>${message}</span>
        <button class="notification-close">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
    
    // Manual close
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
};

// Initialize navbar when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const navbar = new NavbarManager();
    navbar.setActiveNavigation();
    navbar.setupCurrencyLanguage();
});

// Handle window resize
window.addEventListener('resize', () => {
    const navbar = document.querySelector('.navbar-wrapper');
    if (window.innerWidth > 768) {
        // Close mobile menu on desktop
        document.querySelector('.mobile-menu-overlay')?.classList.remove('active');
        document.body.style.overflow = '';
    }
});
