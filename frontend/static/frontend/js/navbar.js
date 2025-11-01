// Professional Navbar JavaScript

class NavbarManager {
    constructor() {
        this.searchTimeout = null; // Initialize search timeout
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
        const menuToggle = document.querySelector('#mobileMenuToggle');
        const mobileMenuOverlay = document.querySelector('#mobileMenuOverlay');
        const mobileMenuClose = document.querySelector('#mobileMenuClose');
        const mobileMenu = document.querySelector('#mobileMenu');

        console.log('Setting up mobile menu...');
        console.log('Menu toggle:', menuToggle);
        console.log('Menu overlay:', mobileMenuOverlay);
        console.log('Menu close:', mobileMenuClose);
        console.log('Mobile menu:', mobileMenu);

        if (menuToggle) {
            console.log('Adding click listener to menu toggle');
            menuToggle.addEventListener('click', (e) => {
                console.log('Menu toggle clicked!');
                e.preventDefault();
                e.stopPropagation();
                this.toggleMobileMenu();
            });
        } else {
            console.error('Menu toggle button not found!');
        }

        if (mobileMenuClose) {
            mobileMenuClose.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
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

        // Prevent menu clicks from closing the menu
        if (mobileMenu) {
            mobileMenu.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

        // Close mobile menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeMobileMenu();
            }
        });

        // Close mobile menu when clicking on nav links
        const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', () => {
                // Add a small delay to allow navigation to start
                setTimeout(() => {
                    this.closeMobileMenu();
                }, 100);
            });
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                this.closeMobileMenu();
            }
        });
    }

    toggleMobileMenu() {
        console.log('Toggle mobile menu called');
        const overlay = document.querySelector('#mobileMenuOverlay');
        const menuToggle = document.querySelector('#mobileMenuToggle');
        const body = document.body;
        
        console.log('Overlay element:', overlay);
        console.log('Menu toggle element:', menuToggle);
        
        if (overlay && menuToggle) {
            const isActive = overlay.classList.contains('active');
            console.log('Menu is currently active:', isActive);
            
            if (isActive) {
                console.log('Closing menu');
                this.closeMobileMenu();
            } else {
                console.log('Opening menu');
                this.openMobileMenu();
            }
        } else {
            console.error('Required elements not found for mobile menu toggle');
        }
    }

    openMobileMenu() {
        console.log('Opening mobile menu');
        const overlay = document.querySelector('#mobileMenuOverlay');
        const menuToggle = document.querySelector('#mobileMenuToggle');
        const body = document.body;
        
        if (overlay && menuToggle) {
            console.log('Adding active class to overlay');
            overlay.classList.add('active');
            menuToggle.classList.add('active');
            body.style.overflow = 'hidden';
            
            // Update cart count in mobile menu
            this.updateMobileCartCount();
            
            // Trigger entrance animations
            setTimeout(() => {
                const navLinks = overlay.querySelectorAll('.mobile-nav-link');
                navLinks.forEach((link, index) => {
                    link.style.animationDelay = `${0.1 + (index * 0.05)}s`;
                });
            }, 100);
        } else {
            console.error('Could not find overlay or menu toggle elements');
        }
    }

    closeMobileMenu() {
        console.log('Closing mobile menu');
        const overlay = document.querySelector('#mobileMenuOverlay');
        const menuToggle = document.querySelector('#mobileMenuToggle');
        const body = document.body;
        
        if (overlay && menuToggle) {
            console.log('Removing active class from overlay');
            overlay.classList.remove('active');
            menuToggle.classList.remove('active');
            body.style.overflow = '';
        } else {
            console.error('Could not find overlay or menu toggle elements');
        }
    }

    updateMobileCartCount() {
        // Update mobile cart badge
        const mobileCartBadge = document.querySelector('.mobile-cart-badge');
        const cartCount = document.querySelector('.cart-count');
        
        if (mobileCartBadge && cartCount) {
            const oldCount = mobileCartBadge.textContent;
            const newCount = cartCount.textContent;
            
            mobileCartBadge.textContent = newCount;
            
            // Add bounce animation if count changed
            if (oldCount !== newCount) {
                mobileCartBadge.classList.add('updated');
                setTimeout(() => {
                    mobileCartBadge.classList.remove('updated');
                }, 500);
            }
        }
        
        // Update mobile menu cart stats
        const mobileStatCounts = document.querySelectorAll('.mobile-stat .stat-number');
        if (mobileStatCounts.length > 0) {
            const cartCountElement = document.querySelector('.cart-count');
            const wishlistCountElement = document.querySelector('.wishlist-count');
            
            if (cartCountElement && mobileStatCounts[0]) {
                mobileStatCounts[0].textContent = cartCountElement.textContent;
            }
            
            if (wishlistCountElement && mobileStatCounts[1]) {
                mobileStatCounts[1].textContent = wishlistCountElement.textContent;
            }
        }
    }

    // Dropdown Management
    setupDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown, .nav-item.dropdown, .category-menu, .user-dropdown, .cart');
        
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
            if (!e.target.closest('.dropdown, .nav-item.dropdown, .category-menu, .user-dropdown, .cart')) {
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
                // Show suggestions if there's already text and suggestions exist
                const value = searchInput.value.trim();
                if (value.length >= 2) {
                    this.fetchSearchSuggestions(value);
                }
            });
            
            searchInput.addEventListener('blur', () => {
                // Hide suggestions after a small delay to allow click events on suggestions
                setTimeout(() => {
                    this.hideSearchSuggestions();
                }, 200);
            });
            
            // Keyboard navigation for suggestions
            searchInput.addEventListener('keydown', (e) => {
                this.handleSearchKeyDown(e);
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
        console.log('Search input changed:', value);
        // Clear any existing timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        if (value.length >= 2) {
            console.log('Starting search timeout for:', value);
            // Add debouncing - wait 300ms after user stops typing
            this.searchTimeout = setTimeout(() => {
                console.log('Timeout fired, fetching suggestions for:', value);
                this.fetchSearchSuggestions(value);
            }, 300);
        } else {
            console.log('Value too short, hiding suggestions');
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
            console.log('Fetching search suggestions for:', query);
            // Show loading state
            this.showSearchLoading();
            
            const categorySelect = document.querySelector('.category-select');
            const category = categorySelect ? categorySelect.value : '';
            
            // Build API URL
            const params = new URLSearchParams();
            params.append('q', query);
            if (category) {
                params.append('category', category);
            }
            
            const url = `/api/search/?${params.toString()}`;
            console.log('Making request to:', url);
            
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });
            
            console.log('Response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Received data:', data);
                this.displaySearchSuggestions(data.results, query);
            } else {
                console.error('Search API error:', response.status);
                this.hideSearchSuggestions();
            }
        } catch (error) {
            console.error('Error fetching search suggestions:', error);
            this.hideSearchSuggestions();
        }
    }

    displaySearchSuggestions(results, query) {
        const container = document.querySelector('.search-suggestions');
        console.log('Displaying suggestions in container:', container);
        if (!container) {
            console.error('Search suggestions container not found!');
            return;
        }

        container.innerHTML = '';
        console.log('Results to display:', results);
        
        if (results && results.length > 0) {
            // Add search header
            const header = document.createElement('div');
            header.className = 'suggestions-header';
            header.innerHTML = `
                <span class="suggestions-title">Search results for "${query}"</span>
                <span class="suggestions-count">${results.length} results</span>
            `;
            container.appendChild(header);
            
            results.forEach(result => {
                const item = document.createElement('div');
                item.className = `suggestion-item suggestion-${result.type}`;
                
                if (result.type === 'category') {
                    item.innerHTML = `
                        <div class="suggestion-icon">
                            <i class="fas fa-tag"></i>
                        </div>
                        <div class="suggestion-content">
                            <div class="suggestion-title">${this.highlightQuery(result.title, query)}</div>
                            <div class="suggestion-description">${result.description}</div>
                        </div>
                        <div class="suggestion-arrow">
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    `;
                } else if (result.type === 'product') {
                    item.innerHTML = `
                        <div class="suggestion-image">
                            ${result.image ? 
                                `<img src="${result.image}" alt="${result.title}" loading="lazy">` : 
                                `<div class="no-image"><i class="fas fa-image"></i></div>`
                            }
                        </div>
                        <div class="suggestion-content">
                            <div class="suggestion-title">${this.highlightQuery(result.title, query)}</div>
                            <div class="suggestion-description">${result.description}</div>
                            <div class="suggestion-meta">
                                <span class="suggestion-price">${result.price}</span>
                                <span class="suggestion-category">${result.category}</span>
                                ${result.is_featured ? '<span class="featured-badge">Featured</span>' : ''}
                                ${!result.in_stock ? '<span class="out-of-stock-badge">Out of Stock</span>' : ''}
                            </div>
                        </div>
                        <div class="suggestion-arrow">
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    `;
                }
                
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('Clicked suggestion:', result.title);
                    window.location.href = result.url;
                });
                
                // Add hover effect
                item.addEventListener('mouseenter', () => {
                    item.classList.add('hovered');
                });
                
                item.addEventListener('mouseleave', () => {
                    item.classList.remove('hovered');
                });
                
                container.appendChild(item);
            });
            
            // Add "View all results" link
            const viewAll = document.createElement('div');
            viewAll.className = 'suggestion-view-all';
            viewAll.innerHTML = `
                <a href="/search/?q=${encodeURIComponent(query)}" class="view-all-link">
                    <i class="fas fa-search"></i>
                    View all results for "${query}"
                </a>
            `;
            container.appendChild(viewAll);
            
            this.showSearchSuggestions();
            console.log('Search suggestions displayed successfully');
        } else {
            // Show "no results" message
            const noResults = document.createElement('div');
            noResults.className = 'suggestion-no-results';
            noResults.innerHTML = `
                <div class="no-results-icon">
                    <i class="fas fa-search"></i>
                </div>
                <div class="no-results-text">
                    <div class="no-results-title">No results found</div>
                    <div class="no-results-description">Try searching with different keywords</div>
                </div>
            `;
            container.appendChild(noResults);
            this.showSearchSuggestions();
            console.log('No results message displayed');
        }
    }
    
    highlightQuery(text, query) {
        if (!query || !text) return text;
        
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
    
    showSearchLoading() {
        const container = document.querySelector('.search-suggestions');
        if (!container) return;
        
        container.innerHTML = `
            <div class="suggestion-loading">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
                <span>Searching...</span>
            </div>
        `;
        container.style.display = 'block';
        container.classList.add('show');
        console.log('Loading state shown');
    }
    
    handleSearchKeyDown(e) {
        const container = document.querySelector('.search-suggestions');
        if (!container || container.style.display === 'none') return;
        
        const items = container.querySelectorAll('.suggestion-item');
        if (items.length === 0) return;
        
        const currentActive = container.querySelector('.suggestion-item.active');
        let activeIndex = -1;
        
        if (currentActive) {
            activeIndex = Array.from(items).indexOf(currentActive);
        }
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                activeIndex = activeIndex < items.length - 1 ? activeIndex + 1 : 0;
                this.setActiveSuggestion(items, activeIndex);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                activeIndex = activeIndex > 0 ? activeIndex - 1 : items.length - 1;
                this.setActiveSuggestion(items, activeIndex);
                break;
                
            case 'Enter':
                e.preventDefault();
                if (currentActive) {
                    currentActive.click();
                } else {
                    this.performSearch();
                }
                break;
                
            case 'Escape':
                e.preventDefault();
                this.hideSearchSuggestions();
                document.querySelector('.search-input').blur();
                break;
        }
    }
    
    setActiveSuggestion(items, activeIndex) {
        // Remove active class from all items
        items.forEach(item => item.classList.remove('active'));
        
        // Add active class to current item
        if (items[activeIndex]) {
            items[activeIndex].classList.add('active');
            
            // Scroll item into view if needed
            items[activeIndex].scrollIntoView({
                block: 'nearest',
                behavior: 'smooth'
            });
        }
    }

    showSearchSuggestions() {
        const container = document.querySelector('.search-suggestions');
        console.log('Showing search suggestions, container:', container);
        if (container) {
            container.style.display = 'block';
            container.classList.add('show');
            console.log('Container display set to block and show class added, computed style:', window.getComputedStyle(container).display);
            console.log('Container visibility:', window.getComputedStyle(container).visibility);
            console.log('Container z-index:', window.getComputedStyle(container).zIndex);
        } else {
            console.error('Search suggestions container not found when trying to show!');
        }
    }

    hideSearchSuggestions() {
        const container = document.querySelector('.search-suggestions');
        console.log('Hiding search suggestions, container:', container);
        if (container) {
            container.style.display = 'none';
            container.classList.remove('show');
            console.log('Container display set to none and show class removed');
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
        // Try to use CartManager if available
        if (window.cartManager) {
            console.log('CartManager found, using it for cart functionality');
            // Call initial cart update with slight delay to ensure everything is ready
            setTimeout(() => {
                if (window.cartManager && typeof window.cartManager.updateCartDisplay === 'function') {
                    window.cartManager.updateCartDisplay();
                    this.updateMobileCartCount();
                }
            }, 300);
            
            // Listen for future cart updates
            document.addEventListener('cartUpdated', () => {
                if (window.cartManager && typeof window.cartManager.updateCartDisplay === 'function') {
                    window.cartManager.updateCartDisplay();
                    this.updateMobileCartCount();
                }
            });
        } else {
            console.warn('CartManager not available yet, will wait for it');
            // Wait for cart manager to be ready
            document.addEventListener('cartManagerReady', () => {
                if (window.cartManager && typeof window.cartManager.updateCartDisplay === 'function') {
                    window.cartManager.updateCartDisplay();
                    this.updateMobileCartCount();
                }
            });
        }
        
        // Set up periodic cart count updates
        setInterval(() => {
            this.updateMobileCartCount();
        }, 5000);
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

// Cart functions are handled by CartManager class in cart.js

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
    
    // Initialize mobile cart count
    navbar.updateMobileCartCount();
});

// Handle window resize
window.addEventListener('resize', () => {
    const navbar = document.querySelector('.navbar-wrapper');
    if (window.innerWidth > 768) {
        // Close mobile menu on desktop
        const mobileMenuOverlay = document.querySelector('#mobileMenuOverlay');
        const menuToggle = document.querySelector('#mobileMenuToggle');
        
        if (mobileMenuOverlay) {
            mobileMenuOverlay.classList.remove('active');
        }
        
        if (menuToggle) {
            menuToggle.classList.remove('active');
        }
        
        document.body.style.overflow = '';
    }
});

// Touch and swipe support for mobile menu
document.addEventListener('DOMContentLoaded', () => {
    let startX = 0;
    let startY = 0;
    let distX = 0;
    let distY = 0;
    const threshold = 100;
    const restraint = 100;

    document.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    });

    document.addEventListener('touchmove', (e) => {
        if (e.touches.length === 1) {
            distX = e.touches[0].clientX - startX;
            distY = e.touches[0].clientY - startY;
        }
    });

    document.addEventListener('touchend', () => {
        const mobileMenuOverlay = document.querySelector('#mobileMenuOverlay');
        const menuIsOpen = mobileMenuOverlay && mobileMenuOverlay.classList.contains('active');
        
        if (Math.abs(distX) >= threshold && Math.abs(distY) <= restraint) {
            if (distX > 0 && startX <= 50 && !menuIsOpen) {
                // Swipe right from left edge - open menu
                if (window.navbarManager) {
                    window.navbarManager.openMobileMenu();
                }
            } else if (distX < 0 && menuIsOpen) {
                // Swipe left when menu is open - close menu
                if (window.navbarManager) {
                    window.navbarManager.closeMobileMenu();
                }
            }
        }
        
        // Reset values
        startX = 0;
        startY = 0;
        distX = 0;
        distY = 0;
    });
});

// Expose navbar manager globally for swipe functionality
window.navbarManager = null;

// Add global test function for debugging
window.testMobileMenu = function() {
    console.log('Testing mobile menu...');
    const overlay = document.querySelector('#mobileMenuOverlay');
    const toggle = document.querySelector('#mobileMenuToggle');
    
    console.log('Overlay found:', !!overlay);
    console.log('Toggle found:', !!toggle);
    
    if (overlay) {
        console.log('Overlay classes:', overlay.className);
        overlay.classList.toggle('active');
        console.log('Toggled overlay. New classes:', overlay.className);
    }
    
    if (window.navbarManager) {
        console.log('NavbarManager available, calling toggleMobileMenu');
        window.navbarManager.toggleMobileMenu();
    } else {
        console.log('NavbarManager not available');
    }
};

// Simple fallback click handler
document.addEventListener('DOMContentLoaded', () => {
    // Fallback handler in case the class-based approach fails
    setTimeout(() => {
        const toggleBtn = document.querySelector('#mobileMenuToggle');
        if (toggleBtn && !toggleBtn.hasAttribute('data-listener-added')) {
            console.log('Adding fallback click listener');
            toggleBtn.addEventListener('click', function(e) {
                console.log('Fallback click handler triggered');
                e.preventDefault();
                e.stopPropagation();
                
                const overlay = document.querySelector('#mobileMenuOverlay');
                if (overlay) {
                    overlay.classList.toggle('active');
                    console.log('Toggled overlay via fallback handler');
                }
            });
            toggleBtn.setAttribute('data-listener-added', 'true');
        }
    }, 1000);
});

// Update the navbar initialization
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing navbar');
    try {
        window.navbarManager = new NavbarManager();
        console.log('NavbarManager created successfully');
        window.navbarManager.setActiveNavigation();
        window.navbarManager.setupCurrencyLanguage();
        window.navbarManager.updateMobileCartCount();
        console.log('NavbarManager fully initialized');
    } catch (error) {
        console.error('Error initializing NavbarManager:', error);
    }
});
