# 📤 نشر التطبيق على Render

## 📋 المتطلبات المسبقة

- ✅ حساب GitHub
- ✅ حساب على [render.com](https://render.com)
- ✅ Firebase serviceAccountKey.json
- ✅ API Key من بوابة الدفع

---

## 🚀 خطوات النشر

### الخطوة 1️⃣: إعداد GitHub (إذا لم تكن قد فعلت بعد)

```bash
# أنشئ مستودع جديد على GitHub
git init
git add .
git commit -m "Initial commit: TR Store - E-commerce Platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tr-store.git
git push -u origin main
```

### الخطوة 2️⃣: إنشاء Web Service على Render

1. **اذهب إلى:** https://render.com/dashboard
2. **اضغط:** `New` → `Web Service`
3. **في القائمة:** اختر `Connect repository`
4. **ابحث عن:** مستودع `tr-store` وانقر `Connect`

### الخطوة 3️⃣: إعدادات الخدمة

**في صفحة الإعدادات:**

| الحقل | القيمة |
|-------|--------|
| **Name** | `tr-store` أو اسم اختياري |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

### الخطوة 4️⃣: متغيرات البيئة

اضغط `Add Environment Variable` وأضف:

```
FLASK_ENV          production
DEBUG               False
SECRET_KEY          (اضغط القيمة العشوائية أدناه)
```

**لإنشاء SECRET_KEY قوي:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**متغيرات إضافية:**

```
PAYMENT_API_KEY     (مفتاح EdfaPay)
PAYMENT_GATEWAY_SECRET     (سر البوابة)
PAYMENT_CALLBACK_URL       https://your-app-name.onrender.com/api/payment/gateway/callback
SITE_URL           https://your-app-name.onrender.com
```

### الخطوة 5️⃣: رفع serviceAccountKey.json

**الطريقة 1: عبر .env var (موصى **

```bash
# قراءة الملف وتحويله
cat serviceAccountKey.json | base64

# ثم أضفه كـ متغير بيئة
FIREBASE_CONFIG_BASE64=(القيمة المشفرة)
```

**ثم عدّل app.py:**
```python
import base64
import json
import os

if 'FIREBASE_CONFIG_BASE64' in os.environ:
    decoded = base64.b64decode(os.environ['FIREBASE_CONFIG_BASE64'])
    config_dict = json.loads(decoded)
    # استخدم config_dict مباشرة
```

**الطريقة 2: كملف في المستودع**

```bash
# أضفه مباشرة (احذره من .gitignore إذا كان موجود)
git add serviceAccountKey.json
git commit -m "Add firebase config"
git push
```

### الخطوة 6️⃣: الخوادم الثابتة والقد محدودة (Free)

**ملاحظات مهمة:**

| الميزة | Render Free | Render Pro |
|--------|-----------|-----------|
| **الوقت المتوقف** | ✅ (لا وقت توقف) | ✅ (دائم) |
| **الذاكرة (RAM)** | 512 MB | 1 GB+ |
| **المعالج** | مشترك | مخصص |
| **Concurrency** | منخفض | عالي |
| **HTTPS** | ✅ | ✅ |

**للإنتاج:** استخدم Render Pro أو خادم مخصص

---

## ✅ التحقق من النشر

### 1️⃣: افحص سجل البناء (Build Logs)

```
Building...
Fetching repository...
Building application...
Running build command: pip install -r requirements.txt
```

**إذا رأيت أخطاء:**
- تحقق من requirements.txt
- تأكد من وجود جميع الملفات
- افحص Python version

### 2️⃣: افحص سجل التشغيل (Runtime Logs)

```
=  Render BUILD COMPLETE
=  Running on https://tr-store-xxxx.onrender.com
```

**اختبر الموقع:**
```bash
curl https://tr-store-xxxx.onrender.com/api/info
```

### 3️⃣: اختبر المميزات الأساسية

```bash
# الصحة
curl https://tr-store-xxxx.onrender.com/api/health

# المعلومات
curl https://tr-store-xxxx.onrender.com/api/info

# المنتجات
curl https://tr-store-xxxx.onrender.com/api/get-products
```

---

## 🔧 استكشاف الأخطاء الشائعة

### ❌ خطأ: Build Failed

**الحل:**
```bash
# تحقق من requirements.txt locally
pip install -r requirements.txt

# إذا فشل، أصلح وأضفه
```

### ❌ خطأ: Runtime Error

**تحقق:**
- هل `app.py` موجود؟
- هل `PORT` يُقرأ من البيئة؟
- هل `SECRET_KEY` حُدّد؟

```python
port = int(os.getenv('PORT', 5000))
app.run(port=port)
```

### ❌ خطأ: Firebase غير متصل

**الحل:**
- تحقق من `serviceAccountKey.json` صحيح
- تأكد من Base64 encoding صحيح
- جرب الاتصال محلياً أولاً

### ❌ خطأ: Callback من البوابة لا يأتي

**الحل:**
- افحص Webhook URL في إعدادات البوابة
- تأكد من `https://` وليس `http://`
- اختبر من Dashboard البوابة

---

## 🔄 التحديثات والتعديلات

### إرسال تحديث جديد

```bash
# عدّل الملفات
# ...

# أرسل
git add .
git commit -m "Fix: update payment gateway integration"
git push origin main
```

**Render ستشتغل البناء تلقائياً!**

---

## 📊 المراقبة والسجلات

### في Render Dashboard:

1. **Logs:** اضغط على service
2. **Runtime Logs:** شاهد logs الحي
3. **Build Logs:** شاهد بناء سابقة
4. **Metrics:** استهلاك المورد

### إنشاء Alerts:

```
Dashboard → Settings → Alerts
```

---

## 🔒 نصائح الأمان

✅ **استخدم secrets آمنة:**
```bash
# لا تضع في الكود أبداً!
# استخدم Environment Variables فقط
```

✅ **تفعيل HTTPS:**
- Render يفعلها افتراضياً ✅

✅ **قيود الوصول:**
```python
if FLASK_ENV == 'production':
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
```

✅ **السجلات:**
- راقب السجلات للأخطاء
- احذر من محاولات اختراق

---

## 🚨 الاستجابة للمشاكل

### إذا توقف التطبيق:

1. افحص سجلات Render
2. تحقق من قاعدة البيانات Firebase
3. اتصل بـ Render Support

### إذا تمس الأداء ببطء:

1. ارقِّ إلى Pro Plan
2. أضف Caching
3. حسّن قاعدة البيانات

---

## 📞 للمساعدة

- **Render Support:** https://render.com/support
- **Documentation:** https://render.com/docs
- **Firebase Support:** https://firebase.google.com/support

---

**آخر تحديث:** 7 مارس 2026
