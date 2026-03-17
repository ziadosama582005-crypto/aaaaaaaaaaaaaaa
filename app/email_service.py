"""
خدمة إرسال الإيميلات عبر SMTP (Gmail)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings


def send_verification_email(to_email: str, code: str, store_name: str) -> bool:
    """إرسال كود التحقق عبر الإيميل — يرجع True إذا نجح"""
    settings = get_settings()

    if not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        return False

    subject = f"كود التحقق - {store_name}"
    html = f"""
    <div dir="rtl" style="font-family:Arial,sans-serif;max-width:400px;margin:0 auto;padding:20px">
        <h2 style="color:#ffa502;text-align:center">🎁 {store_name}</h2>
        <p style="text-align:center;color:#333">كود التحقق الخاص بك:</p>
        <div style="text-align:center;margin:20px 0">
            <span style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#333;background:#f5f5f5;padding:15px 30px;border-radius:10px;display:inline-block">{code}</span>
        </div>
        <p style="text-align:center;color:#888;font-size:13px">صالح لمدة 10 دقائق</p>
        <p style="text-align:center;color:#aaa;font-size:11px;margin-top:20px">نظام نقاط الولاء</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"❌ فشل إرسال الإيميل: {e}")
        return False
