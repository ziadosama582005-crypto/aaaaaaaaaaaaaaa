# -*- coding: utf-8 -*-
"""
مسارات الفئات والمنتجات المتقدمة
"""

from flask import Blueprint, render_template, request, jsonify
from firebase_utils import db, FIREBASE_AVAILABLE, get_user, get_user_balance
from flask import session
import logging

logger = logging.getLogger(__name__)

# إنشاء Blueprint
categories_bp = Blueprint('categories', __name__)

# ===================== الفئات =====================

@categories_bp.route('/t/<category_id>')
def category(category_id):
    """صفحة الفئة مع المنتجات"""
    products = []
    sold_items = []
    my_purchases = []
    category = None
    
    user_id = session.get('user_id')
    
    if FIREBASE_AVAILABLE and db:
        try:
            # جلب الفئة
            cat_doc = db.collection('categories').document(category_id).get()
            if cat_doc.exists:
                category = cat_doc.to_dict()
                category['id'] = cat_doc.id
            
            # جلب المنتجات المتاحة
            docs = db.collection('products')\
                .where('category_id', '==', category_id)\
                .where('sold', '==', False)\
                .stream()
            
            for doc in docs:
                product = doc.to_dict()
                product['id'] = doc.id
                products.append(product)
            
            # جلب المنتجات المباعة
            docs = db.collection('products')\
                .where('category_id', '==', category_id)\
                .where('sold', '==', True)\
                .stream()
            
            for doc in docs:
                product = doc.to_dict()
                product['id'] = doc.id
                sold_items.append(product)
            
            # جلب مشترياتي من هذه الفئة
            if user_id:
                docs = db.collection('purchases')\
                    .where('user_id', '==', str(user_id))\
                    .where('category', '==', category_id)\
                    .stream()
                
                for doc in docs:
                    purchase = doc.to_dict()
                    purchase['id'] = doc.id
                    my_purchases.append(purchase)
        
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    
    user = None
    if user_id:
        user = get_user(user_id)
    
    balance = get_user_balance(user_id) if user_id else 0
    
    return render_template(
        'category.html',
        category=category,
        items=products,
        sold_items=sold_items,
        my_purchases=my_purchases,
        user_id=user_id,
        balance=balance,
        category_id=category_id,
        category_name=category.get('name') if category else category_id
    )

@categories_bp.route('/categories')
def all_categories():
    """جميع الفئات"""
    categories = []
    
    if FIREBASE_AVAILABLE and db:
        try:
            docs = db.collection('categories').stream()
            
            for doc in docs:
                cat = doc.to_dict()
                cat['id'] = doc.id
                
                # عد المنتجات
                available = len(list(db.collection('products')\
                    .where('category_id', '==', cat['id'])\
                    .where('sold', '==', False).stream()))
                
                sold = len(list(db.collection('products')\
                    .where('category_id', '==', cat['id'])\
                    .where('sold', '==', True).stream()))
                
                cat['products_count'] = available
                cat['sales_count'] = sold
                
                categories.append(cat)
        
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    
    return render_template('categories.html', categories=categories)

# ===================== API لتحميل البيانات =====================

@categories_bp.route('/api/category/<category_id>')
def api_get_category(category_id):
    """API للحصول على بيانات الفئة (متوفر، مباع، مشترياتي)"""
    user_id = session.get('user_id')
    
    if not FIREBASE_AVAILABLE or not db:
        return jsonify({'status': 'error', 'message': 'خدمة غير متاحة'}), 500
    
    try:
        available = []
        sold = []
        purchased = []
        
        # جلب المنتجات المتاحة
        docs = db.collection('products')\
            .where('category_id', '==', category_id)\
            .where('sold', '==', False)\
            .stream()
        
        for doc in docs:
            product = doc.to_dict()
            product['id'] = doc.id
            available.append(product)
        
        # جلب المنتجات المباعة
        docs = db.collection('products')\
            .where('category_id', '==', category_id)\
            .where('sold', '==', True)\
            .stream()
        
        for doc in docs:
            product = doc.to_dict()
            product['id'] = doc.id
            sold.append(product)
        
        # جلب مشترياتي من هذه الفئة
        if user_id:
            docs = db.collection('purchases')\
                .where('user_id', '==', str(user_id))\
                .where('category', '==', category_id)\
                .stream()
            
            for doc in docs:
                purchase = doc.to_dict()
                purchase['id'] = doc.id
                purchased.append(purchase)
        
        return jsonify({
            'status': 'success',
            'available': available,
            'sold': sold,
            'purchased': purchased
        })
    
    except Exception as e:
        logger.error(f"❌ خطأ في الحصول على بيانات الفئة: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

print("✅ categories routes تم تحميله")
