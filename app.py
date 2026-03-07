# -*- coding: utf-8 -*-
"""
التطبيق الرئيسي - TR Store
متجر رقمي متكامل
"""

from flask import Flask, render_template, session, request, jsonify, redirect, url_for
from flask_cors import CORS
from config import *
from firebase_utils import init_firebase
import logging
import os
from datetime import datetime

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء التطبيق
app = Flask(__name__)
app.config.from_object('config')
CORS(app)

# تهيئة Firebase
logger.info("🔧 جاري تهيئة Firebase...")
init_firebase()

# استيراد وتسجيل المسارات
from routes.api import api_bp
from routes.auth import auth_bp
from routes.payment import payment_bp
from routes.purchases import purchases_bp
from routes.categories import categories_bp
from routes.admin import admin_bp

app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(purchases_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(admin_bp)

# ===================== المسارات الأساسية =====================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    from firebase_utils import get_all_categories
    
    categories = get_all_categories()
    
    return render_template('index.html', categories=categories)

@app.route('/category/<category_id>')
def category(category_id):
    """صفحة الفئة"""
    from firebase_utils import get_products_by_category
    
    products = get_products_by_category(category_id)
    
    return render_template('category.html', category_id=category_id, products=products)

@app.route('/product/<product_id>')
def product(product_id):
    """صفحة المنتج"""
    from firebase_utils import get_product
    
    product = get_product(product_id)
    
    if not product:
        return render_template('404.html'), 404
    
    return render_template('product.html', product=product)

@app.route('/shop')
def shop():
    """صفحة المتجر"""
    return render_template('shop.html')

@app.route('/cart')
def cart():
    """صفحة السلة"""
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    """صفحة الدفع"""
    return render_template('checkout.html')

@app.route('/orders')
def orders():
    """صفحة الطلبات"""
    return render_template('orders.html')

@app.route('/wallet')
def wallet():
    """صفحة المحفظة"""
    return render_template('wallet.html')

@app.route('/my_purchases')
def my_purchases():
    """صفحة مشترياتي"""
    return render_template('my_purchases.html')

@app.route('/admin')
def admin_dashboard():
    """لوحة تحكم الأدمن"""
    # سيتم إضافة فحص المصادقة لاحقاً
    return render_template('admin/dashboard.html')

# ===================== معالجات الأخطاء =====================

@app.errorhandler(404)
def not_found(error):
    """صفحة غير موجودة"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """خطأ في الخادم"""
    logger.error(f"❌ خطأ في الخادم: {error}")
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    """الوصول غير مصرح"""
    return render_template('403.html'), 403

# ===================== معلومات التطبيق =====================

@app.route('/api/info')
def api_info():
    """معلومات التطبيق"""
    return jsonify({
        'name': SITE_NAME,
        'description': SITE_DESCRIPTION,
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/health')
def health_check():
    """فحص صحة التطبيق"""
    from firebase_utils import FIREBASE_AVAILABLE
    
    return jsonify({
        'status': 'healthy',
        'firebase': 'connected' if FIREBASE_AVAILABLE else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

# ===================== نقطة الدخول =====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = DEBUG
    
    logger.info(f"🚀 بدء التطبيق على المنفذ {port}")
    logger.info(f"📝 الوضع: {'التطوير' if debug else 'الإنتاج'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
