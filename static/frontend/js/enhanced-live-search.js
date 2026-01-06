// Enhanced Live Search with Visibility Debugging
document.addEventListener('DOMContentLoaded', function() {
    console.log('Enhanced live search initializing...');
    
    // Find search elements
    const searchInput = document.querySelector('.search-input');
    const searchSuggestions = document.querySelector('.search-suggestions');
    const searchWrapper = document.querySelector('.search-input-wrapper');
    
    console.log('Search input found:', !!searchInput);
    console.log('Search suggestions found:', !!searchSuggestions);
    console.log('Search wrapper found:', !!searchWrapper);
    
    if (!searchInput || !searchSuggestions) {
        console.error('Required search elements not found!');
        return;
    }
    
    // Debug element positions
    if (searchWrapper) {
        console.log('Wrapper position:', window.getComputedStyle(searchWrapper).position);
        console.log('Wrapper z-index:', window.getComputedStyle(searchWrapper).zIndex);
    }
    
    console.log('Suggestions position:', window.getComputedStyle(searchSuggestions).position);
    console.log('Suggestions z-index:', window.getComputedStyle(searchSuggestions).zIndex);
    console.log('Suggestions display:', window.getComputedStyle(searchSuggestions).display);
    
    let searchTimeout = null;
    
    // Input event listener
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        console.log('Search input:', query);
        
        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        if (query.length >= 2) {
            // Debounce search requests
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300);
        } else {
            hideSuggestions();
        }
    });
    
    // Focus event listener
    searchInput.addEventListener('focus', function() {
        const query = this.value.trim();
        if (query.length >= 2) {
            performSearch(query);
        }
    });
    
    // Blur event listener (with delay for clicks)
    searchInput.addEventListener('blur', function() {
        setTimeout(() => {
            hideSuggestions();
        }, 200);
    });
    
    // Perform search
    async function performSearch(query) {
        console.log('Performing search for:', query);
        
        try {
            showLoading();
            
            const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Search results received:', data);
                displayResults(data.results, query);
            } else {
                console.error('Search API error:', response.status);
                showTestContent();
            }
        } catch (error) {
            console.error('Search error:', error);
            showTestContent();
        }
    }
    
    // Show test content to verify visibility
    function showTestContent() {
        console.log('Showing test content to verify visibility...');
        searchSuggestions.innerHTML = `
            <div style="padding: 20px; background: red; color: white; font-weight: bold; border: 3px solid black;">
                🔴 TEST VISIBILITY - If you can see this red box, the dropdown is working!
            </div>
        `;
        forceSuggestionVisibility();
    }
    
    // Show loading state
    function showLoading() {
        console.log('Showing loading state...');
        searchSuggestions.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #666; background: yellow; border: 2px solid orange;">
                <i class="fas fa-spinner fa-spin"></i> Searching... (Loading visible test)
            </div>
        `;
        forceSuggestionVisibility();
    }
    
    // Display search results
    function displayResults(results, query) {
        console.log('Displaying results:', results.length);
        
        if (!results || results.length === 0) {
            searchSuggestions.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #666; background: lightblue; border: 2px solid blue;">
                    <i class="fas fa-search"></i><br>
                    No results found for "${query}"<br>
                    (No results visible test)
                </div>
            `;
            forceSuggestionVisibility();
            return;
        }
        
        let html = '';
        
        // Add header with bright background for visibility test
        html += `
            <div style="padding: 10px 15px; background: lightgreen; border: 2px solid green; border-bottom: 1px solid #dee2e6; font-weight: bold; color: #495057;">
                ✅ RESULTS VISIBLE - Search results for "${query}" (${results.length})
            </div>
        `;
        
        // Add results
        results.forEach(result => {
            const highlightedTitle = highlightText(result.title, query);
            
            if (result.type === 'category') {
                html += `
                    <div class="suggestion-result" onclick="window.location.href='${result.url}'" style="padding: 12px 15px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; align-items: center; gap: 10px; background: white;">
                        <div style="width: 32px; height: 32px; background: #007bff; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white;">
                            <i class="fas fa-tag"></i>
                        </div>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #212529; margin-bottom: 2px;">${highlightedTitle}</div>
                            <div style="font-size: 13px; color: #6c757d;">${result.description}</div>
                        </div>
                        <div style="color: #6c757d;">
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    </div>
                `;
            } else if (result.type === 'product') {
                html += `
                    <div class="suggestion-result" onclick="window.location.href='${result.url}'" style="padding: 12px 15px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; align-items: center; gap: 12px; background: white;">
                        <div style="width: 48px; height: 48px; background: #f8f9fa; border-radius: 4px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                            ${result.image ? 
                                `<img src="${result.image}" alt="${result.title}" style="width: 100%; height: 100%; object-fit: cover;">` : 
                                `<i class="fas fa-image" style="color: #6c757d;"></i>`
                            }
                        </div>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #212529; margin-bottom: 2px;">${highlightedTitle}</div>
                            <div style="font-size: 13px; color: #6c757d; margin-bottom: 4px;">${result.description}</div>
                            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                <span style="color: #007bff; font-weight: bold;">${result.price}</span>
                                <span style="background: #e9ecef; padding: 2px 8px; border-radius: 12px; font-size: 11px; color: #495057;">${result.category}</span>
                                ${result.is_featured ? '<span style="background: #ffc107; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Featured</span>' : ''}
                            </div>
                        </div>
                        <div style="color: #6c757d;">
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    </div>
                `;
            }
        });
        
        // Add "View all" link
        html += `
            <div style="padding: 12px 15px; background: #f8f9fa; border-top: 1px solid #dee2e6;">
                <a href="/search/?q=${encodeURIComponent(query)}" style="color: #007bff; text-decoration: none; font-weight: 500; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <i class="fas fa-search"></i> View all results for "${query}"
                </a>
            </div>
        `;
        
        searchSuggestions.innerHTML = html;
        
        // Add hover effects
        const resultElements = searchSuggestions.querySelectorAll('.suggestion-result');
        resultElements.forEach(element => {
            element.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fa';
            });
            element.addEventListener('mouseleave', function() {
                this.style.backgroundColor = 'white';
            });
        });
        
        forceSuggestionVisibility();
    }
    
    // Force suggestion visibility with multiple methods
    function forceSuggestionVisibility() {
        console.log('Forcing suggestion visibility...');
        
        // Method 1: Direct style application
        searchSuggestions.style.display = 'block';
        searchSuggestions.style.visibility = 'visible';
        searchSuggestions.style.opacity = '1';
        searchSuggestions.style.position = 'absolute';
        searchSuggestions.style.top = '100%';
        searchSuggestions.style.left = '0';
        searchSuggestions.style.right = '0';
        searchSuggestions.style.background = 'white';
        searchSuggestions.style.border = '1px solid #dee2e6';
        searchSuggestions.style.borderTop = 'none';
        searchSuggestions.style.borderRadius = '0 0 8px 8px';
        searchSuggestions.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.15)';
        searchSuggestions.style.zIndex = '99999';
        searchSuggestions.style.maxHeight = '400px';
        searchSuggestions.style.overflowY = 'auto';
        searchSuggestions.style.width = '100%';
        
        // Method 2: Add CSS class
        searchSuggestions.classList.add('show');
        
        // Method 3: Remove any hidden classes
        searchSuggestions.classList.remove('hidden', 'invisible');
        
        // Method 4: Check computed styles
        const computedStyle = window.getComputedStyle(searchSuggestions);
        console.log('After forcing - Display:', computedStyle.display);
        console.log('After forcing - Visibility:', computedStyle.visibility);
        console.log('After forcing - Opacity:', computedStyle.opacity);
        console.log('After forcing - Z-index:', computedStyle.zIndex);
        console.log('After forcing - Position:', computedStyle.position);
        
        // Method 5: Check if element is actually visible
        const rect = searchSuggestions.getBoundingClientRect();
        console.log('Element bounds:', rect);
        console.log('Element visible in viewport:', rect.width > 0 && rect.height > 0);
    }
    
    // Highlight search query in text
    function highlightText(text, query) {
        if (!query || !text) return text;
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark style="background: #fff3cd; color: #856404; padding: 1px 2px; border-radius: 2px;">$1</mark>');
    }
    
    // Hide suggestions
    function hideSuggestions() {
        console.log('Hiding suggestions');
        searchSuggestions.style.display = 'none';
        searchSuggestions.classList.remove('show');
    }
    
    // Add a test button to manually show suggestions (for debugging)
    const testButton = document.createElement('button');
    testButton.textContent = 'Test Visibility';
    testButton.style.position = 'fixed';
    testButton.style.top = '10px';
    testButton.style.right = '10px';
    testButton.style.zIndex = '99999';
    testButton.style.background = 'red';
    testButton.style.color = 'white';
    testButton.style.padding = '10px';
    testButton.style.border = 'none';
    testButton.style.borderRadius = '4px';
    testButton.style.cursor = 'pointer';
    
    testButton.addEventListener('click', function() {
        console.log('Manual visibility test triggered');
        showTestContent();
    });
    
    document.body.appendChild(testButton);
    
    console.log('Enhanced live search initialized with visibility debugging');
});