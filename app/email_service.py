"""خدمة إرسال الإيميلات عبر SMTP"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings


def send_verification_email(to_email: str, code: str, store_name: str) -> bool:
    """إرسال كود التحقق عبر الإيميل — يرجع True إذا نجح"""
    settings = get_settings()

    if not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        return False

    subject = f"🔐 كود الدخول - {store_name}"
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"></head>
    <body style="margin: 0; padding: 0; background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, sans-serif;">
        <div style="max-width: 500px; margin: 30px auto; background: white; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🔐 {store_name}</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">رمز التحقق الخاص بك</p>
            </div>
            <div style="padding: 40px 30px; text-align: center;">
                <p style="color: #666; font-size: 16px; margin-bottom: 30px;">مرحباً! 👋<br>استخدم الرمز التالي لتسجيل الدخول:</p>
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; display: inline-block;">
                    <span style="font-size: 36px; font-weight: bold; color: white; letter-spacing: 8px;">{code}</span>
                </div>
                <p style="color: #999; font-size: 14px; margin-top: 30px;">⏰ هذا الرمز صالح لمدة <strong>10 دقائق</strong> فقط</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #aaa; font-size: 12px;">⚠️ إذا لم تطلب هذا الرمز، تجاهل هذا الإيميل</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; text-align: center;">
                <p style="color: #888; font-size: 12px; margin: 0;">{store_name} © 2024</p>
            </div>
        </div>
    </body>
    </html>
    """

    from_name = settings.SMTP_FROM_NAME or store_name
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{settings.SMTP_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(f"رمز التحقق: {code}", "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    print(f"📧 محاولة إرسال إيميل إلى: {to_email} عبر {settings.SMTP_SERVER}:{settings.SMTP_PORT}")

    # محاولة SSL أولاً (port 465)
    try:
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=15) as server:
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)
            print(f"✅ تم إرسال الإيميل بنجاح إلى: {to_email}")
            return True
    except Exception as ssl_error:
        print(f"⚠️ فشل SSL: {ssl_error}, جاري تجربة TLS...")

    # محاولة TLS كخيار ثاني (port 587)
    try:
        with smtplib.SMTP(settings.SMTP_SERVER, 587, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)
            print(f"✅ تم إرسال الإيميل بنجاح (TLS) إلى: {to_email}")
            return True
    except Exception as tls_error:
        print(f"❌ فشل TLS أيضاً: {tls_error}")
        return False
