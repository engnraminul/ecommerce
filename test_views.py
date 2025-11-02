from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def test_live_search(request):
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Search Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        .search-container {
            position: relative;
            margin-bottom: 30px;
        }
        .search-input {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
        }
        .search-suggestions {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-height: 400px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }
        .suggestion-item {
            padding: 12px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
        }
        .suggestion-item:hover {
            background: #f5f5f5;
        }
        .suggestion-title {
            font-weight: bold;
            margin-bottom: 4px;
        }
        .suggestion-description {
            color: #666;
            font-size: 14px;
        }
        .log {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            max-height: 300px;
            overflow-y: auto;
        }
        .log-entry {
            margin-bottom: 5px;
        }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .info { color: #007bff; }
    </style>
</head>
<body>
    <h1>🔍 Live Search Test</h1>
    <p>This test page verifies that the AJAX live search functionality is working correctly.</p>
    
    <div class="search-container">
        <input type="text" id="searchInput" class="search-input" placeholder="Type to search products or categories..." autocomplete="off">
        <div id="searchSuggestions" class="search-suggestions"></div>
    </div>
    
    <h3>Test Log:</h3>
    <div class="log" id="log">
        <div class="log-entry info">🚀 Ready to test live search...</div>
    </div>

    <script>
        class LiveSearchTest {
            constructor() {
                this.searchInput = document.getElementById('searchInput');
                this.searchSuggestions = document.getElementById('searchSuggestions');
                this.log = document.getElementById('log');
                this.searchTimeout = null;
                
                this.init();
            }
            
            init() {
                this.searchInput.addEventListener('input', (e) => {
                    this.handleSearchInput(e.target.value);
                });
                
                this.searchInput.addEventListener('focus', () => {
                    const value = this.searchInput.value.trim();
                    if (value.length >= 2) {
                        this.fetchSearchSuggestions(value);
                    }
                });
                
                this.searchInput.addEventListener('blur', () => {
                    setTimeout(() => {
                        this.hideSearchSuggestions();
                    }, 200);
                });
                
                this.logMessage('✅ Live search initialized successfully', 'success');
            }
            
            handleSearchInput(value) {
                this.logMessage(`📝 Input: "${value}"`, 'info');
                
                if (this.searchTimeout) {
                    clearTimeout(this.searchTimeout);
                }
                
                if (value.length >= 2) {
                    this.logMessage(`⏳ Debouncing search for "${value}" (300ms delay)`, 'info');
                    this.searchTimeout = setTimeout(() => {
                        this.fetchSearchSuggestions(value);
                    }, 300);
                } else {
                    this.hideSearchSuggestions();
                }
            }
            
            async fetchSearchSuggestions(query) {
                try {
                    this.logMessage(`🔍 Fetching suggestions for: "${query}"`, 'info');
                    this.showSearchLoading();
                    
                    const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`, {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/json',
                        }
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        this.logMessage(`✅ Received ${data.results.length} results`, 'success');
                        this.displaySearchSuggestions(data.results, query);
                    } else {
                        this.logMessage(`❌ Error: ${response.status} ${response.statusText}`, 'error');
                        this.hideSearchSuggestions();
                    }
                } catch (error) {
                    this.logMessage(`❌ Network Error: ${error.message}`, 'error');
                    this.hideSearchSuggestions();
                }
            }
            
            displaySearchSuggestions(results, query) {
                this.searchSuggestions.innerHTML = '';
                
                if (results && results.length > 0) {
                    // Add header
                    const header = document.createElement('div');
                    header.style.cssText = 'padding: 8px 12px; background: #f8f9fa; border-bottom: 1px solid #ddd; font-weight: bold; font-size: 14px;';
                    header.textContent = `Search results for "${query}" (${results.length} found)`;
                    this.searchSuggestions.appendChild(header);
                    
                    results.forEach(result => {
                        const item = document.createElement('div');
                        item.className = 'suggestion-item';
                        
                        const typeIcon = result.type === 'category' ? '📁' : '🛍️';
                        const priceDisplay = result.price ? `<div style="color: #007bff; font-weight: bold; margin-top: 4px;">${result.price}</div>` : '';
                        
                        item.innerHTML = `
                            <div class="suggestion-title">${typeIcon} ${this.highlightQuery(result.title, query)}</div>
                            <div class="suggestion-description">${result.description}</div>
                            ${priceDisplay}
                        `;
                        
                        item.addEventListener('click', () => {
                            this.logMessage(`🖱️ Clicked: ${result.title} (${result.type})`, 'info');
                            // In a real implementation, this would navigate to the URL
                            // window.location.href = result.url;
                        });
                        
                        this.searchSuggestions.appendChild(item);
                    });
                    
                    this.showSearchSuggestions();
                    this.logMessage(`🎯 Displayed ${results.length} suggestions`, 'success');
                } else {
                    const noResults = document.createElement('div');
                    noResults.className = 'suggestion-item';
                    noResults.innerHTML = '<div class="suggestion-title">❌ No results found</div><div class="suggestion-description">Try different keywords</div>';
                    this.searchSuggestions.appendChild(noResults);
                    this.showSearchSuggestions();
                    this.logMessage(`🚫 No results found for "${query}"`, 'info');
                }
            }
            
            highlightQuery(text, query) {
                if (!query || !text) return text;
                const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
                return text.replace(regex, '<mark style="background: #ffeb3b; padding: 2px;">$1</mark>');
            }
            
            showSearchLoading() {
                this.searchSuggestions.innerHTML = `
                    <div class="suggestion-item" style="text-align: center;">
                        <div class="suggestion-title">🔄 Searching...</div>
                        <div class="suggestion-description">Please wait while we search...</div>
                    </div>
                `;
                this.showSearchSuggestions();
            }
            
            showSearchSuggestions() {
                this.searchSuggestions.style.display = 'block';
            }
            
            hideSearchSuggestions() {
                this.searchSuggestions.style.display = 'none';
            }
            
            logMessage(message, type = 'info') {
                const timestamp = new Date().toLocaleTimeString();
                const entry = document.createElement('div');
                entry.className = `log-entry ${type}`;
                entry.textContent = `[${timestamp}] ${message}`;
                this.log.appendChild(entry);
                this.log.scrollTop = this.log.scrollHeight;
            }
        }
        
        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            new LiveSearchTest();
        });
    </script>
</body>
</html>'''
    return HttpResponse(html_content)