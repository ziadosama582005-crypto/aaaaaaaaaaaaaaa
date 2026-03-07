# -*- coding: utf-8 -*-
"""
خدمة البريد الإلكتروني (Email)
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class EmailService:
    """خدمة إرسال البريد الإلكتروني"""
    
    # إعدادات SMTP
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'mail.privateemail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 465))
    SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'TR Store')
    
    @classmethod
    def is_configured(cls):
        """التحقق من إعداد الخدمة"""
        return bool(cls.SMTP_EMAIL and cls.SMTP_PASSWORD)
    
    @classmethod
    def send_email(cls, to_email, subject, html_body, text_body=None):
        """إرسال بريد إلكتروني"""
        try:
            if not cls.is_configured():
                logger.warning("⚠️ خدمة البريد غير مُعدّة")
                return False
            
            # إنشاء الرسالة
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{cls.SMTP_FROM_NAME} <{cls.SMTP_EMAIL}>"
            msg['To'] = to_email
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # النسخة النصية (fallback)
            if text_body:
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            
            # النسخة HTML
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # الاتصال والإرسال
            with smtplib.SMTP_SSL(cls.SMTP_SERVER, cls.SMTP_PORT, timeout=10) as server:
                server.login(cls.SMTP_EMAIL, cls.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ تم إرسال بريد إلى {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال البريد: {e}")
            return False
    
    @classmethod
    def send_otp_email(cls, to_email, otp_code, identifier):
        """إرسال كود OTP عبر البريد"""
        try:
            html_body = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: 'Tajawal', sans-serif;
                        background: #f5f5f5;
                        color: #333;
                    }}
                    .container {{
                        max-width: 500px;
                        margin: 40px auto;
                        background: white;
                        border-radius: 12px;
                        padding: 40px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .logo {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #6c5ce7;
                        margin-bottom: 10px;
                    }}
                    .title {{
                        font-size: 24px;
                        color: #333;
                        margin: 0;
                    }}
                    .otp-box {{
                        background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
                        border-radius: 12px;
                        padding: 30px;
                        text-align: center;
                        margin: 30px 0;
                    }}
                    .otp-label {{
                        color: rgba(255,255,255,0.9);
                        font-size: 14px;
                        margin-bottom: 10px;
                    }}
                    .otp-code {{
                        font-size: 48px;
                        font-weight: bold;
                        color: white;
                        letter-spacing: 8px;
                        font-family: 'Courier New', monospace;
                    }}
                    .instructions {{
                        background: #f9f9f9;
                        border-right: 4px solid #6c5ce7;
                        padding: 15px;
                        border-radius: 4px;
                        margin: 20px 0;
                        font-size: 14px;
                        line-height: 1.8;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                        font-size: 12px;
                        color: #999;
                    }}
                    .warning {{
                        color: #e74c3c;
                        font-weight: bold;
                        margin-top: 20px;
                        font-size: 13px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🏪 TR Store</div>
                        <p class="title">كود التحقق الخاص بك</p>
                    </div>
                    
                    <p style="text-align: center; color: #666; font-size: 16px; margin: 20px 0;">
                        مرحباً بك! 👋<br>
                        لقد طلبت تسجيل دخول باستخدام:
                    </p>
                    
                    <p style="text-align: center; font-size: 16px; color: #333; font-weight: bold;">
                        {identifier}
                    </p>
                    
                    <div class="otp-box">
                        <div class="otp-label">كود التحقق</div>
                        <div class="otp-code">{otp_code}</div>
                    </div>
                    
                    <div class="instructions">
                        📌 <strong>تعليمات:</strong><br>
                        • انسخ الكود أعلاه<br>
                        • الصقه في صفحة التحقق<br>
                        • الكود صالح لمدة 5 دقائق فقط<br>
                        • لا تشارك هذا الكود مع أحد
                    </div>
                    
                    <div class="warning">
                        ⚠️ إذا لم تطلب هذا الكود، تجاهل هذا البريد
                    </div>
                    
                    <div class="footer">
                        <p>© 2026 TR Store جميع الحقوق محفوظة</p>
                        <p>هذا البريد الإلكتروني تم إرساله تلقائياً، يرجى عدم الرد عليه</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            كود التحقق الخاص بك: {otp_code}
            
            هذا الكود صالح لمدة 5 دقائق فقط.
            لا تشارك هذا الكود مع أحد.
            
            © 2026 TR Store
            """
            
            return cls.send_email(
                to_email,
                "كود التحقق الخاص بك - TR Store",
                html_body,
                text_body
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False
    
    @classmethod
    def send_order_confirmation(cls, to_email, order_id, items, total_amount):
        """إرسال تأكيد الطلب"""
        try:
            items_html = ""
            for item in items:
                items_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        {item.get('name', 'منتج')}
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">
                        {item.get('quantity', 1)}
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: left;">
                        {item.get('price', 0)} ر.س
                    </td>
                </tr>
                """
            
            html_body = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Tajawal', sans-serif; background: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; padding: 30px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .order-id {{ background: #6c5ce7; color: white; padding: 15px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    .total {{ text-align: left; font-size: 18px; font-weight: bold; color: #6c5ce7; padding: 15px 0; border-top: 2px solid #6c5ce7; }}
                    .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2 style="margin: 0; color: #333;">✅ تأكيد الطلب</h2>
                    </div>
                    
                    <div class="order-id">
                        رقم الطلب: #{order_id}
                    </div>
                    
                    <h3 style="color: #333; margin-top: 30px;">منتجات الطلب:</h3>
                    
                    <table>
                        <thead style="background: #f9f9f9;">
                            <tr>
                                <th style="padding: 10px; text-align: right;">المنتج</th>
                                <th style="padding: 10px; text-align: center;">الكمية</th>
                                <th style="padding: 10px; text-align: left;">السعر</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div class="total">
                        الإجمالي: {total_amount} ر.س
                    </div>
                    
                    <p style="text-align: center; color: #666; margin: 30px 0;">
                        شكراً لتسوقك معنا! 🎉<br>
                        سيتم معالجة طلبك قريباً.
                    </p>
                    
                    <div class="footer">
                        <p>© 2026 TR Store</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return cls.send_email(
                to_email,
                f"تأكيد الطلب #{order_id} - TR Store",
                html_body
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False
    
    @classmethod
    def send_welcome_email(cls, to_email, user_name):
        """إرسال رسالة ترحيب"""
        try:
            html_body = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Tajawal', sans-serif; background: #f5f5f5; }}
                    .container {{ max-width: 500px; margin: 40px auto; background: white; border-radius: 12px; padding: 40px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ font-size: 36px; font-weight: bold; color: #6c5ce7; }}
                    .features {{ background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .feature {{ display: flex; align-items: center; margin: 10px 0; }}
                    .feature-icon {{ font-size: 20px; margin-left: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🏪 TR Store</div>
                        <h2 style="color: #333; margin-top: 20px;">أهلاً وسهلاً {user_name}! 👋</h2>
                    </div>
                    
                    <p style="color: #666; font-size: 16px; line-height: 1.8;">
                        نرحب بك في TR Store، أفضل متجر لمنتجاتك المفضلة!
                    </p>
                    
                    <div class="features">
                        <div class="feature">
                            <span class="feature-icon">🛍️</span>
                            <div>
                                <strong>تسوق سهل وآمن</strong><br>
                                <small style="color: #999;">اختر منتجاتك من قائمة واسعة</small>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <span class="feature-icon">💳</span>
                            <div>
                                <strong>طرق دفع متعددة</strong><br>
                                <small style="color: #999;">محفظة أو بطاقة ائتمان</small>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <span class="feature-icon">📦</span>
                            <div>
                                <strong>توصيل سريع</strong><br>
                                <small style="color: #999;">احصل على طلبك بسرعة</small>
                            </div>
                        </div>
                    </div>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="https://your-store.com" style="background: #6c5ce7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">
                            ابدأ التسوق الآن
                        </a>
                    </p>
                </div>
            </body>
            </html>
            """
            
            return cls.send_email(
                to_email,
                "مرحباً بك في TR Store! 🎉",
                html_body
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False

print("✅ email_service تم تحميله")
