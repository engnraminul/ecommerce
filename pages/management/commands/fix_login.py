from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix user login credentials'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔐 Fixing User Login Credentials'))
        self.stdout.write('=' * 50)
        
        email = 'aminul3065@gmail.com'
        password = 'aminul3065'
        
        try:
            # Try to find user by email
            user = User.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f'✅ Found user: {user.username}'))
            
        except User.DoesNotExist:
            # Try to find user by username
            try:
                user = User.objects.get(username='aminul')
                self.stdout.write(self.style.SUCCESS(f'✅ Found user by username: {user.username}'))
                # Update email
                user.email = email
                
            except User.DoesNotExist:
                # Create new user
                self.stdout.write(self.style.WARNING('❌ User not found, creating new user...'))
                user = User.objects.create_user(
                    username='aminul3065',
                    email=email,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created new user: {user.username}'))
        
        # Update user properties
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        
        self.stdout.write(self.style.SUCCESS('\n✅ User credentials updated!'))
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Staff Access: {user.is_staff}')
        self.stdout.write(f'Superuser: {user.is_superuser}')
        self.stdout.write(f'Active: {user.is_active}')
        
        # Show all existing users for reference
        self.stdout.write(self.style.SUCCESS('\n📋 All Users in System:'))
        for u in User.objects.all():
            status = '👑 Admin' if u.is_superuser else '👤 User'
            self.stdout.write(f'  {status} {u.username} ({u.email}) - Active: {u.is_active}')
        
        self.stdout.write(self.style.SUCCESS('\n🚪 Login Instructions:'))
        self.stdout.write('1. Go to: http://127.0.0.1:8000/mb-admin/')
        self.stdout.write(f'2. Username: {user.username}')
        self.stdout.write(f'3. Password: {password}')
        self.stdout.write('4. Click Login')
        
        self.stdout.write(self.style.SUCCESS('\n🎯 You can now access the Pages Dashboard!'))