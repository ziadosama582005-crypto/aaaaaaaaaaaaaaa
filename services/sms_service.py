# -*- coding: utf-8 -*-
"""
خدمة الرسائل النصية (SMS)
يدعم: Twilio, AWS SNS, أو Authentica
"""

import logging
import os
import requests

logger = logging.getLogger(__name__)

class SMSService:
    """خدمة إرسال الرسائل النصية"""
    
    # المزود المستخدم
    PROVIDER = os.getenv('SMS_PROVIDER', 'twilio')  # twilio, aws, authentica
    
    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE = os.getenv('TWILIO_PHONE', '')
    
    # Authentica
    AUTHENTICA_API_KEY = os.getenv('AUTHENTICA_API_KEY', '')
    AUTHENTICA_URL = 'https://api.authentica.com/send'
    
    @classmethod
    def is_configured(cls):
        """التحقق من إعداد الخدمة"""
        if cls.PROVIDER == 'twilio':
            return bool(cls.TWILIO_ACCOUNT_SID and cls.TWILIO_AUTH_TOKEN)
        elif cls.PROVIDER == 'authentica':
            return bool(cls.AUTHENTICA_API_KEY)
        return False
    
    @classmethod
    def send_sms(cls, phone_number, message):
        """إرسال رسالة نصية"""
        try:
            if not cls.is_configured():
                logger.warning("⚠️ خدمة SMS غير مُعدّة")
                return False
            
            if cls.PROVIDER == 'twilio':
                return cls._send_via_twilio(phone_number, message)
            elif cls.PROVIDER == 'authentica':
                return cls._send_via_authentica(phone_number, message)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال SMS: {e}")
            return False
    
    @classmethod
    def _send_via_twilio(cls, phone_number, message):
        """إرسال عبر Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN)
            
            msg = client.messages.create(
                body=message,
                from_=cls.TWILIO_PHONE,
                to=phone_number
            )
            
            logger.info(f"✅ SMS أرسل: {msg.sid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ Twilio: {e}")
            return False
    
    @classmethod
    def _send_via_authentica(cls, phone_number, message):
        """إرسال عبر Authentica"""
        try:
            headers = {
                'Authorization': f'Bearer {cls.AUTHENTICA_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'phone': phone_number,
                'message': message,
                'sender_id': 'TR-Store'
            }
            
            response = requests.post(cls.AUTHENTICA_URL, json=data, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ SMS أرسل إلى {phone_number}")
                return True
            else:
                logger.error(f"❌ Authentica: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False
    
    @classmethod
    def send_otp_sms(cls, phone_number, otp_code):
        """إرسال OTP عبر SMS"""
        message = f"كود التحقق الخاص بك: {otp_code}\nصالح لمدة 5 دقائق فقط"
        return cls.send_sms(phone_number, message)
    
    @classmethod
    def send_order_notification(cls, phone_number, order_id, total_amount):
        """إرسال إشعار الطلب"""
        message = f"✅ تم استقبال طلبك #{order_id}\nالإجمالي: {total_amount} ر.س\nشكراً لتسوقك معنا! 🎉"
        return cls.send_sms(phone_number, message)
    
    @classmethod
    def send_payment_confirmation(cls, phone_number, order_id, amount):
        """إرسال تأكيد الدفع"""
        message = f"💳 تم الدفع بنجاح\nالطلب: #{order_id}\nالمبلغ: {amount} ر.س"
        return cls.send_sms(phone_number, message)

print("✅ sms_service تم تحميله")
