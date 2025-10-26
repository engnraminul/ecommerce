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
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Welcome</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #343a40; background-color: #f8f9fa; }
                        .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                        .header { background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 30px; text-align: center; }
                        .logo { font-size: 24px; font-weight: bold; margin-bottom: 8px; }
                        .content { padding: 30px; }
                        .welcome-box { background: #e3f2fd; border-left: 4px solid #007bff; padding: 20px; margin: 20px 0; border-radius: 5px; }
                        .feature { margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
                        .cta-button { display: inline-block; background: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 15px 0; }
                        .footer { background: #343a40; color: white; padding: 20px; text-align: center; font-size: 14px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">{{site_name}}</div>
                            <div>Welcome to our store!</div>
                        </div>
                        
                        <div class="content">
                            <h2 style="color: #007bff; margin-bottom: 15px;">Welcome {{user_name}}!</h2>
                            
                            <div class="welcome-box">
                                <p><strong>Your account has been created successfully!</strong> We're excited to have you as part of our community.</p>
                            </div>
                            
                            <p style="margin: 20px 0;">You can now enjoy these features:</p>
                            
                            <div class="feature">
                                <strong>Browse Products:</strong> Explore our curated collection
                            </div>
                            <div class="feature">
                                <strong>Track Orders:</strong> Monitor your purchases from order to delivery
                            </div>
                            <div class="feature">
                                <strong>Manage Account:</strong> Update your profile and preferences
                            </div>
                            <div class="feature">
                                <strong>Wishlist:</strong> Save your favorite items for later
                            </div>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{{site_url}}" class="cta-button">Start Shopping</a>
                            </div>
                            
                            <p style="margin: 20px 0; color: #6c757d;">If you have any questions, our support team is here to help!</p>
                        </div>
                        
                        <div class="footer">
                            <div style="margin-bottom: 10px;">
                                <strong>{{site_name}}</strong>
                            </div>
                            <div>
                                © {{current_year}} {{site_name}}. All rights reserved.<br>
                                Support: support@{{site_name|lower}}.com
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'description': 'Clean welcome email for new users',
            },
            {
                'name': 'Account Activation',
                'template_type': 'activation',
                'subject': 'Activate Your {{site_name}} Account - Just One Click Away! 🔐',
                'html_content': '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Activate Your Account</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #343a40; background-color: #f8f9fa; }
                        .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                        .header { background: linear-gradient(135deg, #17a2b8, #138496); color: white; padding: 40px 30px; text-align: center; }
                        .logo { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
                        .tagline { font-size: 14px; opacity: 0.9; }
                        .content { padding: 40px 30px; }
                        .activation-box { background: linear-gradient(135deg, #e3f2fd, #bbdefb); border-left: 5px solid #17a2b8; padding: 25px; margin: 25px 0; border-radius: 8px; text-align: center; }
                        .cta-button { display: inline-block; background: linear-gradient(135deg, #17a2b8, #138496); color: white; padding: 18px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 25px 0; box-shadow: 0 6px 16px rgba(23, 162, 184, 0.4); font-size: 16px; transition: all 0.3s ease; }
                        .cta-button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(23, 162, 184, 0.5); }
                        .security-info { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 25px 0; }
                        .security-icon { color: #ffc107; font-size: 24px; margin-bottom: 10px; }
                        .footer { background: #343a40; color: white; padding: 30px; text-align: center; }
                        .divider { height: 2px; background: linear-gradient(to right, #17a2b8, #007bff); margin: 30px 0; border-radius: 1px; }
                        .url-box { background: #f8f9fa; border: 2px dashed #17a2b8; padding: 15px; border-radius: 8px; margin: 20px 0; word-break: break-all; font-family: monospace; font-size: 14px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">{{site_name}}</div>
                            <div class="tagline">Account Activation Required</div>
                        </div>
                        
                        <div class="content">
                            <h1 style="color: #17a2b8; margin-bottom: 20px;">Almost There, {{user_name}}! 🔐</h1>
                            
                            <div class="activation-box">
                                <h2 style="color: #17a2b8; margin-bottom: 15px;">🎯 One Step Away from Shopping!</h2>
                                <p>Thank you for registering with {{site_name}}! To complete your account setup and start enjoying our premium shopping experience, please activate your account.</p>
                            </div>
                            
                            <p style="margin: 25px 0;">Click the button below to activate your account and unlock access to:</p>
                            
                            <ul style="margin: 20px 0; color: #6c757d; line-height: 2;">
                                <li>🛍️ <strong>Exclusive Products</strong> - Access to our full catalog</li>
                                <li>💰 <strong>Member Discounts</strong> - Special pricing for registered users</li>
                                <li>📦 <strong>Order Tracking</strong> - Real-time delivery updates</li>
                                <li>💝 <strong>Wishlist Feature</strong> - Save your favorite items</li>
                                <li>🎁 <strong>Loyalty Rewards</strong> - Earn points with every purchase</li>
                            </ul>
                            
                            <div style="text-align: center; margin: 35px 0;">
                                <a href="{{activation_url}}" class="cta-button">🚀 Activate My Account Now</a>
                            </div>
                            
                            <div class="divider"></div>
                            
                            <div class="security-info">
                                <div class="security-icon">🔒</div>
                                <h4 style="color: #856404; margin-bottom: 10px;">Security Information</h4>
                                <ul style="color: #856404; line-height: 1.8;">
                                    <li>This activation link is valid for <strong>7 days</strong> from registration</li>
                                    <li>The link can only be used once for security reasons</li>
                                    <li>If the link expires, you can request a new activation email</li>
                                </ul>
                            </div>
                            
                            <h4 style="color: #343a40; margin: 25px 0;">Having trouble with the button?</h4>
                            <p style="margin-bottom: 15px; color: #6c757d;">Copy and paste this link into your browser:</p>
                            <div class="url-box">{{activation_url}}</div>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                                <h4 style="color: #007bff; margin-bottom: 15px;">❓ Didn't register?</h4>
                                <p style="color: #6c757d;">If you didn't create an account with {{site_name}}, please ignore this email. Your information is safe and no account has been created.</p>
                            </div>
                            
                            <p style="margin: 25px 0; color: #6c757d;">Need help? Our support team is available 24/7 to assist you with account activation or any other questions.</p>
                        </div>
                        
                        <div class="footer">
                            <div style="margin-bottom: 20px;">
                                <strong>{{site_name}} Security Team</strong><br>
                                <span style="opacity: 0.8;">Keeping your account safe and secure</span>
                            </div>
                            
                            <div style="opacity: 0.8; font-size: 12px; margin-top: 20px;">
                                © {{current_year}} {{site_name}}. All rights reserved.<br>
                                This is an automated security email. Please do not reply to this message.<br>
                                Support: support@{{site_name|lower}}.com | Help Center: {{site_url}}/help
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'description': 'Professional activation email sent to users to activate their account',
            },
            {
                'name': 'Password Reset',
                'template_type': 'password_reset',
                'subject': 'Reset Your {{site_name}} Password - Secure & Easy 🔑',
                'html_content': '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Password Reset</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #343a40; background-color: #f8f9fa; }
                        .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                        .header { background: linear-gradient(135deg, #ffc107, #e0a800); color: #343a40; padding: 40px 30px; text-align: center; }
                        .logo { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
                        .tagline { font-size: 14px; opacity: 0.8; }
                        .content { padding: 40px 30px; }
                        .reset-box { background: linear-gradient(135deg, #fff8e1, #ffecb3); border-left: 5px solid #ffc107; padding: 25px; margin: 25px 0; border-radius: 8px; text-align: center; }
                        .cta-button { display: inline-block; background: linear-gradient(135deg, #ffc107, #e0a800); color: #343a40; padding: 18px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 25px 0; box-shadow: 0 6px 16px rgba(255, 193, 7, 0.4); font-size: 16px; transition: all 0.3s ease; }
                        .cta-button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(255, 193, 7, 0.5); }
                        .security-alert { background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 20px; margin: 25px 0; }
                        .security-tips { background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 8px; padding: 20px; margin: 25px 0; }
                        .footer { background: #343a40; color: white; padding: 30px; text-align: center; }
                        .divider { height: 2px; background: linear-gradient(to right, #ffc107, #dc3545); margin: 30px 0; border-radius: 1px; }
                        .url-box { background: #f8f9fa; border: 2px dashed #ffc107; padding: 15px; border-radius: 8px; margin: 20px 0; word-break: break-all; font-family: monospace; font-size: 14px; }
                        .timer-box { background: linear-gradient(135deg, #dc3545, #c82333); color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">{{site_name}}</div>
                            <div class="tagline">🔐 Password Reset Request</div>
                        </div>
                        
                        <div class="content">
                            <h1 style="color: #ffc107; margin-bottom: 20px;">Password Reset Requested 🔑</h1>
                            
                            <div class="reset-box">
                                <h2 style="color: #856404; margin-bottom: 15px;">🔒 Secure Password Reset</h2>
                                <p>Hi {{user_name}}, we received a request to reset the password for your {{site_name}} account. Don't worry - we'll get you back into your account quickly and securely!</p>
                            </div>
                            
                            <div class="timer-box">
                                <h3 style="margin-bottom: 10px;">⏰ Time Sensitive Request</h3>
                                <p style="margin: 0;">This password reset link will expire in <strong>24 hours</strong> for your security.</p>
                            </div>
                            
                            <p style="margin: 25px 0;">To create a new password, simply click the button below and follow the instructions:</p>
                            
                            <div style="text-align: center; margin: 35px 0;">
                                <a href="{{reset_url}}" class="cta-button">🔑 Reset My Password Now</a>
                            </div>
                            
                            <div class="divider"></div>
                            
                            <div class="security-tips">
                                <h4 style="color: #0c5460; margin-bottom: 15px;">💡 Password Security Tips</h4>
                                <ul style="color: #0c5460; line-height: 1.8;">
                                    <li>Use at least 8 characters with a mix of letters, numbers, and symbols</li>
                                    <li>Avoid using personal information like birthdays or names</li>
                                    <li>Don't reuse passwords from other accounts</li>
                                    <li>Consider using a password manager for stronger security</li>
                                </ul>
                            </div>
                            
                            <h4 style="color: #343a40; margin: 25px 0;">Can't click the button?</h4>
                            <p style="margin-bottom: 15px; color: #6c757d;">Copy and paste this link into your browser:</p>
                            <div class="url-box">{{reset_url}}</div>
                            
                            <div class="security-alert">
                                <h4 style="color: #721c24; margin-bottom: 15px;">⚠️ Security Notice</h4>
                                <ul style="color: #721c24; line-height: 1.8;">
                                    <li><strong>Didn't request this reset?</strong> Your account is still secure. Simply ignore this email and your password will remain unchanged.</li>
                                    <li><strong>Suspicious activity?</strong> Contact our support team immediately if you believe your account may be compromised.</li>
                                    <li><strong>Multiple requests?</strong> Only the most recent reset link will work - previous links are automatically disabled.</li>
                                </ul>
                            </div>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                                <h4 style="color: #007bff; margin-bottom: 15px;">🛡️ Account Security Information</h4>
                                <p style="color: #6c757d; margin-bottom: 15px;"><strong>Request Details:</strong></p>
                                <ul style="color: #6c757d; line-height: 1.6;">
                                    <li>Account: {{user_email}}</li>
                                    <li>Request Time: {{current_date}} at {{current_time}}</li>
                                    <li>User Agent: Web Browser</li>
                                    <li>Valid Until: {{expiry_date}} at {{expiry_time}}</li>
                                </ul>
                            </div>
                            
                            <p style="margin: 25px 0; color: #6c757d;">Need additional help? Our security team is available 24/7 to assist with account recovery and security questions.</p>
                        </div>
                        
                        <div class="footer">
                            <div style="margin-bottom: 20px;">
                                <strong>{{site_name}} Security Team</strong><br>
                                <span style="opacity: 0.8;">Protecting your account every step of the way</span>
                            </div>
                            
                            <div style="opacity: 0.8; font-size: 12px; margin-top: 20px;">
                                © {{current_year}} {{site_name}}. All rights reserved.<br>
                                This is an automated security email. Please do not reply to this message.<br>
                                Security Help: security@{{site_name|lower}}.com | Account Support: {{site_url}}/account-help
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'description': 'Professional password reset email with enhanced security information',
            },
            {
                'name': 'Order Confirmed',
                'template_type': 'order_confirmed',
                'subject': 'Order Confirmed! 🎉 Your {{site_name}} Order #{{order_number}}',
                'html_content': '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Order Confirmed</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #343a40; background-color: #f8f9fa; }
                        .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                        .header { background: linear-gradient(135deg, #28a745, #1e7e34); color: white; padding: 40px 30px; text-align: center; }
                        .logo { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
                        .tagline { font-size: 14px; opacity: 0.9; }
                        .content { padding: 40px 30px; }
                        .order-box { background: linear-gradient(135deg, #d4edda, #c3e6cb); border-left: 5px solid #28a745; padding: 25px; margin: 25px 0; border-radius: 8px; }
                        .order-details { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 25px; margin: 25px 0; }
                        .order-item { border-bottom: 1px solid #dee2e6; padding: 15px 0; display: flex; justify-content: space-between; align-items: center; }
                        .order-item:last-child { border-bottom: none; }
                        .item-info { flex: 1; }
                        .item-name { font-weight: bold; color: #343a40; margin-bottom: 5px; }
                        .item-details { color: #6c757d; font-size: 14px; }
                        .item-price { font-weight: bold; color: #28a745; font-size: 16px; }
                        .total-section { background: #343a40; color: white; padding: 20px; border-radius: 8px; margin: 25px 0; }
                        .total-row { display: flex; justify-content: space-between; margin: 10px 0; }
                        .total-final { border-top: 1px solid #6c757d; padding-top: 15px; margin-top: 15px; font-size: 18px; font-weight: bold; }
                        .shipping-info { background: #e7f3ff; border: 1px solid #b3d7ff; border-radius: 8px; padding: 20px; margin: 25px 0; }
                        .timeline { margin: 25px 0; }
                        .timeline-item { display: flex; align-items: center; margin: 15px 0; }
                        .timeline-icon { width: 30px; height: 30px; background: #28a745; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 14px; }
                        .timeline-pending { background: #6c757d; }
                        .cta-button { display: inline-block; background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 10px; box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3); }
                        .footer { background: #343a40; color: white; padding: 30px; text-align: center; }
                        .divider { height: 2px; background: linear-gradient(to right, #28a745, #007bff); margin: 30px 0; border-radius: 1px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">{{site_name}}</div>
                            <div class="tagline">Order Confirmation</div>
                        </div>
                        
                        <div class="content">
                            <h1 style="color: #28a745; margin-bottom: 20px;">Thank You for Your Order! 🎉</h1>
                            
                            <div class="order-box">
                                <h2 style="color: #155724; margin-bottom: 15px;">✅ Order Successfully Placed</h2>
                                <p>Hi {{user_name}}, your order has been received and is being processed. We'll send you updates as your order moves through our fulfillment process.</p>
                            </div>
                            
                            <div class="order-details">
                                <h3 style="color: #343a40; margin-bottom: 20px; border-bottom: 2px solid #28a745; padding-bottom: 10px;">📋 Order Details</h3>
                                
                                <div style="display: flex; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap;">
                                    <div style="margin-bottom: 10px;">
                                        <strong>Order Number:</strong><br>
                                        <span style="color: #007bff; font-weight: bold; font-size: 16px;">#{{order_number}}</span>
                                    </div>
                                    <div style="margin-bottom: 10px;">
                                        <strong>Order Date:</strong><br>
                                        <span>{{order_date|date:"F d, Y \a\\t h:i A"}}</span>
                                    </div>
                                    <div style="margin-bottom: 10px;">
                                        <strong>Payment Method:</strong><br>
                                        <span>{{payment_method|default:"Credit Card"}}</span>
                                    </div>
                                </div>
                                
                                <h4 style="color: #343a40; margin: 20px 0 15px 0;">🛍️ Items Ordered</h4>
                                
                                {% for item in order_items %}
                                <div class="order-item">
                                    <div class="item-info">
                                        <div class="item-name">{{item.product_name}}</div>
                                        <div class="item-details">
                                            Quantity: {{item.quantity}} | SKU: {{item.sku|default:"N/A"}}
                                            {% if item.variant %}| Variant: {{item.variant}}{% endif %}
                                        </div>
                                    </div>
                                    <div class="item-price">${{item.total_price}}</div>
                                </div>
                                {% empty %}
                                <div class="order-item">
                                    <div class="item-info">
                                        <div class="item-name">Sample Product</div>
                                        <div class="item-details">Quantity: 1 | SKU: SAMPLE001</div>
                                    </div>
                                    <div class="item-price">${{order_total}}</div>
                                </div>
                                {% endfor %}
                            </div>
                            
                            <div class="total-section">
                                <h4 style="margin-bottom: 15px;">💰 Order Summary</h4>
                                <div class="total-row">
                                    <span>Subtotal:</span>
                                    <span>${{order_subtotal|default:order_total}}</span>
                                </div>
                                <div class="total-row">
                                    <span>Shipping:</span>
                                    <span>${{shipping_cost|default:"Free"}}</span>
                                </div>
                                {% if tax_amount %}
                                <div class="total-row">
                                    <span>Tax:</span>
                                    <span>${{tax_amount}}</span>
                                </div>
                                {% endif %}
                                {% if discount_amount %}
                                <div class="total-row" style="color: #28a745;">
                                    <span>Discount:</span>
                                    <span>-${{discount_amount}}</span>
                                </div>
                                {% endif %}
                                <div class="total-row total-final">
                                    <span>Total:</span>
                                    <span>${{order_total}}</span>
                                </div>
                            </div>
                            
                            <div class="shipping-info">
                                <h4 style="color: #004085; margin-bottom: 15px;">🚚 Shipping Information</h4>
                                <div style="margin-bottom: 15px;">
                                    <strong>Shipping Address:</strong><br>
                                    {{shipping_name|default:user_full_name}}<br>
                                    {{shipping_address|default:"Address will be confirmed"}}<br>
                                    {{shipping_city|default:"City"}}, {{shipping_state|default:"State"}} {{shipping_zip|default:"ZIP"}}<br>
                                    {{shipping_country|default:"Country"}}
                                </div>
                                <div>
                                    <strong>Estimated Delivery:</strong> {{estimated_delivery|default:"3-5 business days"}}<br>
                                    <strong>Shipping Method:</strong> {{shipping_method|default:"Standard Shipping"}}
                                </div>
                            </div>
                            
                            <div class="divider"></div>
                            
                            <h4 style="color: #343a40; margin-bottom: 20px;">📈 What's Next?</h4>
                            
                            <div class="timeline">
                                <div class="timeline-item">
                                    <div class="timeline-icon">✓</div>
                                    <div>
                                        <strong>Order Received</strong><br>
                                        <span style="color: #6c757d;">We've received your order and payment</span>
                                    </div>
                                </div>
                                <div class="timeline-item">
                                    <div class="timeline-icon timeline-pending">2</div>
                                    <div>
                                        <strong>Processing</strong><br>
                                        <span style="color: #6c757d;">We're preparing your items for shipment</span>
                                    </div>
                                </div>
                                <div class="timeline-item">
                                    <div class="timeline-icon timeline-pending">3</div>
                                    <div>
                                        <strong>Shipped</strong><br>
                                        <span style="color: #6c757d;">Your order is on its way to you</span>
                                    </div>
                                </div>
                                <div class="timeline-item">
                                    <div class="timeline-icon timeline-pending">4</div>
                                    <div>
                                        <strong>Delivered</strong><br>
                                        <span style="color: #6c757d;">Your order has arrived!</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="text-align: center; margin: 35px 0;">
                                <a href="{{site_url}}/orders/{{order_number}}" class="cta-button">📦 Track Your Order</a>
                                <a href="{{site_url}}/account/orders" class="cta-button">📋 View All Orders</a>
                            </div>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                                <h4 style="color: #007bff; margin-bottom: 15px;">💡 Order Management Tips</h4>
                                <ul style="color: #6c757d; line-height: 1.8;">
                                    <li>Keep this email for your records and return reference</li>
                                    <li>You'll receive tracking information once your order ships</li>
                                    <li>Check your account dashboard for real-time order updates</li>
                                    <li>Contact us within 1 hour if you need to modify your order</li>
                                </ul>
                            </div>
                            
                            <p style="margin: 25px 0; color: #6c757d;">Questions about your order? Our customer service team is here to help! We typically process orders within 24 hours on business days.</p>
                        </div>
                        
                        <div class="footer">
                            <div style="margin-bottom: 20px;">
                                <strong>{{site_name}} Order Team</strong><br>
                                <span style="opacity: 0.8;">Thank you for choosing us for your shopping needs</span>
                            </div>
                            
                            <div style="opacity: 0.8; font-size: 12px; margin-top: 20px;">
                                © {{current_year}} {{site_name}}. All rights reserved.<br>
                                Order Support: orders@{{site_name|lower}}.com | Customer Service: {{site_url}}/support<br>
                                Return Policy: {{site_url}}/returns | Shipping Info: {{site_url}}/shipping
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'description': 'Professional order confirmation email with complete order details and tracking information',
            },
            {
                'name': 'Order Shipped',
                'template_type': 'order_shipped',
                'subject': 'Your Order Has Shipped - Order #{{order_number}}',
                'html_content': '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Order Shipped</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #343a40; background-color: #f8f9fa; }
                        .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                        .header { background: linear-gradient(135deg, #17a2b8, #138496); color: white; padding: 30px; text-align: center; }
                        .logo { font-size: 24px; font-weight: bold; margin-bottom: 8px; }
                        .content { padding: 30px; }
                        .shipped-box { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 20px; margin: 20px 0; border-radius: 5px; }
                        .tracking-section { background: #343a40; color: white; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; }
                        .tracking-number { background: #17a2b8; color: white; padding: 12px; border-radius: 5px; font-weight: bold; margin: 10px 0; font-size: 16px; }
                        .details-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                        .details-table td { padding: 10px; border-bottom: 1px solid #dee2e6; }
                        .details-table .label { font-weight: bold; color: #6c757d; width: 40%; }
                        .cta-button { display: inline-block; background: #17a2b8; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 10px 5px; }
                        .footer { background: #343a40; color: white; padding: 20px; text-align: center; font-size: 14px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">{{site_name}}</div>
                            <div>Your Order Has Shipped!</div>
                        </div>
                        
                        <div class="content">
                            <h2 style="color: #17a2b8; margin-bottom: 15px;">Great News {{user_name}}!</h2>
                            
                            <div class="shipped-box">
                                <p><strong>Your order has been shipped and is on its way to you.</strong></p>
                            </div>
                            
                            <div class="tracking-section">
                                <h3 style="margin-bottom: 10px;">Track Your Package</h3>
                                <p>Tracking Number:</p>
                                <div class="tracking-number">{{tracking_number}}</div>
                            </div>
                            
                            <h3 style="color: #343a40; margin: 25px 0 15px 0;">Shipping Details</h3>
                            <table class="details-table">
                                <tr>
                                    <td class="label">Order Number:</td>
                                    <td>#{{order_number}}</td>
                                </tr>
                                <tr>
                                    <td class="label">Carrier:</td>
                                    <td>{{carrier}}</td>
                                </tr>
                                <tr>
                                    <td class="label">Shipping Method:</td>
                                    <td>{{shipping_method}}</td>
                                </tr>
                                <tr>
                                    <td class="label">Estimated Delivery:</td>
                                    <td>{{estimated_delivery}}</td>
                                </tr>
                            </table>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{{tracking_url}}" class="cta-button">Track Package</a>
                                <a href="{{site_url}}/orders/{{order_number}}" class="cta-button">View Order</a>
                            </div>
                            
                            <p style="margin: 20px 0; color: #6c757d;">You can track your package using the tracking number above. Your order should arrive within the estimated delivery time.</p>
                            
                            <p style="margin: 20px 0; color: #6c757d;">If you have any questions about your shipment, please contact our support team.</p>
                        </div>
                        
                        <div class="footer">
                            <div style="margin-bottom: 10px;">
                                <strong>{{site_name}}</strong>
                            </div>
                            <div>
                                © {{current_year}} {{site_name}}. All rights reserved.<br>
                                Support: support@{{site_name|lower}}.com
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'description': 'Clean shipping notification email with essential tracking information',
            },
            {
                'name': 'Order Delivered',
                'template_type': 'order_delivered',
                'subject': 'Delivered! 🎊 Your {{site_name}} Order #{{order_number}} Has Arrived',
                'html_content': '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Order Delivered</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #343a40; background-color: #f8f9fa; }
                        .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                        .header { background: linear-gradient(135deg, #28a745, #1e7e34); color: white; padding: 40px 30px; text-align: center; }
                        .logo { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
                        .tagline { font-size: 14px; opacity: 0.9; }
                        .content { padding: 40px 30px; }
                        .delivered-box { background: linear-gradient(135deg, #d4edda, #c3e6cb); border-left: 5px solid #28a745; padding: 25px; margin: 25px 0; border-radius: 8px; text-align: center; }
                        .delivery-details { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 25px; margin: 25px 0; }
                        .detail-row { display: flex; justify-content: space-between; margin: 10px 0; padding: 10px 0; border-bottom: 1px solid #dee2e6; }
                        .detail-row:last-child { border-bottom: none; }
                        .detail-label { font-weight: bold; color: #6c757d; }
                        .detail-value { color: #343a40; }
                        .cta-button { display: inline-block; background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 10px; box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3); }
                        .review-section { background: #fff8e1; border: 1px solid #ffecb3; border-radius: 8px; padding: 25px; margin: 25px 0; text-align: center; }
                        .satisfaction-icons { font-size: 40px; margin: 20px 0; }
                        .support-section { background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 20px; margin: 25px 0; }
                        .footer { background: #343a40; color: white; padding: 30px; text-align: center; }
                        .divider { height: 2px; background: linear-gradient(to right, #28a745, #ffc107); margin: 30px 0; border-radius: 1px; }
                        .star-rating { color: #ffc107; font-size: 24px; margin: 10px 0; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">{{site_name}}</div>
                            <div class="tagline">🎊 Delivery Completed Successfully!</div>
                        </div>
                        
                        <div class="content">
                            <h1 style="color: #28a745; margin-bottom: 20px;">Your Order Has Been Delivered! 🎉</h1>
                            
                            <div class="delivered-box">
                                <h2 style="color: #155724; margin-bottom: 15px;">📦 Package Successfully Delivered</h2>
                                <p>Congratulations {{user_name}}! Your {{site_name}} order has been delivered safely. We hope you love your purchase!</p>
                                <div class="satisfaction-icons">📦➡️🏠✅</div>
                            </div>
                            
                            <div class="delivery-details">
                                <h3 style="color: #343a40; margin-bottom: 20px; border-bottom: 2px solid #28a745; padding-bottom: 10px;">📋 Delivery Confirmation</h3>
                                
                                <div class="detail-row">
                                    <span class="detail-label">Order Number:</span>
                                    <span class="detail-value">#{{order_number}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Delivered On:</span>
                                    <span class="detail-value">{{delivery_date|date:"F d, Y \a\\t h:i A"|default:"Today"}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Delivered To:</span>
                                    <span class="detail-value">{{delivery_location|default:"Front door"}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Received By:</span>
                                    <span class="detail-value">{{received_by|default:"Resident"}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Delivery Signature:</span>
                                    <span class="detail-value">{{signature_status|default:"Electronic confirmation"}}</span>
                                </div>
                                {% if delivery_photo %}
                                <div class="detail-row">
                                    <span class="detail-label">Delivery Photo:</span>
                                    <span class="detail-value"><a href="{{delivery_photo}}" style="color: #007bff;">View Photo</a></span>
                                </div>
                                {% endif %}
                            </div>
                            
                            <div style="text-align: center; margin: 35px 0;">
                                <a href="{{site_url}}/orders/{{order_number}}" class="cta-button">📋 View Order Details</a>
                                <a href="{{site_url}}/products" class="cta-button">🛍️ Continue Shopping</a>
                            </div>
                            
                            <div class="divider"></div>
                            
                            <div class="review-section">
                                <h3 style="color: #f57c00; margin-bottom: 20px;">⭐ Share Your Experience</h3>
                                <p style="margin-bottom: 20px;">Your opinion matters! Help other customers by reviewing your purchase.</p>
                                <div class="star-rating">⭐⭐⭐⭐⭐</div>
                                <p style="margin-bottom: 25px; color: #6c757d;">Rate your shopping experience and product quality</p>
                                <a href="{{site_url}}/orders/{{order_number}}/review" style="display: inline-block; background: linear-gradient(135deg, #ffc107, #e0a800); color: #343a40; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);">✍️ Write a Review</a>
                            </div>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                                <h4 style="color: #007bff; margin-bottom: 15px;">🎁 What's Next?</h4>
                                <ul style="color: #6c757d; line-height: 1.8;">
                                    <li><strong>Inspect your items:</strong> Check that everything arrived in perfect condition</li>
                                    <li><strong>Keep your receipt:</strong> Save this email for warranty and return purposes</li>
                                    <li><strong>Register products:</strong> Some items may require product registration for warranty</li>
                                    <li><strong>Share your joy:</strong> Tag us on social media with your unboxing experience!</li>
                                </ul>
                            </div>
                            
                            <div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 8px; padding: 20px; margin: 25px 0;">
                                <h4 style="color: #0c5460; margin-bottom: 15px;">💰 Earn Rewards</h4>
                                <p style="color: #0c5460; margin-bottom: 15px;">Great news! You've earned <strong>{{loyalty_points|default:"50"}} reward points</strong> with this purchase.</p>
                                <ul style="color: #0c5460; line-height: 1.6;">
                                    <li>Redeem points for discounts on future orders</li>
                                    <li>Refer friends to earn bonus points</li>
                                    <li>Check your rewards balance in your account</li>
                                </ul>
                            </div>
                            
                            <div class="support-section">
                                <h4 style="color: #004085; margin-bottom: 15px;">🤝 Need Support?</h4>
                                <div style="margin-bottom: 15px;">
                                    <strong>Having issues with your order?</strong><br>
                                    <span style="color: #004085;">We're here to help! Contact us within 30 days for:</span>
                                </div>
                                <ul style="color: #004085; line-height: 1.8;">
                                    <li>Product defects or damage</li>
                                    <li>Missing items or wrong products</li>
                                    <li>Return or exchange requests</li>
                                    <li>Warranty claims and support</li>
                                </ul>
                                <div style="margin-top: 15px;">
                                    <a href="{{site_url}}/support" style="color: #004085; text-decoration: none; font-weight: bold;">📞 Contact Support →</a>
                                </div>
                            </div>
                            
                            <p style="margin: 25px 0; color: #6c757d;">Thank you for choosing {{site_name}} for your shopping needs. We appreciate your business and look forward to serving you again soon!</p>
                        </div>
                        
                        <div class="footer">
                            <div style="margin-bottom: 20px;">
                                <strong>{{site_name}} Customer Success Team</strong><br>
                                <span style="opacity: 0.8;">Celebrating successful deliveries since day one</span>
                            </div>
                            
                            <div style="margin: 20px 0;">
                                <a href="#" style="color: white; text-decoration: none; margin: 0 10px;">📘 Facebook</a>
                                <a href="#" style="color: white; text-decoration: none; margin: 0 10px;">📷 Instagram</a>
                                <a href="#" style="color: white; text-decoration: none; margin: 0 10px;">🐦 Twitter</a>
                                <a href="#" style="color: white; text-decoration: none; margin: 0 10px;">📺 YouTube</a>
                            </div>
                            
                            <div style="opacity: 0.8; font-size: 12px; margin-top: 20px;">
                                © {{current_year}} {{site_name}}. All rights reserved.<br>
                                Customer Support: support@{{site_name|lower}}.com | Returns: {{site_url}}/returns<br>
                                Account Help: {{site_url}}/account | Product Reviews: {{site_url}}/reviews
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'description': 'Professional delivery confirmation with review prompts and next steps',
            },
            {
                'name': 'Order Cancelled',
                'template_type': 'order_cancelled',
                'subject': 'Order Cancelled - Refund Processing 💰 Order #{{order_number}}',
                'html_content': '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Order Cancelled</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #343a40; background-color: #f8f9fa; }
                        .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                        .header { background: linear-gradient(135deg, #dc3545, #c82333); color: white; padding: 40px 30px; text-align: center; }
                        .logo { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
                        .tagline { font-size: 14px; opacity: 0.9; }
                        .content { padding: 40px 30px; }
                        .cancelled-box { background: linear-gradient(135deg, #f8d7da, #f5c6cb); border-left: 5px solid #dc3545; padding: 25px; margin: 25px 0; border-radius: 8px; text-align: center; }
                        .order-details { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 25px; margin: 25px 0; }
                        .detail-row { display: flex; justify-content: space-between; margin: 10px 0; padding: 10px 0; border-bottom: 1px solid #dee2e6; }
                        .detail-row:last-child { border-bottom: none; }
                        .detail-label { font-weight: bold; color: #6c757d; }
                        .detail-value { color: #343a40; }
                        .refund-section { background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 25px; margin: 25px 0; }
                        .cta-button { display: inline-block; background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 10px; box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3); }
                        .reason-section { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 25px 0; }
                        .footer { background: #343a40; color: white; padding: 30px; text-align: center; }
                        .divider { height: 2px; background: linear-gradient(to right, #dc3545, #ffc107); margin: 30px 0; border-radius: 1px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">{{site_name}}</div>
                            <div class="tagline">Order Cancellation Notice</div>
                        </div>
                        
                        <div class="content">
                            <h1 style="color: #dc3545; margin-bottom: 20px;">Order Cancellation Confirmed</h1>
                            
                            <div class="cancelled-box">
                                <h2 style="color: #721c24; margin-bottom: 15px;">❌ Order Successfully Cancelled</h2>
                                <p>Hi {{user_name}}, we've processed your cancellation request for order #{{order_number}}. We're sorry to see this order cancelled, but we understand that circumstances change.</p>
                            </div>
                            
                            <div class="order-details">
                                <h3 style="color: #343a40; margin-bottom: 20px; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">📋 Cancelled Order Details</h3>
                                
                                <div class="detail-row">
                                    <span class="detail-label">Order Number:</span>
                                    <span class="detail-value">#{{order_number}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Original Order Date:</span>
                                    <span class="detail-value">{{order_date|date:"F d, Y \a\\t h:i A"}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Cancellation Date:</span>
                                    <span class="detail-value">{{cancellation_date|default:current_date}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Order Status:</span>
                                    <span class="detail-value" style="color: #dc3545; font-weight: bold;">{{new_status|default:"Cancelled"}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Order Total:</span>
                                    <span class="detail-value" style="font-weight: bold;">${{order_total}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Payment Method:</span>
                                    <span class="detail-value">{{payment_method|default:"Credit Card"}}</span>
                                </div>
                            </div>
                            
                            <div class="refund-section">
                                <h3 style="color: #155724; margin-bottom: 20px;">💰 Refund Information</h3>
                                <div style="margin-bottom: 20px;">
                                    <p style="color: #155724; margin-bottom: 15px;"><strong>Good News:</strong> Your refund is being processed automatically.</p>
                                    <ul style="color: #155724; line-height: 1.8;">
                                        <li><strong>Refund Amount:</strong> ${{refund_amount|default:order_total}}</li>
                                        <li><strong>Refund Method:</strong> Original payment method</li>
                                        <li><strong>Processing Time:</strong> 3-5 business days</li>
                                        <li><strong>Refund Reference:</strong> REF{{order_number}}{{current_year}}</li>
                                    </ul>
                                </div>
                                <div style="background: #d1ecf1; padding: 15px; border-radius: 6px;">
                                    <p style="color: #0c5460; margin: 0;"><strong>📅 Expected Refund Date:</strong> {{expected_refund_date|default:"Within 5 business days"}}</p>
                                </div>
                            </div>
                            
                            {% if cancellation_reason %}
                            <div class="reason-section">
                                <h4 style="color: #856404; margin-bottom: 15px;">📝 Cancellation Reason</h4>
                                <p style="color: #856404;">{{cancellation_reason}}</p>
                            </div>
                            {% endif %}
                            
                            <div style="text-align: center; margin: 35px 0;">
                                <a href="{{site_url}}/account/orders" class="cta-button">📋 View Order History</a>
                                <a href="{{site_url}}/products" class="cta-button">🛍️ Continue Shopping</a>
                            </div>
                            
                            <div class="divider"></div>
                            
                            <div style="background: #e7f3ff; border: 1px solid #b3d7ff; border-radius: 8px; padding: 20px; margin: 25px 0;">
                                <h4 style="color: #004085; margin-bottom: 15px;">🔄 What Happens Next?</h4>
                                <div style="margin-bottom: 15px;">
                                    <strong>Immediate Actions:</strong>
                                </div>
                                <ul style="color: #004085; line-height: 1.8;">
                                    <li>Your payment has been released and refund initiated</li>
                                    <li>Any shipping preparations have been stopped</li>
                                    <li>Reserved inventory has been returned to stock</li>
                                    <li>You'll receive email confirmation when refund is complete</li>
                                </ul>
                            </div>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                                <h4 style="color: #007bff; margin-bottom: 15px;">💡 For Future Orders</h4>
                                <ul style="color: #6c757d; line-height: 1.8;">
                                    <li><strong>Easy Reordering:</strong> Your cancelled items remain in your wishlist</li>
                                    <li><strong>Account Credit:</strong> Consider store credit for faster future checkout</li>
                                    <li><strong>Order Modification:</strong> Contact us early if you need to change orders</li>
                                    <li><strong>Customer Support:</strong> We're here to help with any questions</li>
                                </ul>
                            </div>
                            
                            <div style="background: #fff8e1; border: 1px solid #ffecb3; border-radius: 8px; padding: 20px; margin: 25px 0;">
                                <h4 style="color: #f57c00; margin-bottom: 15px;">🎁 We'd Love to Have You Back</h4>
                                <p style="color: #f57c00; margin-bottom: 15px;">While we're sorry this order didn't work out, we'd love another chance to serve you:</p>
                                <ul style="color: #f57c00; line-height: 1.8;">
                                    <li>Check out our new arrivals and featured products</li>
                                    <li>Subscribe to our newsletter for exclusive deals</li>
                                    <li>Follow us on social media for product updates</li>
                                    <li>Contact us if you need help finding the right product</li>
                                </ul>
                            </div>
                            
                            <p style="margin: 25px 0; color: #6c757d;">Have questions about your cancellation or refund? Our customer service team is available 24/7 to assist you with any concerns.</p>
                            
                            <p style="margin: 25px 0; color: #6c757d;">Thank you for giving {{site_name}} a try. We hope to serve you again in the future!</p>
                        </div>
                        
                        <div class="footer">
                            <div style="margin-bottom: 20px;">
                                <strong>{{site_name}} Customer Service</strong><br>
                                <span style="opacity: 0.8;">Always here to help, even with cancellations</span>
                            </div>
                            
                            <div style="opacity: 0.8; font-size: 12px; margin-top: 20px;">
                                © {{current_year}} {{site_name}}. All rights reserved.<br>
                                Refund Support: refunds@{{site_name|lower}}.com | Customer Service: {{site_url}}/support<br>
                                Order Help: {{site_url}}/order-help | Return Policy: {{site_url}}/returns
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'description': 'Professional order cancellation email with refund information and next steps',
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