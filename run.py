#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف التشغيل الرئيسي
"""

import sys
import os

# إضافة المجلد الحالي للمسار
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    from app import app, logger
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    logger.info(f"🚀 بدء التطبيق")
    logger.info(f"📝 المنفذ: {port}")
    logger.info(f"🐛 الوضع: {'التطوير' if debug else 'الإنتاج'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
