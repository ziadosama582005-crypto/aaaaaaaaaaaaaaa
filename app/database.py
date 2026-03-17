"""
اتصال Firestore - تهيئة Firebase وإنشاء عميل Firestore
"""

import os
import json
import base64
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import get_settings

settings = get_settings()

db = None  # Firestore client


def init_firebase():
    """تهيئة Firebase - يدعم Base64 (Render) أو ملف محلي"""
    global db

    if firebase_admin._apps:
        db = firestore.client()
        return

    # الطريقة 1: Base64 من متغير البيئة (Render)
    if settings.FIREBASE_CONFIG_BASE64:
        try:
            decoded = base64.b64decode(settings.FIREBASE_CONFIG_BASE64)
            config_dict = json.loads(decoded)
            cred = credentials.Certificate(config_dict)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("✅ Firebase متصل (Base64)")
            return
        except Exception as e:
            print(f"⚠️ فشل Base64: {e}")

    # الطريقة 2: ملف محلي (تطوير)
    if os.path.exists(settings.FIREBASE_CONFIG_PATH):
        cred = credentials.Certificate(settings.FIREBASE_CONFIG_PATH)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase متصل (ملف محلي)")
        return

    raise RuntimeError("❌ لا يوجد إعداد Firebase. أضف FIREBASE_CONFIG_BASE64 أو serviceAccountKey.json")


def get_db():
    """إرجاع عميل Firestore"""
    if db is None:
        init_firebase()
    return db
