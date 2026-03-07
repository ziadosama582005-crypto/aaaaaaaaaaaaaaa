# -*- coding: utf-8 -*-
"""
مسارات API - APIs الرئيسية
"""

from flask import Blueprint, request, jsonify, session
from firebase_utils import *
from services.email_service import EmailService
from services.sms_service import SMSService
import logging

logger = logging.getLogger(__name__)

# إنشاء Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ===================== المحفظة والرصيد =====================

@api_bp.route('/get-balance', methods=['GET'])
def get_balance_api():
    """جلب رصيد المستخدم"""
    try:
        # سيتم استبدال هذا بنظام المصادقة لاحقاً
        user_id = request.args.get('user_id', '1')
        balance = get_user_balance(user_id)
        
        return jsonify({
            'success': True,
            'balance': balance
        })
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/add-balance', methods=['POST'])
def add_balance_api():
    """إضافة رصيد"""
    try:
        data = request.get_json()
        user_id = request.args.get('user_id', '1')
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': 'المبلغ يجب أن يكون أكبر من صفر'
            }), 400
        
        if add_balance(user_id, amount):
            return jsonify({
                'success': True,
                'message': 'تمت إضافة الرصيد',
                'new_balance': get_user_balance(user_id)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'فشل في إضافة الرصيد'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/get-transactions', methods=['GET'])
def get_transactions_api():
    """جلب معاملات المستخدم"""
    try:
        user_id = request.args.get('user_id', '1')
        limit = int(request.args.get('limit', 50))
        
        transactions = get_user_transactions(user_id, limit)
        
        return jsonify({
            'success': True,
            'transactions': transactions
        })
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===================== الطلبات =====================

@api_bp.route('/create-order', methods=['POST'])
def create_order_api():
    """إنشاء طلب جديد"""
    try:
        data = request.get_json()
        user_id = request.args.get('user_id', '1')
        items = data.get('items', [])
        total = float(data.get('total', 0))
        payment_method = data.get('payment_method', 'wallet')
        
        if not items or total <= 0:
            return jsonify({
                'success': False,
                'message': 'بيانات الطلب غير صحيحة'
            }), 400
        
        # خصم من المحفظة إذا كانت طريقة الدفع محفظة
        if payment_method == 'wallet':
            balance = get_user_balance(user_id)
            if balance < total:
                return jsonify({
                    'success': False,
                    'message': 'رصيد غير كافي'
                }), 400
            
            deduct_balance(user_id, total)
        
        # إنشاء الطلب
        order_id = create_order(user_id, items, total, payment_method)
        
        if order_id:
            # جلب بيانات المستخدم لإرسال التأكيد
            user = get_user(user_id)
            
            # إرسال تأكيد الطلب عبر البريد
            if user and user.get('email'):
                order_details = {
                    'order_id': order_id,
                    'items': items,
                    'total': total,
                    'date': 'اليوم'  # يمكن تحسينها لاحقاً
                }
                EmailService.send_order_confirmation(user['email'], order_details)
            
            # إرسال إشعار عبر SMS
            if user and user.get('phone'):
                SMSService.send_order_notification(user['phone'], order_id)
            
            return jsonify({
                'success': True,
                'order_id': order_id,
                'message': 'تم إنشاء الطلب بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'فشل في إنشاء الطلب'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/get-orders', methods=['GET'])
def get_orders_api():
    """جلب طلبات المستخدم"""
    try:
        user_id = request.args.get('user_id', '1')
        limit = int(request.args.get('limit', 50))
        
        orders = get_user_orders(user_id, limit)
        
        return jsonify({
            'success': True,
            'orders': orders
        })
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===================== المنتجات =====================

@api_bp.route('/get-products', methods=['GET'])
def get_products_api():
    """جلب جميع المنتجات"""
    try:
        products = get_all_products()
        
        return jsonify({
            'success': True,
            'products': products
        })
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/get-product/<product_id>', methods=['GET'])
def get_product_api(product_id):
    """جلب بيانات منتج"""
    try:
        product = get_product(product_id)
        
        if product:
            return jsonify({
                'success': True,
                'product': product
            })
        else:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
            
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===================== الأقسام =====================

@api_bp.route('/get-categories', methods=['GET'])
def get_categories_api():
    """جلب جميع الأقسام"""
    try:
        categories = get_all_categories()
        
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===================== المشتريات =====================

@api_bp.route('/get-user-purchases', methods=['GET'])
def get_user_purchases_api():
    """جلب مشتريات المستخدم"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'purchases': []
            })
        
        purchases = []
        
        if FIREBASE_AVAILABLE and db:
            from firebase_utils import db
            docs = db.collection('purchases')\
                .where('user_id', '==', str(user_id))\
                .order_by('purchased_at', direction='DESCENDING')\
                .stream()
            
            for doc in docs:
                purchase = doc.to_dict()
                purchase['id'] = doc.id
                purchases.append(purchase)
        
        return jsonify({
            'success': True,
            'purchases': purchases
        })
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'purchases': [],
            'message': str(e)
        })

print("✅ api routes تم تحميله")
