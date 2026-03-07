# -*- coding: utf-8 -*-
"""
خدمة المصادقة والجلسات
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from firebase_utils import create_user, get_user, db, FIREBASE_AVAILABLE
from functools import wraps
from flask import session, redirect, url_for, request

logger = logging.getLogger(__name__)

# ===================== إدارة الجلسات =====================

def create_session(user_id, email='', phone=''):
    """إنشاء جلسة جديدة"""
    try:
        session['user_id'] = str(user_id)
        session['email'] = email
        session['phone'] = phone
        session['created_at'] = datetime.now().isoformat()
        session.permanent = True
        
        logger.info(f"✅ جلسة جديدة: {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء جلسة: {e}")
        return False

def get_session_user():
    """جلب المستخدم من الجلسة"""
    try:
        user_id = session.get('user_id')
        if user_id:
            return get_user(user_id)
        return None
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return None

def destroy_session():
    """إزالة الجلسة"""
    try:
        session.clear()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return False

# ===================== فاحصات المصادقة =====================

def require_login(f):
    """ديكوريتور: يتطلب تسجيل دخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """ديكوريتور: يتطلب مسؤول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = get_session_user()
        if not user or not user.get('is_admin', False):
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# ===================== OTP والتحقق =====================

class OTPManager:
    """مدير كود التحقق OTP"""
    
    # تخزين مؤقت في الذاكرة (يجب استبداله بـ Redis في الإنتاج)
    _otp_store = {}
    _max_attempts = 3
    _otp_validity = 300  # 5 دقائق
    
    @classmethod
    def generate_otp(cls, identifier):
        """توليد كود OTP"""
        try:
            otp = secrets.randbelow(1000000)
            otp_str = str(otp).zfill(6)
            
            cls._otp_store[identifier] = {
                'code': otp_str,
                'attempts': 0,
                'created_at': datetime.now(),
                'verified': False
            }
            
            logger.info(f"✅ OTP: {otp_str} للـ {identifier}")
            return otp_str
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return None
    
    @classmethod
    def verify_otp(cls, identifier, code):
        """التحقق من كود OTP"""
        try:
            if identifier not in cls._otp_store:
                return False, "كود انتهت صلاحيته"
            
            otp_data = cls._otp_store[identifier]
            
            # فحص الانتهاء الزمني
            if (datetime.now() - otp_data['created_at']).seconds > cls._otp_validity:
                del cls._otp_store[identifier]
                return False, "انتهت صلاحية الكود"
            
            # فحص عدد المحاولات
            if otp_data['attempts'] >= cls._max_attempts:
                del cls._otp_store[identifier]
                return False, "تجاوزت الحد الأقصى من المحاولات"
            
            # التحقق من الكود
            if str(code) == otp_data['code']:
                otp_data['verified'] = True
                return True, "تم التحقق بنجاح"
            
            otp_data['attempts'] += 1
            return False, f"كود خاطئ ({cls._max_attempts - otp_data['attempts']} محاولات متبقية)"
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False, str(e)
    
    @classmethod
    def is_verified(cls, identifier):
        """هل تم التحقق من الكود"""
        if identifier in cls._otp_store:
            return cls._otp_store[identifier].get('verified', False)
        return False
    
    @classmethod
    def mark_used(cls, identifier):
        """وضع علامة على OTP كمستخدم"""
        if identifier in cls._otp_store:
            del cls._otp_store[identifier]

print("✅ auth_service تم تحميله")
