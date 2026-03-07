# -*- coding: utf-8 -*-
"""
الإعدادات الرئيسية للتطبيق
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# بيئة التطوير
DEBUG = os.getenv('DEBUG', 'False') == 'True'
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# السرية والأمان
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')

# إعدادات الجلسة
PERMANENT_SESSION_LIFETIME = timedelta(days=30)
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'tr_session')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
SESSION_TYPE = 'filesystem'

# Firebase
FIREBASE_CONFIG_PATH = os.getenv('FIREBASE_CONFIG_PATH', './serviceAccountKey.json')

# API Keys والدفع
PAYMENT_API_KEY = os.getenv('PAYMENT_API_KEY', '')
PAYMENT_GATEWAY_URL = os.getenv('PAYMENT_GATEWAY_URL', 'https://api.edfapay.com/payment')
PAYMENT_GATEWAY_SECRET = os.getenv('PAYMENT_GATEWAY_SECRET', '')
PAYMENT_CALLBACK_URL = os.getenv('PAYMENT_CALLBACK_URL', 'http://localhost:5000/api/payment/gateway/callback')

# إعدادات الدفع
PAYMENT_METHODS = ['wallet', 'card', 'transfer']
PAYMENT_GATEWAY_FEE = 2.5  # نسبة الرسوم

# تحديدات المعاملات
MIN_WITHDRAWAL = 50.0
MAX_WITHDRAWAL = 10000.0
WITHDRAWAL_FEE_PERCENT = 2.5

# Email و SMS (لاحقاً)
SMTP_SERVER = os.getenv('SMTP_SERVER', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', 465))
SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

# ملخص الموقع
SITE_NAME = 'TR Store'
SITE_DESCRIPTION = 'متجر رقمي متكامل'
SITE_URL = os.getenv('SITE_URL', 'http://localhost:5000')

# الأدمن
ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',') if os.getenv('ADMIN_IDS') else []

print("✅ الإعدادات تم تحميلها بنجاح")
