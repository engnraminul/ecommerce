"""
Professional Dashboard Admin User Creation Command
Creates admin users with enhanced security features for MB Dashboard
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import getpass
import secrets
import string

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a secure admin user for MB Dashboard'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for admin user')
        parser.add_argument('--email', type=str, help='Email for admin user')
        parser.add_argument('--first-name', type=str, help='First name for admin user')
        parser.add_argument('--last-name', type=str, help='Last name for admin user')
        parser.add_argument('--auto-password', action='store_true', 
                          help='Generate a secure random password')
        parser.add_argument('--quiet', action='store_true', 
                          help='Suppress all output except errors')

    def handle(self, *args, **options):
        """Create admin user with enhanced security"""
        
        if not options['quiet']:
            self.stdout.write(
                self.style.SUCCESS('🔐 Creating MB Dashboard Admin User')
            )
        
        # Get username
        username = options.get('username')
        if not username:
            username = input('Username: ').strip()
        
        if not username:
            raise CommandError('Username is required')
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists')
        
        # Get email
        email = options.get('email')
        if not email:
            email = input('Email address: ').strip()
        
        # Get first and last name
        first_name = options.get('first_name', '')
        if not first_name:
            first_name = input('First name (optional): ').strip()
        
        last_name = options.get('last_name', '')
        if not last_name:
            last_name = input('Last name (optional): ').strip()
        
        # Handle password
        if options.get('auto_password'):
            password = self.generate_secure_password()
            if not options['quiet']:
                self.stdout.write(
                    self.style.WARNING(f'Generated secure password: {password}')
                )
                self.stdout.write(
                    self.style.WARNING('⚠️  Please save this password securely!')
                )
        else:
            password = self.get_password()
        
        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            raise CommandError(f'Password validation failed: {", ".join(e.messages)}')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            if not options['quiet']:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Admin user "{username}" created successfully!')
                )
                self.stdout.write(f'   Email: {email}')
                if first_name or last_name:
                    self.stdout.write(f'   Name: {first_name} {last_name}'.strip())
                self.stdout.write(f'   Staff: ✅')
                self.stdout.write(f'   Superuser: ✅')
                self.stdout.write(f'   Active: ✅')
                self.stdout.write('')
                self.stdout.write('🔑 User can now access MB Dashboard at /mb-admin/')
            
        except IntegrityError as e:
            if 'email' in str(e).lower():
                raise CommandError(f'Email "{email}" is already in use')
            else:
                raise CommandError(f'Error creating user: {e}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')

    def get_password(self):
        """Get password from user with confirmation"""
        while True:
            password = getpass.getpass('Password: ')
            if not password:
                self.stdout.write(self.style.ERROR('Password cannot be empty'))
                continue
            
            password_confirm = getpass.getpass('Confirm password: ')
            
            if password == password_confirm:
                return password
            else:
                self.stdout.write(self.style.ERROR('Passwords do not match. Please try again.'))

    def generate_secure_password(self, length=16):
        """Generate a secure random password"""
        # Use a mix of uppercase, lowercase, digits, and safe special characters
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        # Ensure password has at least one from each category
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice('!@#$%^&*()_+-=')
        ]
        
        # Fill the rest randomly
        for _ in range(length - 4):
            password.append(secrets.choice(alphabet))
        
        # Shuffle the password list
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)