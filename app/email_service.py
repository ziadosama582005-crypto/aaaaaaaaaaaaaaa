"""خدمة إرسال الإيميلات عبر SMTP"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from app.config import get_settings


def _send_email(to_email: str, subject: str, html: str, plain: str = "") -> bool:
    """دالة أساسية لإرسال إيميل — يرجع True إذا نجح"""
    settings = get_settings()

    if not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        return False

    from_name = settings.SMTP_FROM_NAME or "TR Store"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, settings.SMTP_EMAIL))
    msg["To"] = to_email
    msg.attach(MIMEText(plain or subject, "plain", "utf-8"))
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


def _email_wrapper(store_name: str, icon: str, title: str, body_html: str) -> str:
    """قالب HTML موحد لجميع الإيميلات"""
    return f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"></head>
    <body style="margin: 0; padding: 0; background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, sans-serif;">
        <div style="max-width: 500px; margin: 30px auto; background: white; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">متجر {store_name}</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">{title}</p>
            </div>
            <div style="padding: 40px 30px; text-align: center;">
                {body_html}
            </div>
            <div style="background: #f8f9fa; padding: 20px; text-align: center;">
                <p style="color: #888; font-size: 12px; margin: 0;">متجر {store_name} © 2024</p>
            </div>
        </div>
    </body>
    </html>
    """


# ──────────── 1. كود التحقق ────────────

def send_verification_email(to_email: str, code: str, store_name: str) -> bool:
    body = f"""
        <p style="color: #666; font-size: 16px; margin-bottom: 30px;">مرحباً! 👋<br>استخدم الرمز التالي لتسجيل الدخول:</p>
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; display: inline-block;">
            <span style="font-size: 36px; font-weight: bold; color: white; letter-spacing: 8px;">{code}</span>
        </div>
        <p style="color: #999; font-size: 14px; margin-top: 30px;">⏰ هذا الرمز صالح لمدة <strong>10 دقائق</strong> فقط</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #aaa; font-size: 12px;">⚠️ إذا لم تطلب هذا الرمز، تجاهل هذا الإيميل</p>
    """
    html = _email_wrapper(store_name, "🔐", "رمز التحقق الخاص بك", body)
    return _send_email(to_email, f"🔐 كود الدخول - {store_name}", html, f"رمز التحقق: {code}")


# ──────────── 2. إضافة نقاط ────────────

def send_points_added_email(to_email: str, store_name: str, amount: float, new_balance: float, note: str = None) -> bool:
    note_html = f'<p style="color: #888; font-size: 14px;">📝 {note}</p>' if note else ""
    body = f"""
        <p style="color: #666; font-size: 16px; margin-bottom: 20px;">🎉 تم إضافة نقاط لحسابك!</p>
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 25px; border-radius: 15px; display: inline-block; min-width: 200px;">
            <p style="color: rgba(255,255,255,0.9); margin: 0 0 5px 0; font-size: 14px;">النقاط المضافة</p>
            <span style="font-size: 36px; font-weight: bold; color: white;">+{amount:.0f}</span>
        </div>
        <div style="margin-top: 20px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <p style="color: #666; margin: 0; font-size: 16px;">رصيدك الحالي: <strong style="color: #11998e; font-size: 20px;">{new_balance:.0f} نقطة</strong></p>
        </div>
        {note_html}
    """
    html = _email_wrapper(store_name, "✅", "تم إضافة نقاط", body)
    return _send_email(to_email, f"✅ +{amount:.0f} نقطة - {store_name}", html, f"تم إضافة {amount:.0f} نقطة. رصيدك: {new_balance:.0f}")


# ──────────── 3. خصم نقاط ────────────

def send_points_deducted_email(to_email: str, store_name: str, amount: float, new_balance: float, note: str = None) -> bool:
    note_html = f'<p style="color: #888; font-size: 14px;">📝 {note}</p>' if note else ""
    body = f"""
        <p style="color: #666; font-size: 16px; margin-bottom: 20px;">تم خصم نقاط من حسابك</p>
        <div style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); padding: 25px; border-radius: 15px; display: inline-block; min-width: 200px;">
            <p style="color: rgba(255,255,255,0.9); margin: 0 0 5px 0; font-size: 14px;">النقاط المخصومة</p>
            <span style="font-size: 36px; font-weight: bold; color: white;">-{amount:.0f}</span>
        </div>
        <div style="margin-top: 20px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <p style="color: #666; margin: 0; font-size: 16px;">رصيدك الحالي: <strong style="color: #eb3349; font-size: 20px;">{new_balance:.0f} نقطة</strong></p>
        </div>
        {note_html}
    """
    html = _email_wrapper(store_name, "❌", "تم خصم نقاط", body)
    return _send_email(to_email, f"❌ -{amount:.0f} نقطة - {store_name}", html, f"تم خصم {amount:.0f} نقطة. رصيدك: {new_balance:.0f}")


# ──────────── 4. استبدال ناجح ────────────

def send_redemption_email(to_email: str, store_name: str, product_name: str, points_spent: float, new_balance: float) -> bool:
    body = f"""
        <p style="color: #666; font-size: 16px; margin-bottom: 20px;">🎁 تم استبدال منتج بنجاح!</p>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 15px; text-align: right;">
            <p style="color: #333; margin: 8px 0; font-size: 15px;">📦 المنتج: <strong>{product_name}</strong></p>
            <p style="color: #333; margin: 8px 0; font-size: 15px;">💎 النقاط المستخدمة: <strong style="color: #eb3349;">{points_spent:.0f}</strong></p>
            <p style="color: #333; margin: 8px 0; font-size: 15px;">💰 الرصيد المتبقي: <strong style="color: #11998e;">{new_balance:.0f}</strong></p>
        </div>
        <div style="margin-top: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px;">
            <p style="color: white; margin: 0; font-size: 14px;">⏳ طلبك قيد المراجعة - سنبلغك عند الموافقة</p>
        </div>
    """
    html = _email_wrapper(store_name, "🎁", "تم الاستبدال بنجاح", body)
    return _send_email(to_email, f"🎁 تم استبدال {product_name} - {store_name}", html, f"تم استبدال {product_name} بـ {points_spent:.0f} نقطة")


# ──────────── 5. رفض الاستبدال ────────────

def send_redemption_rejected_email(to_email: str, store_name: str, product_name: str, points_returned: float, new_balance: float) -> bool:
    body = f"""
        <p style="color: #666; font-size: 16px; margin-bottom: 20px;">تم رفض طلب الاستبدال</p>
        <div style="background: #fff3f3; padding: 20px; border-radius: 15px; border: 1px solid #ffcdd2; text-align: right;">
            <p style="color: #333; margin: 8px 0; font-size: 15px;">📦 المنتج: <strong>{product_name}</strong></p>
            <p style="color: #333; margin: 8px 0; font-size: 15px;">🔄 تم إرجاع: <strong style="color: #11998e;">+{points_returned:.0f} نقطة</strong></p>
        </div>
        <div style="margin-top: 20px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <p style="color: #666; margin: 0; font-size: 16px;">رصيدك الحالي: <strong style="color: #11998e; font-size: 20px;">{new_balance:.0f} نقطة</strong></p>
        </div>
        <p style="color: #999; font-size: 13px; margin-top: 15px;">يمكنك استبدال نقاطك بمنتجات أخرى من المتجر</p>
    """
    html = _email_wrapper(store_name, "❌", "تم رفض طلب الاستبدال", body)
    return _send_email(to_email, f"❌ تم رفض طلب {product_name} - {store_name}", html, f"تم رفض استبدال {product_name} وإرجاع {points_returned:.0f} نقطة")
