from django.core.management.base import BaseCommand
from fraud_checker.services import PackzyFraudChecker
from settings.models import Curier


class Command(BaseCommand):
    help = 'Test fraud checker API with configured credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            'phone_number',
            type=str,
            help='Phone number to check for fraud'
        )
        parser.add_argument(
            '--mock',
            action='store_true',
            help='Use mock data instead of real API'
        )

    def handle(self, *args, **options):
        phone_number = options['phone_number']
        use_mock = options['mock']
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('FRAUD CHECKER TEST'))
        self.stdout.write("=" * 60)
        
        # Show courier configuration
        self.stdout.write("\n📋 COURIER CONFIGURATION:")
        try:
            couriers = Curier.objects.filter(is_active=True)
            if couriers.exists():
                for courier in couriers:
                    self.stdout.write(f"   • {courier.name}")
                    self.stdout.write(f"     API URL: {courier.api_url}")
                    self.stdout.write(f"     API Key: {courier.api_key[:10]}... (hidden)")
                    self.stdout.write(f"     Secret Key: {'*' * len(courier.secret_key) if courier.secret_key else 'Not set'}")
                    self.stdout.write("")
            else:
                self.stdout.write(self.style.WARNING("   No active couriers configured"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   Error loading couriers: {e}"))
        
        # Initialize fraud checker
        self.stdout.write("🔧 INITIALIZING FRAUD CHECKER:")
        fraud_checker = PackzyFraudChecker()
        
        # Set mock mode if requested
        if use_mock:
            fraud_checker.USE_MOCK_DATA = True
            self.stdout.write(self.style.WARNING("   Using mock data"))
        
        # Show credentials status
        cred_status = fraud_checker.get_credentials_status()
        self.stdout.write(f"   API Key: {'✓' if cred_status['api_key_configured'] else '✗'}")
        self.stdout.write(f"   Secret Key: {'✓' if cred_status['secret_key_configured'] else '✗'}")
        if cred_status['api_key_preview']:
            self.stdout.write(f"   API Key Preview: {cred_status['api_key_preview']}")
        
        # Perform fraud check
        self.stdout.write(f"\n🔍 CHECKING PHONE NUMBER: {phone_number}")
        self.stdout.write("-" * 40)
        
        try:
            result = fraud_checker.check_fraud(phone_number)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS("✓ FRAUD CHECK SUCCESSFUL"))
                self.stdout.write(f"   📱 Phone: {result.get('phone_number', 'N/A')}")
                self.stdout.write(f"   📦 Total Parcels: {result.get('total_parcels', 0)}")
                self.stdout.write(f"   ✅ Delivered: {result.get('total_delivered', 0)}")
                self.stdout.write(f"   ❌ Cancelled: {result.get('total_cancelled', 0)}")
                self.stdout.write(f"   ⚠️  Fraud Reports: {len(result.get('total_fraud_reports', []))}")
                self.stdout.write(f"   🎯 Fraud Score: {result.get('fraud_score', 0)}")
                
                risk_level = result.get('risk_level', 'UNKNOWN')
                risk_colors = {
                    'HIGH': self.style.ERROR,
                    'MEDIUM': self.style.WARNING,
                    'LOW': self.style.HTTP_INFO,
                    'MINIMAL': self.style.SUCCESS,
                    'UNKNOWN': self.style.WARNING
                }
                color_func = risk_colors.get(risk_level, self.style.WARNING)
                self.stdout.write(f"   🚨 Risk Level: {color_func(risk_level)}")
                
            else:
                self.stdout.write(self.style.ERROR("✗ FRAUD CHECK FAILED"))
                self.stdout.write(f"   Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ EXCEPTION OCCURRED: {e}"))
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Test completed!")