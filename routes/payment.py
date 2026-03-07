# -*- coding: utf-8 -*-
"""
مسارات الدفع ومعالجة العمليات
"""

from flask import Blueprint, request, jsonify, session
from services.payment_service import PaymentProcessor
from services.auth_service import require_login
from firebase_utils import get_user_balance, create_order
import logging
import hmac
import hashlib
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# إنشاء Blueprint
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# ===================== الدفع من المحفظة =====================

@payment_bp.route('/wallet', methods=['POST'])
@require_login
def pay_with_wallet():
    """الدفع من المحفظة"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        items = data.get('items', [])
        total = float(data.get('total', 0))
        
        if not items or total <= 0:
            return jsonify({
                'success': False,
                'message': 'بيانات غير صحيحة'
            }), 400
        
        # إنشاء الطلب
        order_id = create_order(user_id, items, total, 'wallet')
        
        if not order_id:
            return jsonify({
                'success': False,
                'message': 'فشل في إنشاء الطلب'
            }), 500
        
        # معالجة الدفع من المحفظة
        success, message = PaymentProcessor.process_wallet_payment(
            user_id, total, order_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'order_id': order_id
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===================== الدفع عبر البوابة =====================

@payment_bp.route('/gateway/initiate', methods=['POST'])
@require_login
def initiate_gateway_payment():
    """بدء عملية دفع عبر البوابة"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        items = data.get('items', [])
        total = float(data.get('total', 0))
        method = data.get('method', 'card')  # card أو تحويل بنكي
        
        if not items or total <= 0:
            return jsonify({
                'success': False,
                'message': 'بيانات غير صحيحة'
            }), 400
        
        # إنشاء الطلب
        order_id = create_order(user_id, items, total, method)
        
        if not order_id:
            return jsonify({
                'success': False,
                'message': 'فشل في إنشاء الطلب'
            }), 500
        
        # بدء عملية الدفع
        success, message, payment_data = PaymentProcessor.initiate_gateway_payment(
            user_id, total, order_id, method
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'order_id': order_id,
                'payment_id': payment_data.get('payment_id'),
                'redirect_url': f"/payment/gateway/{payment_data.get('payment_id')}"
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
            
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===================== Callback من البوابة =====================

@payment_bp.route('/gateway/callback', methods=['POST', 'GET'])
def gateway_callback():
    """استقبال رد من البوابة بعد الدفع"""
    try:
        # البيانات من البوابة (حسب توثيق البوابة)
        data = request.get_json() or request.args.to_dict()
        
        payment_id = data.get('payment_id')
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        signature = data.get('signature')
        
        # التحقق من التوقيع (للأمان)
        # استخدم مفتاحك السري
        from config import PAYMENT_API_KEY
        
        # إعادة بناء التوقيع ...
        # expected_signature = hmac.new(
        #     PAYMENT_API_KEY.encode(),
        #     f"{payment_id}{transaction_id}{status}".encode(),
        #     hashlib.sha256
        # ).hexdigest()
        
        # if signature != expected_signature:
        #     return jsonify({'success': False, 'message': 'توقيع غير صحيح'}), 401
        
        # التحقق من الدفع
        if status == 'success':
            success, message = PaymentProcessor.verify_payment(
                payment_id, transaction_id
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'تم الدفع بنجاح'
                })
        
        return jsonify({
            'success': False,
            'message': 'فشلت عملية الدفع'
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===================== معلومات الدفع =====================

@payment_bp.route('/methods', methods=['GET'])
def get_payment_methods():
    """جلب طرق الدفع المتاحة"""
    try:
        user_id = session.get('user_id')
        balance = get_user_balance(user_id) if user_id else 0
        
        methods = {
            'wallet': {
                'name': '💰 المحفظة',
                'description': 'الدفع من رصيدك',
                'available': balance > 0,
                'balance': balance,
                'fee': 0,
                'icon': '💳'
            },
            'card': {
                'name': '🏦 بطاقة ائتمان',
                'description': 'فيزا أو ماستركارد',
                'available': True,
                'fee': 2.5,  # نسبة رسوم
                'icon': '🏦'
            },
            'transfer': {
                'name': '🏧 تحويل بنكي',
                'description': 'تحويل مباشر للحساب',
                'available': True,
                'fee': 0,
                'icon': '🏧'
            }
        }
        
        return jsonify({
            'success': True,
            'methods': methods
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===================== التحويل للبوابة =====================

@payment_bp.route('/redirect/<payment_id>', methods=['GET'])
def redirect_to_gateway(payment_id):
    """تحويل للبوابة للدفع"""
    try:
        from config import PAYMENT_GATEWAY_URL
        
        # بناء رابط الدفع
        gateway_url = f"{PAYMENT_GATEWAY_URL}?payment_id={payment_id}&callback={request.base_url}callback"
        
        return jsonify({
            'success': True,
            'redirect_url': gateway_url
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

print("✅ payment routes تم تحميله")
