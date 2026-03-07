# -*- coding: utf-8 -*-
"""
خدمة Firebase - التعامل مع قاعدة البيانات
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# المتغيرات العامة
db = None
FIREBASE_AVAILABLE = False

def init_firebase():
    """تهيئة Firebase"""
    global db, FIREBASE_AVAILABLE
    
    try:
        from config import FIREBASE_CONFIG_PATH
        
        if os.path.exists(FIREBASE_CONFIG_PATH):
            cred = credentials.Certificate(FIREBASE_CONFIG_PATH)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            FIREBASE_AVAILABLE = True
            print("✅ Firebase: متصل")
            return True
        else:
            print(f"⚠️ Firebase: لم نجد ملف {FIREBASE_CONFIG_PATH}")
            FIREBASE_AVAILABLE = False
            return False
            
    except Exception as e:
        print(f"❌ خطأ في Firebase: {e}")
        FIREBASE_AVAILABLE = False
        return False

# ===================== دوال المستخدم =====================

def create_user(user_id, email='', phone='', name=''):
    """إنشاء مستخدم جديد"""
    if not FIREBASE_AVAILABLE or not db:
        return False
    
    try:
        user_data = {
            'user_id': user_id,
            'email': email,
            'phone': phone,
            'name': name,
            'balance': 0.0,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'is_banned': False
        }
        
        db.collection('users').document(str(user_id)).set(user_data)
        logger.info(f"✅ تم إنشاء مستخدم: {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء المستخدم: {e}")
        return False

def get_user(user_id):
    """جلب بيانات المستخدم"""
    if not FIREBASE_AVAILABLE or not db:
        return None
    
    try:
        doc = db.collection('users').document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"❌ خطأ في جلب المستخدم: {e}")
        return None

def get_user_balance(user_id):
    """جلب رصيد المستخدم"""
    user = get_user(user_id)
    if user:
        return float(user.get('balance', 0))
    return 0.0

def add_balance(user_id, amount):
    """إضافة رصيد للمستخدم"""
    if not FIREBASE_AVAILABLE or not db:
        return False
    
    try:
        current_balance = get_user_balance(user_id)
        new_balance = current_balance + amount
        
        db.collection('users').document(str(user_id)).update({
            'balance': new_balance,
            'updated_at': datetime.now()
        })
        
        # تسجيل العملية
        log_transaction(user_id, 'balance_add', amount, f'إضافة رصيد')
        
        logger.info(f"✅ تمت إضافة {amount} للمستخدم {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إضافة الرصيد: {e}")
        return False

def deduct_balance(user_id, amount):
    """خصم رصيد من المستخدم"""
    if not FIREBASE_AVAILABLE or not db:
        return False
    
    try:
        current_balance = get_user_balance(user_id)
        
        if current_balance < amount:
            logger.warning(f"⚠️ رصيد غير كافي للمستخدم {user_id}")
            return False
        
        new_balance = current_balance - amount
        
        db.collection('users').document(str(user_id)).update({
            'balance': new_balance,
            'updated_at': datetime.now()
        })
        
        # تسجيل العملية
        log_transaction(user_id, 'balance_deduct', amount, f'خصم رصيد')
        
        logger.info(f"✅ تم خصم {amount} من المستخدم {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في خصم الرصيد: {e}")
        return False

# ===================== دوال المنتجات =====================

def create_product(name, category_id, price, description='', image_url='', delivery_type='instant', sold=False):
    """إنشاء منتج جديد"""
    if not FIREBASE_AVAILABLE or not db:
        return None
    
    try:
        product_data = {
            'item_name': name,
            'category_id': category_id,
            'price': float(price),
            'description': description,
            'image_url': image_url,
            'created_at': datetime.now(),
            'is_active': True,
            'stock': 0,
            'delivery_type': delivery_type,  # instant أو manual
            'sold': sold,
            'seller_id': None,
            'sales_count': 0
        }
        
        doc_ref = db.collection('products').document()
        doc_ref.set(product_data)
        
        logger.info(f"✅ تم إنشاء منتج: {name}")
        return doc_ref.id
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء المنتج: {e}")
        return None

def get_product(product_id):
    """جلب بيانات المنتج"""
    if not FIREBASE_AVAILABLE or not db:
        return None
    
    try:
        doc = db.collection('products').document(product_id).get()
        if doc.exists:
            return {**doc.to_dict(), 'id': product_id}
        return None
    except Exception as e:
        logger.error(f"❌ خطأ في جلب المنتج: {e}")
        return None

def get_all_products():
    """جلب جميع المنتجات"""
    if not FIREBASE_AVAILABLE or not db:
        return []
    
    try:
        docs = db.collection('products').where('is_active', '==', True).stream()
        products = []
        for doc in docs:
            product = doc.to_dict()
            product['id'] = doc.id
            products.append(product)
        return products
    except Exception as e:
        logger.error(f"❌ خطأ في جلب المنتجات: {e}")
        return []

def get_products_by_category(category_id):
    """جلب منتجات الفئة"""
    if not FIREBASE_AVAILABLE or not db:
        return []
    
    try:
        docs = db.collection('products')\
            .where('category_id', '==', category_id)\
            .where('is_active', '==', True)\
            .stream()
        
        products = []
        for doc in docs:
            product = doc.to_dict()
            product['id'] = doc.id
            products.append(product)
        return products
    except Exception as e:
        logger.error(f"❌ خطأ في جلب المنتجات: {e}")
        return []

# ===================== دوال الأقسام =====================

def create_category(name, description='', image_url=''):
    """إنشاء قسم جديد"""
    if not FIREBASE_AVAILABLE or not db:
        return None
    
    try:
        category_data = {
            'name': name,
            'description': description,
            'image_url': image_url,
            'created_at': datetime.now(),
            'is_active': True
        }
        
        doc_ref = db.collection('categories').document()
        doc_ref.set(category_data)
        
        logger.info(f"✅ تم إنشاء قسم: {name}")
        return doc_ref.id
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء القسم: {e}")
        return None

def get_all_categories():
    """جلب جميع الأقسام"""
    if not FIREBASE_AVAILABLE or not db:
        return []
    
    try:
        docs = db.collection('categories').where('is_active', '==', True).stream()
        categories = []
        for doc in docs:
            category = doc.to_dict()
            category['id'] = doc.id
            categories.append(category)
        return categories
    except Exception as e:
        logger.error(f"❌ خطأ في جلب الأقسام: {e}")
        return []

# ===================== دوال المعاملات =====================

def log_transaction(user_id, transaction_type, amount, description=''):
    """تسجيل معاملة"""
    if not FIREBASE_AVAILABLE or not db:
        return False
    
    try:
        transaction = {
            'user_id': str(user_id),
            'type': transaction_type,
            'amount': float(amount),
            'description': description,
            'timestamp': datetime.now(),
            'status': 'completed'
        }
        
        db.collection('transactions').document().set(transaction)
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في تسجيل المعاملة: {e}")
        return False

def get_user_transactions(user_id, limit=50):
    """جلب معاملات المستخدم"""
    if not FIREBASE_AVAILABLE or not db:
        return []
    
    try:
        docs = db.collection('transactions')\
            .where('user_id', '==', str(user_id))\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        
        transactions = []
        for doc in docs:
            transaction = doc.to_dict()
            transaction['id'] = doc.id
            transactions.append(transaction)
        return transactions
    except Exception as e:
        logger.error(f"❌ خطأ في جلب المعاملات: {e}")
        return []

# ===================== دوال الطلبات =====================

def create_order(user_id, items, total_amount, payment_method='wallet'):
    """إنشاء طلب جديد"""
    if not FIREBASE_AVAILABLE or not db:
        return None
    
    try:
        order_data = {
            'user_id': str(user_id),
            'items': items,
            'total_amount': float(total_amount),
            'payment_method': payment_method,
            'status': 'pending',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        doc_ref = db.collection('orders').document()
        doc_ref.set(order_data)
        
        logger.info(f"✅ تم إنشاء طلب: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء الطلب: {e}")
        return None

def get_order(order_id):
    """جلب بيانات الطلب"""
    if not FIREBASE_AVAILABLE or not db:
        return None
    
    try:
        doc = db.collection('orders').document(order_id).get()
        if doc.exists:
            return {**doc.to_dict(), 'id': order_id}
        return None
    except Exception as e:
        logger.error(f"❌ خطأ في جلب الطلب: {e}")
        return None

def get_user_orders(user_id, limit=50):
    """جلب طلبات المستخدم"""
    if not FIREBASE_AVAILABLE or not db:
        return []
    
    try:
        docs = db.collection('orders')\
            .where('user_id', '==', str(user_id))\
            .order_by('created_at', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        
        orders = []
        for doc in docs:
            order = doc.to_dict()
            order['id'] = doc.id
            orders.append(order)
        return orders
    except Exception as e:
        logger.error(f"❌ خطأ في جلب الطلبات: {e}")
        return []

# ===================== دوال المشتريات =====================

def create_purchase(user_id, product_id, item_name, price, category, delivery_type='instant', buyer_details=''):
    """إنشاء مشتراة جديدة"""
    if not FIREBASE_AVAILABLE or not db:
        return None
    
    try:
        purchase = {
            'user_id': str(user_id),
            'product_id': product_id,
            'item_name': item_name,
            'price': float(price),
            'category': category,
            'delivery_type': delivery_type,
            'buyer_details': buyer_details,
            'purchased_at': datetime.now(),
            'status': 'completed',
            'hidden_data': ''
        }
        
        doc_ref = db.collection('purchases').document()
        doc_ref.set(purchase)
        
        logger.info(f"✅ تم إنشاء مشتراة: {item_name}")
        return doc_ref.id
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء المشتراة: {e}")
        return None

def get_user_purchases(user_id, limit=50):
    """جلب مشتريات المستخدم"""
    if not FIREBASE_AVAILABLE or not db:
        return []
    
    try:
        docs = db.collection('purchases')\
            .where('user_id', '==', str(user_id))\
            .order_by('purchased_at', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        
        purchases = []
        for doc in docs:
            purchase = doc.to_dict()
            purchase['id'] = doc.id
            purchases.append(purchase)
        return purchases
    except Exception as e:
        logger.error(f"❌ خطأ في جلب المشتريات: {e}")
        return []

print("✅ firebase_utils تم تحميله")
