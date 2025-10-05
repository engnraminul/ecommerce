import os
import json
from django.http import JsonResponse
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
        media_type = request.GET.get('type', 'all')  # all, images, videos
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        search = request.GET.get('search', '')
        
        # Define media directories to scan
        media_dirs = ['products', 'variants', 'reviews']
        all_files = []
        
        # Scan media directories
        for media_dir in media_dirs:
            dir_path = os.path.join(settings.MEDIA_ROOT, media_dir)
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        # Get file info
                        file_info = get_file_info(file_path, media_dir, filename)
                        
                        # Filter by type
                        if media_type != 'all':
                            if media_type == 'images' and not file_info['is_image']:
                                continue
                            elif media_type == 'videos' and not file_info['is_video']:
                                continue
                        
                        # Filter by search term
                        if search and search.lower() not in filename.lower():
                            continue
                            
                        all_files.append(file_info)
        
        # Sort by date (newest first)
        all_files.sort(key=lambda x: x['modified_date'], reverse=True)
        
        # Pagination
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_files = all_files[start_index:end_index]
        
        return JsonResponse({
            'success': True,
            'files': paginated_files,
            'total': len(all_files),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(all_files) + per_page - 1) // per_page
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

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
            'dimensions': f"{width}x{height}" if width and height else None
        }
    except Exception as e:
        return {
            'id': f"{directory}_{filename}",
            'filename': filename,
            'directory': directory,
            'url': f"{settings.MEDIA_URL}{directory}/{filename}",
            'error': str(e)
        }

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
        directory = request.POST.get('directory', 'products')
        
        # Validate file type
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not mime_type or not mime_type.startswith(('image/', 'video/')):
            return JsonResponse({
                'success': False,
                'message': 'Only image and video files are allowed'
            }, status=400)
        
        # Generate unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Save file
        file_path = f"{directory}/{unique_filename}"
        saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
        
        # Get file info
        full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
        file_info = get_file_info(full_path, directory, unique_filename)
        
        return JsonResponse({
            'success': True,
            'message': 'File uploaded successfully',
            'file': file_info
        })
        
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