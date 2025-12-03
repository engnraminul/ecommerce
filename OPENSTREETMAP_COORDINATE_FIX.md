# OpenStreetMap URL and Coordinate Fix

## Problem
When saving OpenStreetMap URLs (like `https://www.openstreetmap.org/?#map=19/23.892996/90.382711`) in the contact settings, the map location was not showing marked on the contact page.

## Root Cause
The contact page expected `map_coordinates` in "lat,lon" format, but the dashboard form only accepted `map_embed_url`. There was no conversion between different URL formats and coordinate extraction.

## Solution

### 1. Created Universal Coordinate Extraction Function
Added `extract_coordinates_from_url()` function that supports multiple URL formats:

**Supported URL Formats:**
- ✅ OpenStreetMap: `https://www.openstreetmap.org/?#map=19/23.892996/90.382711`
- ✅ Google Maps: `https://www.google.com/maps/@23.892996,90.382711,17z`
- ✅ Google Maps Query: `https://maps.google.com/?q=23.892996,90.382711`
- ✅ Embed URLs: `https://www.openstreetmap.org/export/embed.html?marker=23.7809,90.3493`
- ✅ Direct Coordinates: `23.892996,90.382711`

### 2. Enhanced Contact Settings Processing
- Automatically extracts coordinates from any supported map URL
- Stores both `map_embed_url` and `map_coordinates` in settings
- Backward compatible with existing data

### 3. Updated Dashboard Form
- Changed field label from "Google Maps Embed URL" to "Map URL or Coordinates"
- Added comprehensive help text with examples
- Updated placeholder to show OpenStreetMap URL example

### 4. Improved Contact Page Rendering
- Uses extracted coordinates for Leaflet map display
- Shows proper marker at the exact location
- Falls back to default location if no coordinates available

## Files Modified

### `contact/views.py`
1. **Added coordinate extraction function**:
   ```python
   def extract_coordinates_from_url(url):
       # Supports multiple URL formats with regex patterns
       # Returns 'lat,lon' string or None
   ```

2. **Enhanced `update_contact_settings()`**:
   - Automatically extracts coordinates from map URLs
   - Stores both URL and coordinates
   - Added logging for coordinate extraction

3. **Updated `contact_page()` function**:
   - Uses new extraction function for coordinate processing
   - Better fallback handling
   - Updated default settings

### `dashboard/templates/dashboard/contacts.html`
- **Updated form field**:
  - Changed label: "Google Maps Embed URL" → "Map URL or Coordinates"
  - Added comprehensive help text
  - Updated placeholder with OpenStreetMap example

## Usage Examples

### For Administrators
1. **OpenStreetMap (Recommended)**:
   - Go to https://www.openstreetmap.org
   - Navigate to your location
   - Copy the URL from browser address bar
   - Example: `https://www.openstreetmap.org/?#map=19/23.892996/90.382711`

2. **Google Maps**:
   - Go to https://maps.google.com
   - Right-click on location → "What's here?"
   - Copy coordinates or share link
   - Example: `https://www.google.com/maps/@23.892996,90.382711,17z`

3. **Direct Coordinates**:
   - Simply enter: `23.892996,90.382711`
   - Format: `latitude,longitude`

### How It Works
1. User enters any supported map URL or coordinates
2. System automatically extracts coordinates using regex patterns
3. Both original URL and coordinates are saved
4. Contact page uses coordinates for Leaflet map display
5. Map shows exact location with custom marker

## Technical Details

### Coordinate Extraction Patterns
```python
# OpenStreetMap: #map=zoom/lat/lon
osm_pattern1 = r'openstreetmap\.org/.*#map=\d+/([\d.-]+)/([\d.-]+)'

# Google Maps: @lat,lon,zoom
google_pattern2 = r'google\.com/maps/@([\d.-]+),([\d.-]+),\d+z'

# Embed marker: marker=lat,lon
marker_pattern = r'marker=([\d.-]+),([\d.-]+)'

# Direct coordinates: lat,lon
coord_pattern = r'^([\d.-]+)\s*,\s*([\d.-]+)$'
```

### Map Display
- Uses Leaflet.js with OpenStreetMap tiles
- Custom marker with business logo
- Popup with business address
- Zoom level 16 for good detail
- Fallback to Dhaka coordinates if no location set

## Testing Results
✅ OpenStreetMap URLs properly parsed  
✅ Google Maps URLs properly parsed  
✅ Direct coordinates accepted  
✅ Map marker displays at correct location  
✅ Backward compatible with existing settings  
✅ Error handling for invalid URLs  

## Benefits
- **User-Friendly**: Accept any map URL format
- **Accurate**: Exact coordinate extraction and display
- **Flexible**: Multiple input formats supported
- **Reliable**: Proper error handling and fallbacks
- **Modern**: Uses OpenStreetMap instead of proprietary solutions