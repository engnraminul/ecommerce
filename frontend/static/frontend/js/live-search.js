/**
 * Professional Live Search System
 * Advanced real-time search with debouncing, caching, and keyboard navigation
 */

class LiveSearchManager {
    constructor() {
        this.searchInput = null;
        this.searchForm = null;
        this.categorySelect = null;
        this.dropdown = null;
        this.isDropdownVisible = false;
        this.currentQuery = '';
        this.searchCache = new Map();
        this.searchHistory = this.loadSearchHistory();
        this.debounceTimeout = null;
        this.debounceDelay = 300;
        this.minQueryLength = 2;
        this.maxResults = 8;
        this.currentFocusIndex = -1;
        this.searchResults = [];
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.setupElements();
        this.createDropdown();
        this.bindEvents();
        this.setupKeyboardNavigation();
        console.log('LiveSearchManager initialized successfully');
    }

    setupElements() {
        this.searchInput = document.querySelector('.search-input');
        this.searchForm = document.querySelector('.search-form');
        this.categorySelect = document.querySelector('.category-select');
        
        if (!this.searchInput || !this.searchForm) {
            console.warn('Required search elements not found');
            return;
        }
        
        // Add autocomplete attributes
        this.searchInput.setAttribute('autocomplete', 'off');
        this.searchInput.setAttribute('autocapitalize', 'off');
        this.searchInput.setAttribute('spellcheck', 'false');
        this.searchInput.setAttribute('role', 'combobox');
        this.searchInput.setAttribute('aria-expanded', 'false');
        this.searchInput.setAttribute('aria-haspopup', 'listbox');
    }

    createDropdown() {
        if (!this.searchInput) return;
        
        // Create dropdown container
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'live-search-dropdown';
        this.dropdown.setAttribute('role', 'listbox');
        this.dropdown.setAttribute('aria-label', 'Search suggestions');
        
        // Insert dropdown after search form (better positioning)
        const searchForm = this.searchInput.closest('.search-form');
        if (searchForm && searchForm.parentNode) {
            searchForm.parentNode.insertBefore(this.dropdown, searchForm.nextSibling);
        } else {
            // Fallback: insert after search wrapper
            const searchWrapper = this.searchInput.closest('.search-input-wrapper');
            if (searchWrapper && searchWrapper.parentNode) {
                searchWrapper.parentNode.insertBefore(this.dropdown, searchWrapper.nextSibling);
            }
        }
    }

    bindEvents() {
        if (!this.searchInput) return;
        
        // Input events
        this.searchInput.addEventListener('input', (e) => {
            this.handleInput(e.target.value.trim());
        });
        
        this.searchInput.addEventListener('focus', () => {
            if (this.searchInput.value.trim().length >= this.minQueryLength) {
                this.showDropdown();
            } else if (this.searchHistory.length > 0) {
                this.showSearchHistory();
            }
        });
        
        this.searchInput.addEventListener('blur', (e) => {
            // Delay hiding to allow clicking on dropdown items
            setTimeout(() => {
                if (!this.dropdown.contains(document.activeElement)) {
                    this.hideDropdown();
                }
            }, 150);
        });

        // Category change
        if (this.categorySelect) {
            this.categorySelect.addEventListener('change', () => {
                if (this.currentQuery) {
                    this.clearCache();
                    this.performSearch(this.currentQuery);
                }
                this.updateSearchPlaceholder();
            });
        }

        // Form submission
        if (this.searchForm) {
            this.searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmission();
            });
        }

        // Global click handler
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.live-search-dropdown') && 
                !e.target.closest('.search-input-wrapper') &&
                !e.target.closest('.search-form')) {
                this.hideDropdown();
            }
        });

        // Window resize
        window.addEventListener('resize', () => {
            if (this.isDropdownVisible) {
                this.positionDropdown();
            }
        });
    }

    setupKeyboardNavigation() {
        if (!this.searchInput) return;
        
        this.searchInput.addEventListener('keydown', (e) => {
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.navigateDown();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.navigateUp();
                    break;
                case 'Enter':
                    e.preventDefault();
                    this.selectCurrentItem();
                    break;
                case 'Escape':
                    this.hideDropdown();
                    this.searchInput.blur();
                    break;
                case 'Tab':
                    this.hideDropdown();
                    break;
            }
        });
    }

    handleInput(query) {
        this.currentQuery = query;
        
        // Clear previous timeout
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }
        
        if (query.length === 0) {
            this.hideDropdown();
            return;
        }
        
        if (query.length < this.minQueryLength) {
            if (this.searchHistory.length > 0) {
                this.showSearchHistory();
            } else {
                this.hideDropdown();
            }
            return;
        }
        
        // Debounced search
        this.debounceTimeout = setTimeout(() => {
            this.performSearch(query);
        }, this.debounceDelay);
    }

    async performSearch(query) {
        if (!query || query.length < this.minQueryLength) return;
        
        const cacheKey = this.getCacheKey(query);
        
        // Check cache first
        if (this.searchCache.has(cacheKey)) {
            const cachedResults = this.searchCache.get(cacheKey);
            this.displayResults(cachedResults, query);
            return;
        }
        
        // Show loading state
        this.showLoading();
        this.isLoading = true;
        
        try {
            const params = new URLSearchParams({
                q: query
            });
            
            if (this.categorySelect && this.categorySelect.value) {
                params.append('category', this.categorySelect.value);
            }
            
            const response = await fetch(`/api/live-search/?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Check for API errors
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Cache results
            this.searchCache.set(cacheKey, data);
            
            // Display results
            this.displayResults(data, query);
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError(error.message || 'Unable to fetch search results. Please try again.');
        } finally {
            this.isLoading = false;
        }
    }

    displayResults(data, query) {
        if (!this.dropdown) return;
        
        const { products = [], categories = [], suggestions = [] } = data;
        this.searchResults = [];
        this.currentFocusIndex = -1;
        
        let html = '<div class="search-dropdown-content">';
        
        // Products section
        if (products.length > 0) {
            html += `
                <div class="search-section">
                    <div class="search-section-header">
                        <i class="fas fa-box"></i>
                        Products
                    </div>
            `;
            
            products.forEach((product, index) => {
                const highlightedName = this.highlightQuery(product.name, query);
                const imageUrl = product.image || '/static/frontend/images/no-image.jpg';
                
                html += `
                    <a href="${product.url}" class="product-search-item" data-index="${this.searchResults.length}" data-type="product">
                        <img src="${imageUrl}" alt="${product.name}" class="search-product-image" 
                             onerror="this.src='/static/frontend/images/no-image.jpg'; this.onerror=null;">
                        <div class="product-info">
                            <div class="product-name">${highlightedName}</div>
                            <div class="product-category">${product.category}</div>
                        </div>
                        <div class="product-price">৳${parseFloat(product.price).toFixed(2)}</div>
                    </a>
                `;
                
                this.searchResults.push({
                    type: 'product',
                    url: product.url,
                    name: product.name
                });
            });
            
            html += '</div>';
        }
        
        // Categories section
        if (categories.length > 0) {
            html += `
                <div class="search-section">
                    <div class="search-section-header">
                        <i class="fas fa-th-large"></i>
                        Categories
                    </div>
            `;
            
            categories.forEach((category) => {
                const highlightedName = this.highlightQuery(category.name, query);
                const categoryImage = category.image || '';
                
                html += `
                    <a href="${category.url}" class="search-item category-item" data-index="${this.searchResults.length}" data-type="category">
                        <div class="search-item-icon">
                            ${categoryImage ? 
                                `<img src="${categoryImage}" alt="${category.name}" class="category-icon-image" 
                                      onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                 <i class="fas fa-tag" style="display: none;"></i>` :
                                `<i class="fas fa-tag"></i>`
                            }
                        </div>
                        <div class="search-item-content">
                            <div class="search-item-title">${highlightedName}</div>
                            <div class="search-item-meta">Category</div>
                        </div>
                    </a>
                `;
                
                this.searchResults.push({
                    type: 'category',
                    url: category.url,
                    name: category.name
                });
            });
            
            html += '</div>';
        }
        
        // Search suggestions
        if (suggestions.length > 0) {
            html += `
                <div class="search-section">
                    <div class="search-section-header">
                        <i class="fas fa-search"></i>
                        Suggestions
                    </div>
            `;
            
            suggestions.slice(0, 3).forEach((suggestion) => {
                const highlightedSuggestion = this.highlightQuery(suggestion, query);
                
                html += `
                    <div class="search-item suggestion-item" data-index="${this.searchResults.length}" data-type="suggestion" data-query="${suggestion}">
                        <div class="search-item-icon">
                            <i class="fas fa-search"></i>
                        </div>
                        <div class="search-item-content">
                            <div class="search-item-title">${highlightedSuggestion}</div>
                            <div class="search-item-meta">Search for this term</div>
                        </div>
                    </div>
                `;
                
                this.searchResults.push({
                    type: 'suggestion',
                    query: suggestion,
                    name: suggestion
                });
            });
            
            html += '</div>';
        }
        
        // Quick actions
        html += this.getQuickActionsHTML();
        
        html += '</div>';
        
        // Show empty state if no results
        if (products.length === 0 && categories.length === 0 && suggestions.length === 0) {
            html = this.getEmptyStateHTML(query);
        }
        
        this.dropdown.innerHTML = html;
        this.bindDropdownEvents();
        this.showDropdown();
    }

    showSearchHistory() {
        if (!this.dropdown || this.searchHistory.length === 0) return;
        
        this.searchResults = [];
        this.currentFocusIndex = -1;
        
        let html = '<div class="search-dropdown-content">';
        html += `
            <div class="search-history">
                <div class="search-history-header">
                    <span class="search-history-title">Recent Searches</span>
                    <button class="clear-history" onclick="liveSearch.clearSearchHistory()">Clear</button>
                </div>
        `;
        
        this.searchHistory.slice(0, 5).forEach((item, index) => {
            html += `
                <div class="search-item history-item" data-index="${this.searchResults.length}" data-type="history" data-query="${item}">
                    <div class="search-item-icon">
                        <i class="fas fa-history"></i>
                    </div>
                    <div class="search-item-content">
                        <div class="search-item-title">${item}</div>
                        <div class="search-item-meta">Recent search</div>
                    </div>
                </div>
            `;
            
            this.searchResults.push({
                type: 'history',
                query: item,
                name: item
            });
        });
        
        html += '</div>';
        html += this.getQuickActionsHTML();
        html += '</div>';
        
        this.dropdown.innerHTML = html;
        this.bindDropdownEvents();
        this.showDropdown();
    }

    showLoading() {
        if (!this.dropdown) return;
        
        this.dropdown.innerHTML = `
            <div class="search-loading">
                <div class="search-loading-spinner"></div>
                <div>Searching...</div>
            </div>
        `;
        
        this.showDropdown();
    }

    showError(message) {
        if (!this.dropdown) return;
        
        this.dropdown.innerHTML = `
            <div class="search-empty">
                <div class="search-empty-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="search-empty-text">${message}</div>
            </div>
        `;
        
        this.showDropdown();
    }

    getEmptyStateHTML(query) {
        return `
            <div class="search-empty">
                <div class="search-empty-icon">
                    <i class="fas fa-search"></i>
                </div>
                <div class="search-empty-text">No results found for "${query}"</div>
                <div class="search-empty-suggestion">Try different keywords or check spelling</div>
            </div>
        `;
    }

    getQuickActionsHTML() {
        return `
            <div class="search-quick-actions">
                <div class="quick-action-buttons">
                    <a href="/products/?featured=true" class="quick-action-btn">
                        <i class="fas fa-fire"></i>
                        Featured
                    </a>
                    <a href="/products/?new=true" class="quick-action-btn">
                        <i class="fas fa-sparkles"></i>
                        New Arrivals
                    </a>
                    <a href="/products/?sale=true" class="quick-action-btn">
                        <i class="fas fa-tags"></i>
                        Sale
                    </a>
                    <a href="/categories/" class="quick-action-btn">
                        <i class="fas fa-th-large"></i>
                        All Categories
                    </a>
                </div>
            </div>
        `;
    }

    bindDropdownEvents() {
        if (!this.dropdown) return;
        
        // Bind click events for search items
        const searchItems = this.dropdown.querySelectorAll('.search-item, .product-search-item');
        searchItems.forEach((item) => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleItemClick(item);
            });
            
            item.addEventListener('mouseenter', () => {
                this.setFocusIndex(parseInt(item.dataset.index));
            });
        });
    }

    handleItemClick(item) {
        const type = item.dataset.type;
        
        if (type === 'suggestion' || type === 'history') {
            const query = item.dataset.query;
            this.searchInput.value = query;
            this.addToSearchHistory(query);
            this.handleFormSubmission();
        } else if (item.href) {
            this.addToSearchHistory(this.currentQuery);
            window.location.href = item.href;
        }
    }

    navigateDown() {
        if (!this.isDropdownVisible || this.searchResults.length === 0) return;
        
        this.currentFocusIndex = Math.min(this.currentFocusIndex + 1, this.searchResults.length - 1);
        this.updateFocus();
    }

    navigateUp() {
        if (!this.isDropdownVisible || this.searchResults.length === 0) return;
        
        this.currentFocusIndex = Math.max(this.currentFocusIndex - 1, -1);
        this.updateFocus();
    }

    selectCurrentItem() {
        if (this.currentFocusIndex >= 0 && this.currentFocusIndex < this.searchResults.length) {
            const item = this.dropdown.querySelector(`[data-index="${this.currentFocusIndex}"]`);
            if (item) {
                this.handleItemClick(item);
            }
        } else {
            this.handleFormSubmission();
        }
    }

    updateFocus() {
        const items = this.dropdown.querySelectorAll('.search-item, .product-search-item');
        
        items.forEach((item, index) => {
            item.classList.remove('keyboard-focused');
            if (index === this.currentFocusIndex) {
                item.classList.add('keyboard-focused');
                item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            }
        });
    }

    setFocusIndex(index) {
        this.currentFocusIndex = index;
        this.updateFocus();
    }

    handleFormSubmission() {
        const query = this.searchInput.value.trim();
        if (!query) return;
        
        this.addToSearchHistory(query);
        this.hideDropdown();
        
        // Build search URL
        const params = new URLSearchParams({ q: query });
        if (this.categorySelect && this.categorySelect.value) {
            params.append('category', this.categorySelect.value);
        }
        
        window.location.href = `/search/?${params}`;
    }

    showDropdown() {
        if (!this.dropdown) return;
        
        this.dropdown.classList.add('show');
        this.isDropdownVisible = true;
        this.searchInput.setAttribute('aria-expanded', 'true');
        this.positionDropdown();
    }

    hideDropdown() {
        if (!this.dropdown) return;
        
        this.dropdown.classList.remove('show');
        this.isDropdownVisible = false;
        this.searchInput.setAttribute('aria-expanded', 'false');
        this.currentFocusIndex = -1;
    }

    positionDropdown() {
        if (!this.dropdown || !this.searchInput) return;
        
        const searchForm = this.searchInput.closest('.search-form');
        const searchWrapper = this.searchInput.closest('.search-input-wrapper');
        const targetElement = searchForm || searchWrapper;
        
        if (targetElement) {
            const rect = targetElement.getBoundingClientRect();
            
            // Position dropdown relative to the search form/wrapper
            this.dropdown.style.position = 'absolute';
            this.dropdown.style.top = `${rect.height + 5}px`;
            this.dropdown.style.left = '0';
            this.dropdown.style.width = `${rect.width}px`;
            this.dropdown.style.zIndex = '9999';
        }
    }

    highlightQuery(text, query) {
        if (!query || !text) return text;
        
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<span class="search-highlight">$1</span>');
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    getCacheKey(query) {
        const category = this.categorySelect ? this.categorySelect.value : '';
        return `${query}|${category}`;
    }

    clearCache() {
        this.searchCache.clear();
    }

    updateSearchPlaceholder() {
        if (!this.searchInput || !this.categorySelect) return;
        
        const category = this.categorySelect.selectedOptions[0]?.text || 'All Categories';
        this.searchInput.placeholder = `Search in ${category}...`;
    }

    // Search History Management
    loadSearchHistory() {
        try {
            const history = localStorage.getItem('searchHistory');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('Error loading search history:', error);
            return [];
        }
    }

    saveSearchHistory() {
        try {
            localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
        } catch (error) {
            console.error('Error saving search history:', error);
        }
    }

    addToSearchHistory(query) {
        if (!query || query.length < this.minQueryLength) return;
        
        // Remove if already exists
        this.searchHistory = this.searchHistory.filter(item => item !== query);
        
        // Add to beginning
        this.searchHistory.unshift(query);
        
        // Limit to 10 items
        this.searchHistory = this.searchHistory.slice(0, 10);
        
        this.saveSearchHistory();
    }

    clearSearchHistory() {
        this.searchHistory = [];
        this.saveSearchHistory();
        this.hideDropdown();
        
        if (this.searchInput.value.trim().length === 0) {
            this.hideDropdown();
        }
    }

    // Public API
    destroy() {
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }
        
        if (this.dropdown && this.dropdown.parentNode) {
            this.dropdown.parentNode.removeChild(this.dropdown);
        }
        
        this.clearCache();
    }

    refresh() {
        this.clearCache();
        if (this.currentQuery) {
            this.performSearch(this.currentQuery);
        }
    }

    // Debug function
    debug() {
        console.log('LiveSearch Debug Info:');
        console.log('- Search Input:', this.searchInput);
        console.log('- Search Form:', this.searchForm);
        console.log('- Category Select:', this.categorySelect);
        console.log('- Dropdown:', this.dropdown);
        console.log('- Current Query:', this.currentQuery);
        console.log('- Is Dropdown Visible:', this.isDropdownVisible);
        console.log('- Cache Size:', this.searchCache.size);
        console.log('- Search History:', this.searchHistory);
        
        if (this.dropdown) {
            const rect = this.dropdown.getBoundingClientRect();
            console.log('- Dropdown Position:', {
                top: rect.top,
                left: rect.left,
                width: rect.width,
                height: rect.height,
                visible: getComputedStyle(this.dropdown).visibility
            });
        }
    }
}

// Initialize live search when DOM is ready
let liveSearch = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Live Search...');
    
    // Wait a bit for other scripts to load
    setTimeout(() => {
        try {
            // Check if required elements exist
            const searchInput = document.querySelector('.search-input');
            const searchForm = document.querySelector('.search-form');
            
            if (!searchInput || !searchForm) {
                console.warn('Live Search: Required elements not found. Search input:', !!searchInput, 'Search form:', !!searchForm);
                return;
            }
            
            liveSearch = new LiveSearchManager();
            window.liveSearch = liveSearch; // Make globally accessible
            
            // Add debug function to window for testing
            window.debugLiveSearch = () => {
                if (liveSearch) {
                    liveSearch.debug();
                } else {
                    console.log('Live Search not initialized');
                }
            };
            
            console.log('Live Search initialized successfully');
            console.log('Use window.debugLiveSearch() to debug');
            
        } catch (error) {
            console.error('Failed to initialize Live Search:', error);
        }
    }, 500);
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LiveSearchManager;
}