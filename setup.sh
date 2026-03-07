#!/bin/bash
# ملف التهيئة الأولية

echo "🚀 تهيئة البيئة..."

# تثبيت المكتبات
echo "📦 تثبيت المكتبات..."
pip install -r requirements.txt

# إنشاء المجلدات المطلوبة
echo "📁 إنشاء المجلدات..."
mkdir -p logs
mkdir -p tmp

# طباعة معلومات البيئة
echo "✅ البيئة جاهزة!"
echo ""
echo "📝 المعلومات:"
echo "- Flask Version: $(python -c 'import flask; print(flask.__version__)')"
echo "- Python Version: $(python --version)"
echo "- Environment: $FLASK_ENV"

echo ""
echo "🚀 لبدء التطبيق، شغل:"
echo "  python run.py              (للتطوير)"
echo "  gunicorn app:app           (للإنتاج)"
