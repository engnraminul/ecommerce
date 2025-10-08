# Media Management Dashboard

## Overview
The Media Management Dashboard provides a comprehensive interface for managing all media files in your ecommerce application. It offers advanced features for uploading, organizing, editing, and deleting media files with a user-friendly interface.

## Features

### 📁 File Management
- **Upload Multiple Files**: Drag & drop or browse to upload multiple files simultaneously
- **File Organization**: Organize files into directories (products, banners, avatars, documents, etc.)
- **File Filtering**: Filter by file type, directory, search terms, and sort options
- **File Operations**: Rename, move, download, and delete files
- **Bulk Operations**: Select multiple files for bulk deletion or operations

### 🎯 Advanced Filtering
- **File Type Filters**: Filter by images, videos, documents, or other file types
- **Directory Filters**: View files from specific directories
- **Search Functionality**: Search files by name
- **Sorting Options**: Sort by date, name, or file size (ascending/descending)

### 📊 Statistics & Analytics
- **Total Files Count**: Track total number of files
- **Storage Usage**: Monitor total storage space used
- **Directory Count**: Number of directories in use
- **Selected Files**: Track currently selected files

### 🔧 File Operations
- **Inline Editing**: Edit file names and move files between directories
- **Metadata Management**: Add alt text for images
- **File Preview**: Preview images directly in the interface
- **Download Files**: Download individual files or bulk download

## Interface Components

### Main Dashboard
- **Header Section**: Page title with action buttons (Select All, Clear Selection, Upload)
- **Statistics Bar**: Real-time statistics about files and storage
- **Bulk Actions Bar**: Appears when files are selected for bulk operations
- **Filters Section**: Comprehensive filtering and search options
- **Media Grid**: Visual grid layout of all media files
- **Pagination**: Navigate through multiple pages of files

### Upload Modal
- **Directory Selection**: Choose target directory or create new one
- **Drag & Drop Zone**: Intuitive file dropping area
- **File Browser**: Traditional file selection option
- **Upload Progress**: Real-time upload progress tracking
- **File Preview**: Preview selected files before upload

### Edit File Modal
- **Filename Editing**: Rename files (preserves extension)
- **Directory Management**: Move files between directories
- **Alt Text**: Add accessibility descriptions for images
- **File Information**: Display file metadata

## API Endpoints

### List Media Files
```
GET /mb-admin/api/media/
```
**Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `type`: File type filter (all, image, video, document, other)
- `directory`: Directory filter
- `search`: Search term
- `sort`: Sort order (date_desc, date_asc, name_asc, name_desc, size_desc, size_asc)

**Response:**
```json
{
    "success": true,
    "files": [...],
    "total": 150,
    "total_size": 52428800,
    "total_size_formatted": "50.0 MB",
    "directories": ["products", "banners", "avatars"],
    "page": 1,
    "per_page": 20,
    "total_pages": 8
}
```

### Upload Media File
```
POST /mb-admin/api/media/upload/
```
**Parameters:**
- `file`: File to upload (multipart/form-data)
- `directory`: Target directory (optional)

### Edit Media File
```
PUT /mb-admin/api/media/{file_id}/edit/
```
**Body:**
```json
{
    "filename": "new-filename",
    "directory": "new-directory",
    "alt_text": "Image description"
}
```

### Download Media File
```
GET /mb-admin/api/media/{file_id}/download/
```

### Delete Media File
```
DELETE /mb-admin/api/media/{file_id}/delete/
```

### Create Directory
```
POST /mb-admin/api/media/directories/create/
```
**Body:**
```json
{
    "name": "directory-name"
}
```

## File Structure

### Templates
- `dashboard/templates/dashboard/media.html`: Main media management interface
- `dashboard/templates/dashboard/base.html`: Updated with media navigation link

### Python Files
- `dashboard/views.py`: Added `dashboard_media` view function
- `dashboard/media_api.py`: Enhanced API with new endpoints
- `dashboard/urls.py`: Updated URL patterns

### JavaScript Features
- Drag & drop file upload
- Real-time filtering and search
- Bulk selection and operations
- AJAX-based file operations
- Progress tracking for uploads

## Usage Examples

### Basic File Upload
1. Navigate to Media tab in dashboard
2. Click "Upload Files" button
3. Select directory (or create new one)
4. Drag files to upload zone or browse files
5. Click "Start Upload"

### File Organization
1. Select files you want to move
2. Use bulk actions to move to different directory
3. Or edit individual files to rename/move them

### Search and Filter
1. Use search box to find specific files
2. Apply filters by type or directory
3. Sort results by different criteria
4. Use pagination to navigate results

## Security Features

- **Admin-only Access**: Only admin users can access media management
- **CSRF Protection**: All form submissions protected against CSRF attacks
- **File Type Validation**: Only allowed file types can be uploaded
- **Directory Validation**: Directory names validated for security

## File Types Supported

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)
- SVG (.svg)

### Videos
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- WebM (.webm)

### Documents
- PDF (.pdf)
- Word Documents (.doc, .docx)
- Excel Files (.xls, .xlsx)
- Text Files (.txt)
- CSV Files (.csv)

## Integration with Products

The media management system is fully integrated with the product management system:

- **Product Images**: Upload and select images for products
- **Variant Images**: Manage variant-specific images
- **Media Library Modal**: Access media library from product forms
- **Image Selection**: Easy selection from uploaded media files

## Performance Considerations

- **Lazy Loading**: Images load as needed to improve performance
- **Pagination**: Large file collections are paginated
- **Caching**: File information is cached for better performance
- **Optimized Queries**: Database queries are optimized for speed

## Troubleshooting

### Common Issues

1. **Upload Fails**: Check file size limits and allowed file types
2. **Files Not Showing**: Verify directory permissions and file paths
3. **Edit Not Working**: Ensure CSRF token is valid and user has permissions
4. **Performance Issues**: Consider pagination settings and file optimization

### Error Messages

- **"Invalid file type"**: File type not in allowed list
- **"File not found"**: File may have been deleted or moved
- **"Directory already exists"**: Choose a different directory name
- **"Permission denied"**: Check user permissions and file system access

## Future Enhancements

- **Image Editing**: Basic image editing capabilities
- **Batch Processing**: Resize or optimize multiple images
- **Cloud Storage**: Integration with cloud storage services
- **Advanced Search**: Search by file metadata and content
- **Version Control**: Track file versions and changes
- **CDN Integration**: Content delivery network support

## Configuration

### Settings
```python
# Media settings in settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB
```

### Permissions
Ensure the web server has read/write permissions to the media directory:
```bash
chmod 755 media/
chmod 644 media/*
```

This comprehensive media management system provides a professional, user-friendly interface for managing all media files in your ecommerce application, with advanced features for organization, search, and bulk operations.