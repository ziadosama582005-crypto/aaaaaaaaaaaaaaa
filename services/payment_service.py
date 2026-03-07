# -*- coding: utf-8 -*-
"""
خدمة الدفع - نظام الدفع المتكامل
"""

import logging
from datetime import datetime
from firebase_utils import (
    create_order, log_transaction, get_user_balance,
    deduct_balance, add_balance, db, FIREBASE_AVAILABLE
)

logger = logging.getLogger(__name__)

class PaymentProcessor:
    """معالج الدفع الرئيسي"""
    
    @staticmethod
    def process_wallet_payment(user_id, amount, order_id):
        """معالجة الدفع من المحفظة"""
        try:
            balance = get_user_balance(user_id)
            
            if balance < amount:
                return False, "رصيد غير كافي"
            
            # خصم من المحفظة
            if deduct_balance(user_id, amount):
                # تسجيل العملية
                if FIREBASE_AVAILABLE and db:
                    db.collection('payments').document().set({
                        'user_id': str(user_id),
                        'order_id': order_id,
                        'amount': amount,
                        'method': 'wallet',
                        'status': 'completed',
                        'timestamp': datetime.now()
                    })
                
                logger.info(f"✅ دفع من المحفظة: {user_id} - {amount}")
                return True, "تم الدفع بنجاح"
            else:
                return False, "فشل في عملية الدفع"
                
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False, str(e)
    
    @staticmethod
    def initiate_gateway_payment(user_id, amount, order_id, payment_method='card'):
        """بدء عملية دفع عبر بوابة دفع"""
        try:
            from config import PAYMENT_API_KEY
            
            payment_data = {
                'user_id': str(user_id),
                'order_id': order_id,
                'amount': float(amount),
                'method': payment_method,
                'status': 'pending',
                'created_at': datetime.now(),
                'callback_url': None  # سيتم تحديثه لاحقاً
            }
            
            if FIREBASE_AVAILABLE and db:
                doc_ref = db.collection('pending_payments').document()
                doc_ref.set(payment_data)
                payment_data['payment_id'] = doc_ref.id
            
            logger.info(f"✅ دفع معلق: {payment_data.get('payment_id')}")
            return True, "جاري معالجة الدفع", payment_data
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False, str(e), None
    
    @staticmethod
    def verify_payment(payment_id, gateway_transaction_id):
        """التحقق من عملية دفع من البوابة"""
        try:
            if not FIREBASE_AVAILABLE or not db:
                return False, "قاعدة البيانات غير متاحة"
            
            # جلب بيانات الدفع
            payment_doc = db.collection('pending_payments').document(payment_id).get()
            
            if not payment_doc.exists:
                return False, "العملية غير موجودة"
            
            payment = payment_doc.to_dict()
            
            # تحديث الحالة
            db.collection('pending_payments').document(payment_id).update({
                'status': 'completed',
                'gateway_transaction_id': gateway_transaction_id,
                'verified_at': datetime.now()
            })
            
            # تسجيل المعاملة
            log_transaction(
                payment['user_id'],
                'payment',
                payment['amount'],
                f"دفع من بوابة ({payment['method']})"
            )
            
            # تحديث الطلب
            order_id = payment.get('order_id')
            if order_id:
                db.collection('orders').document(order_id).update({
                    'status': 'completed',
                    'payment_id': payment_id,
                    'updated_at': datetime.now()
                })
            
            logger.info(f"✅ تم التحقق من الدفع: {payment_id}")
            return True, "تم التحقق من الدفع"
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False, str(e)

print("✅ payment_service تم تحميله")
