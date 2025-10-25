import os
import json
import shutil
import re
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
import uuid
from PIL import Image
import mimetypes

@require_http_methods(["GET"])
def list_media_files(request):
    """List all media files with pagination and filtering"""
    try:
        media_type = request.GET.get('type', 'all')  # all, image, video, document, other
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        search = request.GET.get('search', '')
        directory = request.GET.get('directory', '')
        sort_by = request.GET.get('sort', 'date_desc')  # date_desc, date_asc, name_asc, name_desc, size_desc, size_asc
        
        # Define media directories to scan
        media_dirs = ['products', 'variants', 'reviews', 'banners', 'avatars', 'documents', 'categories']
        all_files = []
        total_size = 0
        directories_found = set()
        
        # Scan media directories
        for media_dir in media_dirs:
            dir_path = os.path.join(settings.MEDIA_ROOT, media_dir)
            if os.path.exists(dir_path):
                directories_found.add(media_dir)
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        # Get file info
                        file_info = get_file_info(file_path, media_dir, filename)
                        
                        # Filter by directory
                        if directory and media_dir != directory:
                            continue
                        
                        # Filter by type
                        if media_type != 'all':
                            file_type = get_file_type(file_info['mime_type'])
                            if media_type != file_type:
                                continue
                        
                        # Filter by search term
                        if search and search.lower() not in filename.lower():
                            continue
                        
                        total_size += file_info['size']
                        all_files.append(file_info)
        
        # Sort files
        if sort_by == 'date_desc':
            all_files.sort(key=lambda x: x['modified_date'], reverse=True)
        elif sort_by == 'date_asc':
            all_files.sort(key=lambda x: x['modified_date'])
        elif sort_by == 'name_asc':
            all_files.sort(key=lambda x: x['filename'].lower())
        elif sort_by == 'name_desc':
            all_files.sort(key=lambda x: x['filename'].lower(), reverse=True)
        elif sort_by == 'size_desc':
            all_files.sort(key=lambda x: x['size'], reverse=True)
        elif sort_by == 'size_asc':
            all_files.sort(key=lambda x: x['size'])
        
        # Pagination
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_files = all_files[start_index:end_index]
        
        return JsonResponse({
            'success': True,
            'files': paginated_files,
            'total': len(all_files),
            'total_size': total_size,
            'total_size_formatted': format_file_size(total_size),
            'directories': list(directories_found),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(all_files) + per_page - 1) // per_page if all_files else 1
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

def get_file_type(mime_type):
    """Determine file type category from MIME type"""
    if not mime_type:
        return 'other'
    
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type in ['application/pdf', 'application/msword', 
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                      'application/vnd.ms-excel',
                      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      'text/plain', 'text/csv']:
        return 'document'
    else:
        return 'other'

def get_file_info(file_path, directory, filename):
    """Get detailed file information"""
    try:
        stat = os.stat(file_path)
        file_size = stat.st_size
        modified_date = datetime.fromtimestamp(stat.st_mtime)
        
        # Determine file type
        mime_type, _ = mimetypes.guess_type(filename)
        is_image = mime_type and mime_type.startswith('image/')
        is_video = mime_type and mime_type.startswith('video/')
        
        # Get image dimensions if it's an image
        width, height = None, None
        if is_image:
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
            except:
                pass
        
        # Generate URL
        file_url = f"{settings.MEDIA_URL}{directory}/{filename}"
        
        return {
            'id': f"{directory}_{filename}",
            'filename': filename,
            'directory': directory,
            'url': file_url,
            'size': file_size,
            'size_formatted': format_file_size(file_size),
            'modified_date': modified_date,
            'modified_date_formatted': modified_date.strftime('%Y-%m-%d %H:%M:%S'),
            'mime_type': mime_type,
            'is_image': is_image,
            'is_video': is_video,
            'width': width,
            'height': height,
            'dimensions': f"{width}x{height}" if width and height else None,
            'file_type': get_file_type(mime_type)
        }
    except Exception as e:
        return {
            'id': f"{directory}_{filename}",
            'filename': filename,
            'directory': directory,
            'url': f"{settings.MEDIA_URL}{directory}/{filename}",
            'error': str(e)
        }

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal and ensure safe filenames"""
    # Extract file extension
    name, ext = os.path.splitext(filename)
    
    # Remove or replace problematic characters
    # Keep only alphanumeric, hyphens, underscores, and spaces
    name = re.sub(r'[^\w\s-]', '', name)
    
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    
    # Remove multiple consecutive underscores/hyphens
    name = re.sub(r'[-_]{2,}', '_', name)
    
    # Remove leading/trailing underscores/hyphens
    name = name.strip('_-')
    
    # Ensure filename is not empty
    if not name:
        name = 'file'
    
    # Limit filename length
    if len(name) > 50:
        name = name[:50]
    
    return f"{name}{ext.lower()}"

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

@csrf_exempt
@require_http_methods(["POST"])
def upload_media_file(request):
    """Upload a new media file"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        directory = request.POST.get('directory', 'products').strip()
        
        # Sanitize and validate directory name
        if directory:
            # Remove any path separators and normalize
            directory = os.path.basename(directory)
            directory = re.sub(r'[^\w\s-]', '', directory)
            directory = re.sub(r'\s+', '_', directory)
            directory = directory.strip('_-')
        
        if not directory:
            directory = 'products'
        
        # Validate directory name against allowed directories
        allowed_dirs = ['products', 'variants', 'reviews', 'banners', 'avatars', 'documents', 'categories']
        if directory not in allowed_dirs:
            # Allow custom directories but validate they're safe
            if not re.match(r'^[a-zA-Z0-9_-]+$', directory):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid directory name. Only letters, numbers, hyphens, and underscores are allowed.'
                }, status=400)
        
        # Validate file type (more permissive)
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        allowed_types = [
            'image/', 'video/', 'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'text/csv'
        ]
        
        if mime_type and not any(mime_type.startswith(t) for t in allowed_types):
            return JsonResponse({
                'success': False,
                'message': 'File type not allowed'
            }, status=400)
        
        # Generate safe and unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        original_name = os.path.splitext(uploaded_file.name)[0]
        
        # Sanitize the original filename
        safe_name = sanitize_filename(uploaded_file.name)
        name_without_ext = os.path.splitext(safe_name)[0]
        
        # Generate unique filename with timestamp and random string
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_string = uuid.uuid4().hex[:6]
        unique_filename = f"{name_without_ext}_{timestamp}_{random_string}{file_extension}"
        
        # Ensure filename doesn't exceed filesystem limits
        if len(unique_filename) > 255:
            # Truncate name part if too long
            max_name_length = 255 - len(file_extension) - len(timestamp) - len(random_string) - 2  # 2 for underscores
            name_without_ext = name_without_ext[:max_name_length]
            unique_filename = f"{name_without_ext}_{timestamp}_{random_string}{file_extension}"
        
        # Ensure directory exists
        dir_path = os.path.join(settings.MEDIA_ROOT, directory)
        try:
            os.makedirs(dir_path, exist_ok=True)
        except OSError as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to create directory: {str(e)}'
            }, status=500)
        
        # Save file with safety checks
        file_path = f"{directory}/{unique_filename}"
        
        # Additional safety check for the final path
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        normalized_path = os.path.normpath(full_path)
        
        # Ensure the path is within MEDIA_ROOT
        if not normalized_path.startswith(os.path.normpath(settings.MEDIA_ROOT)):
            return JsonResponse({
                'success': False,
                'message': 'Invalid file path detected'
            }, status=400)
        
        try:
            saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to save file: {str(e)}'
            }, status=500)
        
        # Get file info
        try:
            full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
            file_info = get_file_info(full_path, directory, unique_filename)
            
            return JsonResponse({
                'success': True,
                'message': 'File uploaded successfully',
                'file': file_info
            })
        except Exception as e:
            # If we fail to get file info, at least confirm the upload worked
            return JsonResponse({
                'success': True,
                'message': 'File uploaded successfully',
                'file': {
                    'id': f"{directory}_{unique_filename}",
                    'filename': unique_filename,
                    'directory': directory,
                    'url': f"{settings.MEDIA_URL}{directory}/{unique_filename}",
                    'original_filename': uploaded_file.name
                }
            })
        
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Upload error for file '{uploaded_file.name}': {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def edit_media_file(request, file_id):
    """Edit media file metadata"""
    try:
        # Parse file ID (format: directory_filename)
        parts = file_id.split('_', 1)
        if len(parts) != 2:
            return JsonResponse({
                'success': False,
                'message': 'Invalid file ID'
            }, status=400)
        
        directory, filename = parts
        file_path = os.path.join(settings.MEDIA_ROOT, directory, filename)
        
        if not os.path.exists(file_path):
            return JsonResponse({
                'success': False,
                'message': 'File not found'
            }, status=404)
        
        # Parse request data
        data = json.loads(request.body)
        new_filename = data.get('filename')
        new_directory = data.get('directory')
        alt_text = data.get('alt_text')  # For future use
        
        # Handle filename change
        if new_filename and new_filename != filename:
            # Preserve file extension
            file_extension = os.path.splitext(filename)[1]
            if not new_filename.endswith(file_extension):
                new_filename += file_extension
            
            new_file_path = os.path.join(settings.MEDIA_ROOT, directory, new_filename)
            
            # Check if new filename already exists
            if os.path.exists(new_file_path):
                return JsonResponse({
                    'success': False,
                    'message': 'A file with that name already exists'
                }, status=400)
            
            # Rename file
            os.rename(file_path, new_file_path)
            file_path = new_file_path
            filename = new_filename
        
        # Handle directory change
        if new_directory and new_directory != directory:
            new_dir_path = os.path.join(settings.MEDIA_ROOT, new_directory)
            os.makedirs(new_dir_path, exist_ok=True)
            
            new_file_path = os.path.join(new_dir_path, filename)
            
            # Check if file already exists in new directory
            if os.path.exists(new_file_path):
                return JsonResponse({
                    'success': False,
                    'message': 'A file with that name already exists in the target directory'
                }, status=400)
            
            # Move file
            shutil.move(file_path, new_file_path)
            file_path = new_file_path
            directory = new_directory
        
        # Get updated file info
        file_info = get_file_info(file_path, directory, filename)
        
        return JsonResponse({
            'success': True,
            'message': 'File updated successfully',
            'file': file_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def download_media_file(request, file_id):
    """Download a media file"""
    try:
        # Parse file ID (format: directory_filename)
        parts = file_id.split('_', 1)
        if len(parts) != 2:
            return JsonResponse({
                'success': False,
                'message': 'Invalid file ID'
            }, status=400)
        
        directory, filename = parts
        file_path = os.path.join(settings.MEDIA_ROOT, directory, filename)
        
        if not os.path.exists(file_path):
            return JsonResponse({
                'success': False,
                'message': 'File not found'
            }, status=404)
        
        # Determine content type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Read and return file
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=mime_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_http_methods(["DELETE"])
def delete_media_file(request, file_id):
    """Delete a media file"""
    try:
        # Parse file ID (format: directory_filename)
        parts = file_id.split('_', 1)
        if len(parts) != 2:
            return JsonResponse({
                'success': False,
                'message': 'Invalid file ID'
            }, status=400)
        
        directory, filename = parts
        file_path = os.path.join(settings.MEDIA_ROOT, directory, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return JsonResponse({
                'success': True,
                'message': 'File deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'File not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_directory(request):
    """Create a new media directory"""
    try:
        data = json.loads(request.body)
        directory_name = data.get('name', '').strip()
        
        if not directory_name:
            return JsonResponse({
                'success': False,
                'message': 'Directory name is required'
            }, status=400)
        
        # Validate directory name
        if not directory_name.replace('-', '').replace('_', '').isalnum():
            return JsonResponse({
                'success': False,
                'message': 'Invalid directory name. Only letters, numbers, hyphens, and underscores are allowed.'
            }, status=400)
        
        # Create directory
        dir_path = os.path.join(settings.MEDIA_ROOT, directory_name)
        
        if os.path.exists(dir_path):
            return JsonResponse({
                'success': False,
                'message': 'Directory already exists'
            }, status=400)
        
        os.makedirs(dir_path, exist_ok=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Directory created successfully',
            'directory': directory_name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)