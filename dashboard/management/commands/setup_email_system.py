"""
Management command to setup default email templates and configuration.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from dashboard.models import EmailConfiguration, EmailTemplate


class Command(BaseCommand):
    help = 'Setup default email templates and configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing templates to defaults',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up email system...')
        
        # Create default Gmail configuration
        self.create_default_email_config()
        
        # Create default email templates
        self.create_default_templates(reset=options['reset'])
        
        self.stdout.write(
            self.style.SUCCESS('Email system setup completed successfully!')
        )

    def create_default_email_config(self):
        """Create default email configuration if none exists."""
        if not EmailConfiguration.objects.exists():
            config = EmailConfiguration.objects.create(
                name="Default Gmail Configuration",
                smtp_type="gmail",
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                smtp_use_tls=True,
                smtp_use_ssl=False,
                smtp_username="your-email@gmail.com",
                smtp_password="your-app-password",
                from_email="your-email@gmail.com",
                from_name="Your Store",
                is_active=False,  # Set to False until properly configured
                is_verified=False,
            )
            self.stdout.write(f'Created default email configuration: {config.name}')
        else:
            self.stdout.write('Email configuration already exists')

    def create_default_templates(self, reset=False):
        """Create default email templates."""
        templates = [
            {
                'name': 'Welcome Email',
                'template_type': 'welcome',
                'subject': 'Welcome to {{site_name}}!',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333; text-align: center;">Welcome to {{site_name}}!</h1>
                    <p>Hi {{user_name}},</p>
                    <p>Welcome to our store! We're excited to have you as a customer.</p>
                    <p>You can now:</p>
                    <ul>
                        <li>Browse our products</li>
                        <li>Add items to your cart</li>
                        <li>Track your orders</li>
                        <li>Manage your account</li>
                    </ul>
                    <p>If you have any questions, feel free to contact us.</p>
                    <p>Happy shopping!</p>
                    <br>
                    <p>Best regards,<br>The {{site_name}} Team</p>
                </div>
                ''',
                'description': 'Welcome email sent to new users after registration',
            },
            {
                'name': 'Account Activation',
                'template_type': 'activation',
                'subject': 'Activate your {{site_name}} account',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333; text-align: center;">Activate Your Account</h1>
                    <p>Hi {{user_name}},</p>
                    <p>Thank you for registering with {{site_name}}! To complete your registration, please click the button below to activate your account:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{activation_url}}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Activate Account</a>
                    </div>
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{{activation_url}}">{{activation_url}}</a></p>
                    <p>This activation link will expire in 7 days.</p>
                    <p>If you didn't create an account with us, please ignore this email.</p>
                    <br>
                    <p>Best regards,<br>The {{site_name}} Team</p>
                </div>
                ''',
                'description': 'Email sent to users to activate their account',
            },
            {
                'name': 'Password Reset',
                'template_type': 'password_reset',
                'subject': 'Reset your {{site_name}} password',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333; text-align: center;">Reset Your Password</h1>
                    <p>Hi {{user_name}},</p>
                    <p>We received a request to reset the password for your {{site_name}} account.</p>
                    <p>Click the button below to reset your password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{reset_url}}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a>
                    </div>
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{{reset_url}}">{{reset_url}}</a></p>
                    <p>This password reset link will expire in 24 hours.</p>
                    <p>If you didn't request this password reset, please ignore this email. Your password will remain unchanged.</p>
                    <br>
                    <p>Best regards,<br>The {{site_name}} Team</p>
                </div>
                ''',
                'description': 'Email sent to users when they request a password reset',
            },
            {
                'name': 'Order Confirmed',
                'template_type': 'order_confirmed',
                'subject': 'Order Confirmation - Order #{{order_number}}',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333; text-align: center;">Order Confirmed!</h1>
                    <p>Hi {{user_name}},</p>
                    <p>Thank you for your order! We've received your order and it's being processed.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Order Details</h3>
                        <p><strong>Order Number:</strong> {{order_number}}</p>
                        <p><strong>Order Date:</strong> {{order_date|date:"F d, Y"}}</p>
                        <p><strong>Total Amount:</strong> ${{order_total}}</p>
                    </div>
                    
                    <p>We'll send you another email when your order ships with tracking information.</p>
                    <p>You can track your order status by logging into your account on our website.</p>
                    <p>If you have any questions about your order, please contact us.</p>
                    <br>
                    <p>Best regards,<br>The {{site_name}} Team</p>
                </div>
                ''',
                'description': 'Email sent when an order is confirmed',
            },
            {
                'name': 'Order Shipped',
                'template_type': 'order_shipped',
                'subject': 'Your order is on its way! - Order #{{order_number}}',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333; text-align: center;">Your Order Has Shipped!</h1>
                    <p>Hi {{user_name}},</p>
                    <p>Great news! Your order has been shipped and is on its way to you.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Shipping Details</h3>
                        <p><strong>Order Number:</strong> {{order_number}}</p>
                        <p><strong>Tracking Number:</strong> {{tracking_number}}</p>
                        <p><strong>Carrier:</strong> {{carrier}}</p>
                    </div>
                    
                    <p>You can track your package using the tracking number above on the carrier's website.</p>
                    <p>Your order should arrive within the next few business days.</p>
                    <br>
                    <p>Best regards,<br>The {{site_name}} Team</p>
                </div>
                ''',
                'description': 'Email sent when an order is shipped',
            },
            {
                'name': 'Order Delivered',
                'template_type': 'order_delivered',
                'subject': 'Your order has been delivered! - Order #{{order_number}}',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333; text-align: center;">Order Delivered!</h1>
                    <p>Hi {{user_name}},</p>
                    <p>Your order has been successfully delivered!</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Order Details</h3>
                        <p><strong>Order Number:</strong> {{order_number}}</p>
                        <p><strong>Delivered On:</strong> {{delivery_date|date:"F d, Y"}}</p>
                    </div>
                    
                    <p>We hope you love your purchase! If you have any issues with your order, please contact us.</p>
                    <p>Don't forget to leave a review for the products you purchased.</p>
                    <p>Thank you for shopping with us!</p>
                    <br>
                    <p>Best regards,<br>The {{site_name}} Team</p>
                </div>
                ''',
                'description': 'Email sent when an order is delivered',
            },
            {
                'name': 'Order Cancelled',
                'template_type': 'order_cancelled',
                'subject': 'Order Cancelled - Order #{{order_number}}',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #dc3545; text-align: center;">Order Cancelled</h1>
                    <p>Hi {{user_name}},</p>
                    <p>We're writing to inform you that your order has been cancelled.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Order Details</h3>
                        <p><strong>Order Number:</strong> {{order_number}}</p>
                        <p><strong>Order Total:</strong> ${{order_total}}</p>
                        <p><strong>Status:</strong> {{new_status}}</p>
                    </div>
                    
                    <p>If you paid for this order, a refund will be processed within 3-5 business days.</p>
                    <p>If you have any questions about this cancellation, please contact us.</p>
                    <br>
                    <p>Best regards,<br>The {{site_name}} Team</p>
                </div>
                ''',
                'description': 'Email sent when an order is cancelled',
            },
        ]

        for template_data in templates:
            template_type = template_data['template_type']
            
            if reset or not EmailTemplate.objects.filter(template_type=template_type).exists():
                if reset:
                    EmailTemplate.objects.filter(template_type=template_type).delete()
                
                template = EmailTemplate.objects.create(**template_data)
                self.stdout.write(f'Created email template: {template.name}')
            else:
                self.stdout.write(f'Template already exists: {template_data["name"]}')

        self.stdout.write('Email templates setup completed')