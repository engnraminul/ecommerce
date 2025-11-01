// FIXED SEARCH DROPDOWN FUNCTIONALITY
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Search dropdown fix loaded');
    
    const searchInput = document.querySelector('.search-input');
    const suggestionsContainer = document.querySelector('.search-suggestions');
    
    if (!searchInput || !suggestionsContainer) {
        console.error('❌ Search elements not found!');
        return;
    }
    
    console.log('✅ Search elements found');
    
    let searchTimeout;
    
    // Show dropdown
    function showDropdown() {
        suggestionsContainer.classList.add('active');
        suggestionsContainer.style.display = 'block';
        suggestionsContainer.style.visibility = 'visible';
        suggestionsContainer.style.opacity = '1';
    }
    
    // Hide dropdown
    function hideDropdown() {
        suggestionsContainer.classList.remove('active');
        suggestionsContainer.style.display = 'none';
        suggestionsContainer.style.visibility = 'hidden';
        suggestionsContainer.style.opacity = '0';
    }
    
    // Search function
    async function performSearch(query) {
        console.log('🔍 Searching for:', query);
        
        if (query.length < 2) {
            hideDropdown();
            return;
        }
        
        try {
            // Show loading state
            showDropdown();
            suggestionsContainer.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <i class="fas fa-spinner fa-spin"></i> Searching...
                </div>
            `;
            
            const url = `/api/search/?q=${encodeURIComponent(query)}`;
            console.log('📡 Fetching:', url);
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            console.log('📡 Response:', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok,
                url: response.url
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Server error:', errorText);
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📦 Search data received:', data);
            
            // Build results HTML
            let html = '';
            
            if (data.products && data.products.length > 0) {
                html += `<div class="suggestions-header">Products</div>`;
                data.products.forEach(product => {
                    html += `
                        <a href="${product.url}" class="product-suggestion">
                            <img src="${product.image}" alt="${product.name}" class="product-image" onerror="this.src='/static/images/placeholder.jpg'">
                            <div class="product-info">
                                <div class="product-name">${product.name}</div>
                                <div class="product-price">৳${product.price}</div>
                            </div>
                        </a>
                    `;
                });
            }
            
            if (data.categories && data.categories.length > 0) {
                html += `<div class="suggestions-header">Categories</div>`;
                data.categories.forEach(category => {
                    html += `
                        <a href="${category.url}" class="category-suggestion">
                            <div class="category-icon">
                                <i class="fas fa-tag"></i>
                            </div>
                            <div class="category-name">${category.name}</div>
                        </a>
                    `;
                });
            }
            
            if (!html) {
                html = `<div class="no-results">No results found for "${query}"</div>`;
            }
            
            suggestionsContainer.innerHTML = html;
            showDropdown();
            
            console.log('✅ Search results displayed successfully');
            
        } catch (error) {
            console.error('❌ Search error details:', {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            
            suggestionsContainer.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #dc3545;">
                    <i class="fas fa-exclamation-triangle"></i><br>
                    Search error: ${error.message}<br>
                    <small>Check console for details</small>
                </div>
            `;
            showDropdown();
        }
    }
    
    // Input event listener
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        clearTimeout(searchTimeout);
        
        if (query.length === 0) {
            hideDropdown();
            return;
        }
        
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    });
    
    // Focus event
    searchInput.addEventListener('focus', function() {
        if (searchInput.value.trim().length >= 2) {
            performSearch(searchInput.value.trim());
        }
    });
    
    // Click outside to hide
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            hideDropdown();
        }
    });
    
    // Initially hide dropdown
    hideDropdown();
    
    console.log('🔧 Search functionality initialized successfully!');
});