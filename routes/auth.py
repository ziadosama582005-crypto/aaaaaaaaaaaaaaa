# -*- coding: utf-8 -*-
"""
مسارات المصادقة والدخول
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from services.auth_service import create_session, destroy_session, require_login, OTPManager, get_session_user
from services.email_service import EmailService
from services.sms_service import SMSService
from firebase_utils import create_user, get_user, db, FIREBASE_AVAILABLE
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# إنشاء Blueprint
auth_bp = Blueprint('auth', __name__)

# ===================== صفحات المصادقة =====================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        
        if not identifier:
            flash('❌ أدخل البريد الإلكتروني أو رقم الهاتف', 'danger')
            return redirect(url_for('auth.login'))
        
        # التحقق من صيغة البريد أو الهاتف
        is_email = '@' in identifier
        is_phone = identifier.replace('+', '').isdigit() and len(identifier) >= 9
        
        if not (is_email or is_phone):
            flash('❌ صيغة غير صحيحة', 'danger')
            return redirect(url_for('auth.login'))
        
        # توليد OTP
        otp = OTPManager.generate_otp(identifier)
        
        if not otp:
            flash('❌ حدث خطأ، حاول لاحقاً', 'danger')
            return redirect(url_for('auth.login'))
        
        # إرسال البريد أو SMS
        if is_email:
            if EmailService.send_otp_email(identifier, otp, identifier):
                flash(f'✅ تم إرسال الكود إلى {identifier}', 'success')
            else:
                flash('⚠️ تم إنشاء الكود لكن فشل الإرسال البريدي. لا تقلق، يمكنك المتابعة', 'warning')
        else:  # SMS
            if SMSService.send_otp_sms(identifier, otp):
                flash(f'✅ تم إرسال الكود عبر SMS إلى {identifier}', 'success')
            else:
                flash('⚠️ تم إنشاء الكود لكن فشل الإرسال. لا تقلق، يمكنك المتابعة', 'warning')
        
        # حفظ البيانات بشكل مؤقت
        session['pending_identifier'] = identifier
        session['is_email'] = is_email
        
        return redirect(url_for('auth.verify_otp'))
    
    return render_template('auth/login.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """صفحة التحقق من OTP"""
    identifier = session.get('pending_identifier')
    
    if not identifier:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp_code = request.form.get('otp', '').strip()
        
        # التحقق من الكود
        is_verified, message = OTPManager.verify_otp(identifier, otp_code)
        
        if not is_verified:
            flash(f'❌ {message}', 'danger')
            return redirect(url_for('auth.verify_otp'))
        
        # البحث عن المستخدم أو إنشاء حساب جديد
        user = None
        is_email = session.get('is_email', False)
        
        if FIREBASE_AVAILABLE and db:
            # البحث في Firebase
            query_field = 'email' if is_email else 'phone'
            docs = db.collection('users').where(query_field, '==', identifier).stream()
            
            for doc in docs:
                user = doc.to_dict()
                user['id'] = doc.id
                break
        
        # إذا لم توجد حساب، ننشئ واحداً جديداً
        if not user:
            user_id = create_user(
                user_id=None,
                email=identifier if is_email else '',
                phone=identifier if not is_email else '',
                name='مستخدم جديد'
            )
            
            if not user_id:
                flash('❌ فشل في إنشاء الحساب', 'danger')
                return redirect(url_for('auth.login'))
            
            user = {
                'user_id': user_id,
                'email': identifier if is_email else '',
                'phone': identifier if not is_email else ''
            }
            
            # إرسال بريد ترحيب (غير متزامن - يمكن تحسينه)
            if is_email:
                EmailService.send_welcome_email(identifier, 'مستخدم جديد')
            
            logger.info(f"✅ حساب جديد: {user_id}")
        
        # إنشاء جلسة
        user_id = user.get('user_id') or user.get('id')
        create_session(
            user_id,
            email=user.get('email', ''),
            phone=user.get('phone', '')
        )
        
        # تنظيف الجلسة المؤقتة
        session.pop('pending_identifier', None)
        OTPManager.mark_used(identifier)
        
        flash('✅ تم تسجيل الدخول بنجاح', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/verify_otp.html', identifier=identifier)

@auth_bp.route('/logout')
def logout():
    """تسجيل الخروج"""
    destroy_session()
    flash('✅ تم تسجيل الخروج', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@require_login
def profile():
    """الملف الشخصي"""
    user = get_session_user()
    
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('auth/profile.html', user=user)

# ===================== APIs للمصادقة =====================

@auth_bp.route('/api/send-otp', methods=['POST'])
def api_send_otp():
    """API لإرسال OTP"""
    try:
        data = request.get_json()
        identifier = data.get('identifier', '').strip()
        
        if not identifier:
            return jsonify({
                'success': False,
                'message': 'أدخل البريد الإلكتروني أو الهاتف'
            }), 400
        
        # توليد OTP
        otp = OTPManager.generate_otp(identifier)
        
        if not otp:
            return jsonify({
                'success': False,
                'message': 'حدث خطأ'
            }), 500
        
        # في الإنتاج: إرسال عبر Email أو SMS
        # send_email(identifier, f"كودك: {otp}")
        # send_sms(identifier, f"كودك: {otp}")
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال الكود',
            'otp': otp  # للاختبار فقط، احذفها في الإنتاج
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@auth_bp.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    """API للتحقق من OTP"""
    try:
        data = request.get_json()
        identifier = data.get('identifier', '').strip()
        otp_code = data.get('otp', '').strip()
        
        # التحقق من الكود
        is_verified, message = OTPManager.verify_otp(identifier, otp_code)
        
        if not is_verified:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
        # البحث أو إنشاء المستخدم
        user = None
        is_email = '@' in identifier
        
        if FIREBASE_AVAILABLE and db:
            query_field = 'email' if is_email else 'phone'
            docs = db.collection('users').where(query_field, '==', identifier).stream()
            
            for doc in docs:
                user = doc.to_dict()
                user['id'] = doc.id
                break
        
        # إنشاء حساب جديد
        if not user:
            user_id = create_user(
                user_id=None,
                email=identifier if is_email else '',
                phone=identifier if not is_email else '',
                name='مستخدم'
            )
            user = {'user_id': user_id}
        
        # إنشاء جلسة
        user_id = user.get('user_id') or user.get('id')
        create_session(user_id)
        OTPManager.mark_used(identifier)
        
        return jsonify({
            'success': True,
            'message': 'تم التحقق بنجاح',
            'user_id': str(user_id)
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@auth_bp.route('/api/get-current-user', methods=['GET'])
def api_get_current_user():
    """جلب المستخدم الحالي"""
    try:
        user = get_session_user()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'لم تقم بتسجيل الدخول'
            }), 401
        
        return jsonify({
            'success': True,
            'user': user
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

print("✅ auth routes تم تحميله")
