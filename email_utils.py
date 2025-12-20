import os
from textwrap import dedent
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app

def _send_email(recipient: str, subject: str, html_body: str, text_body: str = None):
    """Send a multipart HTML email via Gmail SMTP using app password.
    
    Requires env vars: GMAIL_EMAIL, GMAIL_APP_PASSWORD.
    """
    sender = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not sender or not password:
        current_app.logger.error("Gmail credentials not configured in env.")
        return
    
    # Create multipart message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    
    # Add HTML body
    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)
    
    # Add plain text fallback if provided
    if text_body:
        text_part = MIMEText(text_body, "plain")
        msg.attach(text_part)
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        current_app.logger.info(f"Sent HTML email to {recipient}: {subject}")
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {recipient}: {e}")

def send_order_confirmation_email(order):
    """Send beautifully formatted HTML order confirmation email."""
    
    # Plain text fallback
    text_body = dedent(f"""Hi {order.customer_name},

Thank you for your order at Café Fusion!

Order ID: {order.id}
Status: {order.status}
Total: ₹{order.total_cents / 100:.2f}

Items:
""")
    for item in order.items:
        text_body += f"- {item.quantity} × {item.menu_item.name} = ₹{item.line_total_cents / 100:.2f}\n"
    
    text_body += dedent("""We'll notify you when your order is ready.

Thanks,
Café Fusion Team""")
    
    # Status configurations for email display
    status_info = {
        'pending': {'emoji': '⏳', 'action': 'received', 'next': 'being prepared'},
        'confirmed': {'emoji': '✅', 'action': 'confirmed', 'next': 'being prepared'},
        'preparing': {'emoji': '👨‍🍳', 'action': 'is being prepared', 'next': 'ready soon'},
        'ready': {'emoji': '✅', 'action': 'is ready for pickup', 'next': 'to be picked up'},
        'completed': {'emoji': '🎉', 'action': 'has been completed', 'next': 'thank you for your order'},
        'cancelled': {'emoji': '❌', 'action': 'has been cancelled', 'next': 'contact us if you have any questions'}
    }
    status = status_info.get(order.status.lower(), {'emoji': 'ℹ️', 'action': order.status, 'next': ''})

    # HTML body with inline styles for maximum compatibility
    items_html = ""
    for item in order.items:
        items_html += dedent(f"""    <tr>
        <td style="padding: 8px 12px; border-bottom: 1px solid #eee; text-align: left;">{item.menu_item.name}</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #eee; text-align: center;">{item.quantity}</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #eee; text-align: right;">₹{item.line_total_cents / 100:.2f}</td>
    </tr>""")
    
    html_body = dedent(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Café Fusion Order #{order.id}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8f9fa; color: #333;">
    <table role="presentation" style="width: 100%; max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <!-- Header -->
        <tr>
            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{status['emoji']} Order {status['action'].title()}</h1>
                <p style="margin: 8px 0 0 0; font-size: 16px; color: rgba(255,255,255,0.9);">Order #{order.id}</p>
            </td>
        </tr>
        
        <!-- Content -->
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="margin: 0 0 20px 0; font-size: 24px; font-weight: 600; color: #2d3748;">Hello {order.customer_name},</h2>
                
                <p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.6; color: #4a5568;">
                    Thank you for choosing <strong style="color: #667eea;">Café Fusion</strong>! 
                    Your order {status['action']} and will be {status['next']}.
                </p>
                
                <!-- Order Summary Card -->
                <table role="presentation" style="width: 100%; background: #f8f9fa; border-radius: 8px; padding: 24px; margin: 0 0 30px 0; border: 1px solid #e2e8f0;">
                    <tr>
                        <td style="padding: 0 0 16px 0;">
                            <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #2d3748;">Order Summary</h3>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <table role="presentation" style="width: 100%; font-size: 15px;">
                                <tr>
                                    <td style="padding: 12px 0; font-weight: 600; color: #4a5568;">Status:</td>
                                    <td style="padding: 12px 0; text-align: right;"><span style="background: #48bb78; color: white; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 500;">{order.status.title()}</span></td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; font-weight: 600; color: #4a5568;">Order Date:</td>
                                    <td style="padding: 12px 0; text-align: right; font-weight: 600;">{order.created_at.strftime('%d %b %Y, %I:%M %p')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0 0 0; font-weight: 600; color: #4a5568;">Total:</td>
                                    <td style="padding: 12px 0 0 0; text-align: right; font-size: 20px; font-weight: 700; color: #2f855a;">₹{order.total_cents / 100:.2f}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
                
                <!-- Items Table -->
                <h3 style="margin: 0 0 20px 0; font-size: 18px; font-weight: 600; color: #2d3748;">Your Order Items</h3>
                <table role="presentation" style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                    <thead>
                        <tr style="background: #edf2f7;">
                            <th style="padding: 16px 12px; text-align: left; font-weight: 600; color: #4a5568; font-size: 14px;">Item</th>
                            <th style="padding: 16px 12px; text-align: center; font-weight: 600; color: #4a5568; font-size: 14px;">Qty</th>
                            <th style="padding: 16px 12px; text-align: right; font-weight: 600; color: #4a5568; font-size: 14px;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
{items_html}                    </tbody>
                </table>
                
                <div style="margin: 30px 0 0 0; padding: 24px; background: #ebf8ff; border-radius: 8px; border-left: 4px solid #4299e1;">
                    <p style="margin: 0 0 12px 0; font-size: 15px; font-weight: 500; color: #2d3748;">
                        📱 Track your order or contact us
                    </p>
                    <p style="margin: 0; font-size: 14px; color: #4a5568; line-height: 1.5;">
                        We'll notify you via SMS when your order is ready for pickup. 
                        Need help? Reply to this email or call <strong>+91 12345 67890</strong>.
                    </p>
                </div>
            </td>
        </tr>
        
        <!-- Footer -->
        <tr>
            <td style="background: #2d3748; padding: 30px; text-align: center; color: #a0aec0; font-size: 14px;">
                <p style="margin: 0 0 8px 0; font-weight: 500;">Café Fusion ☕</p>
                <p style="margin: 0; opacity: 0.8;">Biratnagar, Koshi Province | Made with ❤️ for coffee lovers</p>
            </td>
        </tr>
    </table>
</body>
</html>""")
    
    if not order.customer_email:
        current_app.logger.warning(f"No email provided for order #{order.id}, cannot send confirmation")
        return
        
    recipient = order.customer_email
    status_emoji = status['emoji']
    subject = f"{status_emoji} Café Fusion Order #{order.id} {status['action'].title()}"
    
    _send_email(recipient, subject, html_body, text_body)

def send_welcome_email(user_email: str, name: str, role: str):
    """Send beautifully formatted HTML welcome email for new users/staff."""
    
    html_body = dedent(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8f9fa;">
    <table role="presentation" style="width: 100%; max-width: 600px; margin: 0 auto;">
        <tr>
            <td style="background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); padding: 50px 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 32px; font-weight: 700; color: white;">Welcome to Café Fusion! 🎉</h1>
            </td>
        </tr>
        <tr>
            <td style="background: white; padding: 50px 40px;">
                <h2 style="margin: 0 0 20px 0; font-size: 24px; color: #2d3748;">Hi {name},</h2>
                <p style="font-size: 18px; line-height: 1.6; color: #4a5568; margin: 0 0 30px 0;">
                    Your <strong style="color: #48bb78;">{role.title()}</strong> account has been created successfully!
                </p>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="{os.getenv('APP_URL', 'https://cafefusion.com')}/login" 
                       style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 40px; text-decoration: none; border-radius: 50px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);">
                        🚀 Get Started
                    </a>
                </div>
                
                <div style="background: #f0fff4; padding: 24px; border-radius: 8px; border-left: 4px solid #48bb78; margin: 30px 0;">
                    <p style="margin: 0 0 12px 0; font-weight: 500; color: #22543d;">Welcome to Café Fusion!</p>
                    <p style="margin: 0 0 12px 0; font-size: 15px; color: #4a5568; line-height: 1.6;">
                        We're excited to have you as part of our community. As a {role}, you can now:
                    </p>
                    <ul style="margin: 0; padding-left: 20px; font-size: 15px; color: #4a5568;">
                        <li>Place and track orders</li>
                        <li>View your order history</li>
                        <li>Receive exclusive offers</li>
                    </ul>
                </div>
            </td>
        </tr>
        <tr>
            <td style="background: #2d3748; padding: 30px; text-align: center; color: #a0aec0; font-size: 14px;">
                <p style="margin: 0;">Café Fusion ☕ | Biratnagar, Koshi Province</p>
            </td>
        </tr>
    </table>
</body>
</html>""")
    
    recipient = user_email
    subject = f"👋 Welcome to Café Fusion, {role.title()}!"
    
    _send_email(recipient, subject, html_body)
