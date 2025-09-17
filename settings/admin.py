from django.contrib import admin
from .models import Curier

@admin.register(Curier)
class CurierAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_url', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'api_url')
    readonly_fields = ('created_at', 'updated_at')
