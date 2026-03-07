# -*- coding: utf-8 -*-
"""
مسارات لوحة الإدارة
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from firebase_utils import db, FIREBASE_AVAILABLE, get_user, get_user_balance
import logging
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# إنشاء Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ===================== التحكم بالوصول =====================

ADMIN_USERS = ['admin', '1', 'system']  # يمكن تعديله لاستخدام قاعدة البيانات

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id or str(user_id) not in ADMIN_USERS:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ===================== لوحة التحكم الرئيسية =====================

@admin_bp.route('/dashboard')
@require_admin
def dashboard():
    """لوحة التحكم الرئيسية"""
    stats = {
        'total_users': 0,
        'total_products': 0,
        'total_sales': 0,
        'total_revenue': 0,
        'recent_orders': [],
        'top_products': []
    }
    
    if FIREBASE_AVAILABLE and db:
        try:
            # حساب إحصائيات
            users = list(db.collection('users').stream())
            stats['total_users'] = len(users)
            
            products = list(db.collection('products').stream())
            stats['total_products'] = len(products)
            
            purchases = list(db.collection('purchases').stream())
            stats['total_sales'] = len(purchases)
            
            total_revenue = sum(p.get('price', 0) for p in [p.to_dict() for p in purchases])
            stats['total_revenue'] = total_revenue
            
            # الطلبات الأخيرة
            recent_purchases = db.collection('purchases')\
                .order_by('purchased_at', direction='DESCENDING')\
                .limit(10)\
                .stream()
            
            for doc in recent_purchases:
                purchase = doc.to_dict()
                purchase['id'] = doc.id
                stats['recent_orders'].append(purchase)
            
            # المنتجات الأكثر مبيعاً
            all_products = [p.to_dict() for p in products]
            top_products = sorted(all_products, key=lambda x: x.get('sales_count', 0), reverse=True)[:5]
            stats['top_products'] = top_products
        
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الإحصائيات: {e}")
    
    return render_template('admin/dashboard.html', stats=stats)

# ===================== إدارة المنتجات =====================

@admin_bp.route('/products')
@require_admin
def products():
    """إدارة المنتجات"""
    products_list = []
    
    if FIREBASE_AVAILABLE and db:
        try:
            docs = db.collection('products').stream()
            
            for doc in docs:
                product = doc.to_dict()
                product['id'] = doc.id
                products_list.append(product)
        
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    
    return render_template('admin/products.html', products=products_list)

@admin_bp.route('/api/products/create', methods=['POST'])
@require_admin
def create_product():
    """إضافة منتج جديد"""
    data = request.get_json()
    
    if not FIREBASE_AVAILABLE or not db:
        return jsonify({'status': 'error', 'message': 'خدمة غير متاحة'}), 500
    
    try:
        product = {
            'item_name': data.get('item_name', ''),
            'category_id': data.get('category_id', ''),
            'price': float(data.get('price', 0)),
            'description': data.get('description', ''),
            'delivery_type': data.get('delivery_type', 'instant'),
            'sold': False,
            'sales_count': 0,
            'created_at': datetime.now()
        }
        
        doc_ref = db.collection('products').document()
        doc_ref.set(product)
        
        logger.info(f"✅ تم إنشاء منتج: {product['item_name']}")
        return jsonify({'status': 'success', 'id': doc_ref.id}), 201
    
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/products/<product_id>/update', methods=['POST'])
@require_admin
def update_product(product_id):
    """تحديث منتج"""
    data = request.get_json()
    
    if not FIREBASE_AVAILABLE or not db:
        return jsonify({'status': 'error', 'message': 'خدمة غير متاحة'}), 500
    
    try:
        updates = {
            'item_name': data.get('item_name'),
            'category_id': data.get('category_id'),
            'price': float(data.get('price', 0)),
            'description': data.get('description'),
            'delivery_type': data.get('delivery_type'),
            'sold': data.get('sold', False),
            'updated_at': datetime.now()
        }
        
        db.collection('products').document(product_id).update(updates)
        
        logger.info(f"✅ تم تحديث المنتج: {product_id}")
        return jsonify({'status': 'success'})
    
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/products/<product_id>/delete', methods=['POST'])
@require_admin
def delete_product(product_id):
    """حذف منتج"""
    if not FIREBASE_AVAILABLE or not db:
        return jsonify({'status': 'error', 'message': 'خدمة غير متاحة'}), 500
    
    try:
        db.collection('products').document(product_id).delete()
        
        logger.info(f"✅ تم حذف المنتج: {product_id}")
        return jsonify({'status': 'success'})
    
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ===================== إدارة الطلبات =====================

@admin_bp.route('/orders')
@require_admin
def orders():
    """إدارة الطلبات"""
    orders_list = []
    
    if FIREBASE_AVAILABLE and db:
        try:
            docs = db.collection('purchases')\
                .order_by('purchased_at', direction='DESCENDING')\
                .stream()
            
            for doc in docs:
                order = doc.to_dict()
                order['id'] = doc.id
                orders_list.append(order)
        
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    
    return render_template('admin/orders.html', orders=orders_list)

# ===================== إدارة المستخدمين =====================

@admin_bp.route('/users')
@require_admin
def users():
    """إدارة المستخدمين"""
    users_list = []
    
    if FIREBASE_AVAILABLE and db:
        try:
            docs = db.collection('users').stream()
            
            for doc in docs:
                user = doc.to_dict()
                user['id'] = doc.id
                
                # عد الطلبات
                purchases_count = len(list(db.collection('purchases')\
                    .where('user_id', '==', str(user['id']))\
                    .stream()))
                
                user['purchases_count'] = purchases_count
                users_list.append(user)
        
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    
    return render_template('admin/users.html', users=users_list)

# ===================== التقارير =====================

@admin_bp.route('/reports')
@require_admin
def reports():
    """التقارير والإحصائيات المتقدمة"""
    report_data = {
        'daily_sales': [],
        'category_sales': {},
        'payment_methods': {}
    }
    
    if FIREBASE_AVAILABLE and db:
        try:
            # حساب المبيعات اليومية
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            
            purchases = list(db.collection('purchases')\
                .where('purchased_at', '>=', week_ago)\
                .stream())
            
            daily_totals = {}
            for purchase in purchases:
                p = purchase.to_dict()
                date = p.get('purchased_at')
                if date:
                    date_str = date.strftime('%Y-%m-%d')
                    daily_totals[date_str] = daily_totals.get(date_str, 0) + p.get('price', 0)
            
            report_data['daily_sales'] = daily_totals
        
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    
    return render_template('admin/reports.html', report_data=report_data)

# ===================== API للإحصائيات =====================

@admin_bp.route('/api/stats')
@require_admin
def api_stats():
    """API للحصول على الإحصائيات"""
    stats = {
        'users': 0,
        'products': 0,
        'sales': 0,
        'revenue': 0
    }
    
    if FIREBASE_AVAILABLE and db:
        try:
            stats['users'] = len(list(db.collection('users').stream()))
            stats['products'] = len(list(db.collection('products').stream()))
            
            purchases = list(db.collection('purchases').stream())
            stats['sales'] = len(purchases)
            stats['revenue'] = sum(p.get('price', 0) for p in [p.to_dict() for p in purchases])
        
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    
    return jsonify(stats)

print("✅ admin routes تم تحميله")