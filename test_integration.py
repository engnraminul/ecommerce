from django.shortcuts import render
from django.http import HttpResponse
from settings.context_processors import integration_settings

def test_integration_view(request):
    """Test view to check integration settings"""
    
    # Get context from the context processor
    context = integration_settings(request)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Integration Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 2rem; }}
            .test-section {{ margin: 2rem 0; padding: 1rem; border: 1px solid #ddd; }}
            .code {{ background: #f5f5f5; padding: 1rem; white-space: pre-wrap; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>🔍 Integration Settings Test Page</h1>
        
        <div class="test-section">
            <h2>Context Processor Results</h2>
            <p><strong>Integration Settings Object:</strong> {context.get('integration_settings')}</p>
            <p><strong>Meta Tags Length:</strong> {len(context.get('integration_meta_tags', ''))}</p>
            <p><strong>Header Scripts Length:</strong> {len(context.get('integration_header_scripts', ''))}</p>
            <p><strong>Body Scripts Length:</strong> {len(context.get('integration_body_scripts', ''))}</p>
            <p><strong>Footer Scripts Length:</strong> {len(context.get('integration_footer_scripts', ''))}</p>
        </div>
        
        <div class="test-section">
            <h2>🎯 Meta Pixel Header Scripts</h2>
            <div class="code">{context.get('integration_header_scripts', 'No scripts found')}</div>
        </div>
        
        <div class="test-section">
            <h2>🔧 Raw Template Variables</h2>
            <p>This section shows if template variables are being rendered:</p>
            <div class="code">
Meta Tags: {{ integration_meta_tags|safe }}
Header Scripts: {{ integration_header_scripts|safe }}
Body Scripts: {{ integration_body_scripts|safe }}
Footer Scripts: {{ integration_footer_scripts|safe }}
            </div>
        </div>
        
        <script>
            console.log('🔍 Integration Test Page Loaded');
            console.log('Meta Pixel Check:', window.fbq ? 'Found' : 'Not Found');
            console.log('Full window.fbq object:', window.fbq);
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html, content_type='text/html')