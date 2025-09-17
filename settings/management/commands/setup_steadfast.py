from django.core.management.base import BaseCommand
from settings.models import Curier

class Command(BaseCommand):
    help = 'Creates a SteadFast courier configuration'

    def add_arguments(self, parser):
        parser.add_argument('--api_url', required=True, help='SteadFast API URL')
        parser.add_argument('--api_key', required=True, help='SteadFast API Key')
        parser.add_argument('--secret_key', required=True, help='SteadFast Secret Key')
        
    def handle(self, *args, **options):
        api_url = options['api_url']
        api_key = options['api_key']
        secret_key = options['secret_key']
        
        # Check if SteadFast configuration already exists
        steadfast = Curier.objects.filter(name='steadFast').first()
        
        if steadfast:
            # Update existing configuration
            steadfast.api_url = api_url
            steadfast.api_key = api_key
            steadfast.secret_key = secret_key
            steadfast.is_active = True
            steadfast.save()
            self.stdout.write(self.style.SUCCESS(f'Updated SteadFast courier configuration'))
        else:
            # Create new configuration
            Curier.objects.create(
                name='steadFast',
                api_url=api_url,
                api_key=api_key,
                secret_key=secret_key,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created new SteadFast courier configuration'))