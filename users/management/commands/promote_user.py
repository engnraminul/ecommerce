from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import DashboardPermission

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up specific user with staff and superuser permissions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email of the user to promote',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the user if creating new',
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create user if not exists',
        )
    
    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f'Found user: {user.username} ({user.email})')
        except User.DoesNotExist:
            if options['create']:
                username = options['username'] or email.split('@')[0]
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='temppassword123',  # They should change this
                    is_email_verified=True
                )
                self.stdout.write(f'Created user: {user.username} ({user.email})')
            else:
                self.stdout.write(self.style.ERROR(f'User with email {email} not found. Use --create to create.'))
                return
        
        # Make user staff and superuser
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        
        self.stdout.write(f'Updated user permissions:')
        self.stdout.write(f'  - is_staff: {user.is_staff}')
        self.stdout.write(f'  - is_superuser: {user.is_superuser}')
        self.stdout.write(f'  - is_active: {user.is_active}')
        
        # Create dashboard permissions with all tabs (although superuser has access anyway)
        all_tabs = [code for code, name in DashboardPermission.DASHBOARD_TABS]
        permission, created = DashboardPermission.objects.get_or_create(
            user=user,
            defaults={'allowed_tabs': all_tabs}
        )
        
        if not created:
            permission.allowed_tabs = all_tabs
            permission.save()
        
        self.stdout.write(f'Dashboard permissions: {"Created" if created else "Updated"} with all {len(all_tabs)} tabs')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up user {user.username} with full staff and superuser permissions!'
            )
        )