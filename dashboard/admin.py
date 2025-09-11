from django.contrib import admin
from .models import DashboardSetting, AdminActivity

@admin.register(DashboardSetting)
class DashboardSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_repr', 'timestamp')
    list_filter = ('action', 'model_name', 'user', 'timestamp')
    search_fields = ('user__username', 'action', 'model_name', 'object_repr')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'object_repr', 
                      'changes', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
