# -*- coding: utf-8 -*-
"""
مسارات المشتريات والمشترياتي
"""

from flask import Blueprint, render_template, request, jsonify, session
from services.auth_service import require_login
from firebase_utils import db, FIREBASE_AVAILABLE
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# إنشاء Blueprint
purchases_bp = Blueprint('purchases', __name__)

# ===================== المشتريات =====================

@purchases_bp.route('/my_purchases')
@require_login
def my_purchases():
    """صفحة مشترياتي"""
    user_id = session.get('user_id')
    purchases = []
    
    if FIREBASE_AVAILABLE and db:
        try:
            docs = db.collection('purchases')\
                .where('user_id', '==', str(user_id))\
                .order_by('purchased_at', direction='DESCENDING')\
                .stream()
            
            for doc in docs:
                purchase = doc.to_dict()
                purchase['id'] = doc.id
                purchases.append(purchase)
        except Exception as e:
            logger.error(f"❌ خطأ في جلب المشتريات: {e}")
    
    return render_template('my_purchases.html', purchases=purchases)

@purchases_bp.route('/api/cart/add', methods=['POST'])
@require_login
def add_to_cart_api():
    """إضافة منتج للسلة من API"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        product_id = data.get('product_id')
        buyer_details = data.get('buyer_details', '')
        
        if not product_id:
            return jsonify({
                'status': 'error',
                'message': 'معرف المنتج مطلوب'
            }), 400
        
        # جلب المنتج
        product = db.collection('products').document(product_id).get()
        if not product.exists:
            return jsonify({
                'status': 'error',
                'message': 'المنتج غير موجود'
            }), 404
        
        product_data = product.to_dict()
        
        # التحقق من حالة المنتج
        if product_data.get('sold'):
            return jsonify({
                'status': 'error',
                'message': 'هذا المنتج مباع'
            }), 400
        
        # إضافة للسلة
        cart_ref = db.collection('carts').document(user_id)
        cart = cart_ref.get()
        
        if cart.exists:
            cart_data = cart.to_dict()
        else:
            cart_data = {'items': [], 'created_at': datetime.now()}
        
        # إضافة العنصر
        item = {
            'product_id': product_id,
            'item_name': product_data.get('item_name'),
            'price': product_data.get('price'),
            'category': product_data.get('category_id'),
            'delivery_type': product_data.get('delivery_type', 'instant'),
            'buyer_details': buyer_details,
            'added_at': datetime.now(),
            'sold': False
        }
        
        if 'items' not in cart_data:
            cart_data['items'] = []
        
        cart_data['items'].append(item)
        cart_data['updated_at'] = datetime.now()
        
        cart_ref.set(cart_data)
        
        return jsonify({
            'status': 'success',
            'message': 'تم إضافة المنتج للسلة'
        })
    
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@purchases_bp.route('/api/cart/view', methods=['GET'])
@require_login
def view_cart():
    """جلب السلة"""
    try:
        user_id = session.get('user_id')
        
        cart = db.collection('carts').document(user_id).get()
        
        if not cart.exists:
            return jsonify({
                'status': 'success',
                'items': [],
                'total': 0
            })
        
        cart_data = cart.to_dict()
        items = cart_data.get('items', [])
        
        # حساب الإجمالي
        total = sum(item.get('price', 0) for item in items if not item.get('sold'))
        
        return jsonify({
            'status': 'success',
            'items': items,
            'total': total,
            'count': len([i for i in items if not i.get('sold')])
        })
    
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@purchases_bp.route('/api/cart/remove', methods=['POST'])
@require_login
def remove_from_cart():
    """حذف منتج من السلة"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        product_id = data.get('product_id')
        
        cart = db.collection('carts').document(user_id).get()
        
        if not cart.exists:
            return jsonify({
                'status': 'error',
                'message': 'السلة فارغة'
            }), 404
        
        cart_data = cart.to_dict()
        items = cart_data.get('items', [])
        
        # حذف العنصر
        items = [i for i in items if i.get('product_id') != product_id]
        
        cart_data['items'] = items
        db.collection('carts').document(user_id).set(cart_data)
        
        return jsonify({
            'status': 'success',
            'message': 'تم حذف المنتج'
        })
    
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@purchases_bp.route('/api/cart/checkout', methods=['POST'])
@require_login
def checkout():
    """إتمام الشراء"""
    try:
        user_id = session.get('user_id')
        
        # جلب السلة
        cart = db.collection('carts').document(user_id).get()
        
        if not cart.exists or not cart.get('items'):
            return jsonify({
                'status': 'error',
                'message': 'السلة فارغة'
            }), 400
        
        cart_data = cart.to_dict()
        items = cart_data.get('items', [])
        
        # تصفية المنتجات غير المباعة
        available_items = [i for i in items if not i.get('sold')]
        
        if not available_items:
            return jsonify({
                'status': 'error',
                'message': 'لا توجد منتجات متاحة'
            }), 400
        
        # حساب الإجمالي
        total = sum(item.get('price', 0) for item in available_items)
        
        # جلب رصيد المستخدم
        from firebase_utils import get_user_balance, deduct_balance
        balance = get_user_balance(user_id)
        
        if balance < total:
            return jsonify({
                'status': 'error',
                'message': 'رصيد غير كافي'
            }), 400
        
        # خصم من الرصيد
        deduct_balance(user_id, total)
        
        # تسجيل المشتريات
        for item in available_items:
            purchase = {
                'user_id': str(user_id),
                'product_id': item.get('product_id'),
                'item_name': item.get('item_name'),
                'price': item.get('price'),
                'category': item.get('category'),
                'buyer_details': item.get('buyer_details'),
                'delivery_type': item.get('delivery_type', 'instant'),
                'purchased_at': datetime.now(),
                'status': 'completed',
                'hidden_data': item.get('hidden_data', '')
            }
            
            db.collection('purchases').document().set(purchase)
        
        # مسح السلة
        db.collection('carts').document(user_id).delete()
        
        return jsonify({
            'status': 'success',
            'message': 'تم الشراء بنجاح',
            'purchased_count': len(available_items),
            'total': total
        })
    
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

print("✅ purchases routes تم تحميله")
