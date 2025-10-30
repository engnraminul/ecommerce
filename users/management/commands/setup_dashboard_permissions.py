from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import DashboardPermission

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup default dashboard permissions for existing users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all-tabs',
            action='store_true',
            help='Give all tabs access to staff users by default',
        )
        parser.add_argument(
            '--basic-tabs',
            action='store_true',
            help='Give basic tabs access to regular users by default (orders, products, statistics)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up dashboard permissions...')
        
        # All available tabs
        all_tabs = [code for code, name in DashboardPermission.DASHBOARD_TABS]
        
        # Basic tabs for regular users
        basic_tabs = ['home', 'orders', 'products', 'statistics']
        
        users_updated = 0
        permissions_created = 0
        
        for user in User.objects.all():
            # Skip superusers (they have access to everything anyway)
            if user.is_superuser:
                self.stdout.write(f'Skipping superuser: {user.username}')
                continue
            
            # Check if user already has dashboard permissions
            permission, created = DashboardPermission.objects.get_or_create(
                user=user,
                defaults={'allowed_tabs': []}
            )
            
            if created:
                permissions_created += 1
                
                # Set default permissions based on user type and options
                if options['all_tabs'] and user.is_staff:
                    permission.allowed_tabs = all_tabs
                    permission.save()
                    self.stdout.write(f'Staff user {user.username}: granted access to all tabs')
                elif options['basic_tabs'] and not user.is_staff:
                    permission.allowed_tabs = basic_tabs
                    permission.save()
                    self.stdout.write(f'Regular user {user.username}: granted access to basic tabs')
                else:
                    self.stdout.write(f'User {user.username}: created with no default permissions')
                
                users_updated += 1
            else:
                self.stdout.write(f'User {user.username}: already has dashboard permissions set')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {User.objects.count()} users. '
                f'Created permissions for {permissions_created} users. '
                f'Updated {users_updated} users.'
            )
        )
        
        # Show summary
        self.stdout.write('\nDashboard Permissions Summary:')
        self.stdout.write(f'Superusers: {User.objects.filter(is_superuser=True).count()} (automatic full access)')
        self.stdout.write(f'Staff users: {User.objects.filter(is_staff=True, is_superuser=False).count()}')
        self.stdout.write(f'Regular users: {User.objects.filter(is_staff=False, is_superuser=False).count()}')
        self.stdout.write(f'Users with dashboard permissions: {DashboardPermission.objects.count()}')