# دليل النشر على Render

## المتطلبات قبل البدء

1. **حساب Render** — سجّل في [render.com](https://render.com)
2. **مشروع Firebase** — أنشئ مشروع في [Firebase Console](https://console.firebase.google.com)
3. **الريبو على GitHub** — المشروع مرفوع على GitHub

---

## الخطوة 1: إعداد Firebase

### 1.1 إنشاء مشروع Firebase
- ادخل [Firebase Console](https://console.firebase.google.com)
- اضغط **Add Project** → اختر اسم → أكمل الإنشاء

### 1.2 تفعيل Firestore
- من القائمة الجانبية: **Build → Firestore Database**
- اضغط **Create Database**
- اختر **Production mode**
- اختر أقرب Region (مثلاً `europe-west1` أو `us-central1`)

### 1.3 تحميل ملف Service Account
- اذهب إلى **Project Settings** (⚙️ أعلى القائمة الجانبية)
- تبويب **Service accounts**
- اضغط **Generate new private key**
- سيتم تحميل ملف `serviceAccountKey.json`

### 1.4 تحويل الملف إلى Base64
افتح Terminal ونفّذ:
```bash
cat serviceAccountKey.json | base64 -w 0
```
**انسخ الناتج كاملاً** — ستحتاجه في Render.

> ⚠️ على macOS استخدم: `cat serviceAccountKey.json | base64`

---

## الخطوة 2: إنشاء Web Service في Render

1. ادخل [Render Dashboard](https://dashboard.render.com)
2. اضغط **New** → **Web Service**
3. اربط حساب GitHub واختر الريبو: `aaaaaaaaaaaaaaa`
4. املأ الإعدادات:

| الإعداد | القيمة |
|---------|--------|
| **Name** | loyalty-points-api (أو أي اسم) |
| **Region** | اختر الأقرب لك |
| **Branch** | main |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT` |
| **Plan** | Free (أو حسب احتياجك) |

---

## الخطوة 3: إضافة متغيرات البيئة (Environment Variables)

في صفحة الـ Web Service على Render → تبويب **Environment**:

### المتغيرات المطلوبة (4 متغيرات):

| المتغير | الوصف | مثال |
|---------|-------|------|
| `FIREBASE_CONFIG_BASE64` | ناتج أمر base64 من الخطوة 1.4 | `ewogICJ0eXBlIjogInNlcn...` (نص طويل) |
| `SECRET_KEY` | مفتاح عشوائي لتشفير JWT | أنشئه بالأمر أدناه |
| `ADMIN_EMAIL` | إيميل المدير | `admin@mystore.com` |
| `ADMIN_PASSWORD` | كلمة مرور المدير | `MyStr0ng!Pass` |

### طريقة إنشاء SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
سيطلع لك مفتاح عشوائي مثل:
```
a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
```

### متغيرات اختيارية:

| المتغير | القيمة الافتراضية | الوصف |
|---------|------------------|-------|
| `APP_NAME` | Loyalty Points System | اسم التطبيق |
| `ALGORITHM` | HS256 | خوارزمية JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 (24 ساعة) | مدة صلاحية التوكن |
| `DEBUG` | False | وضع التطوير |

---

## الخطوة 4: النشر

- بعد إضافة المتغيرات، اضغط **Save Changes**
- Render سيبدأ **Build** تلقائياً
- انتظر حتى يظهر **Live** ✅

---

## الخطوة 5: اختبار التطبيق

بعد ظهور الرابط (مثلاً `https://loyalty-points-api.onrender.com`):

### فحص سريع:
```bash
curl https://loyalty-points-api.onrender.com/
```
يجب أن يرجع:
```json
{"status": "running", "app": "Loyalty Points System", "version": "1.0.0"}
```

### تسجيل دخول المدير:
```bash
curl -X POST https://loyalty-points-api.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@mystore.com", "password": "MyStr0ng!Pass"}'
```

### عرض وثائق API:
افتح في المتصفح:
```
https://loyalty-points-api.onrender.com/docs
```

---

## ملخص متغيرات البيئة في Render

```
FIREBASE_CONFIG_BASE64=<الناتج من base64>
SECRET_KEY=<مفتاح عشوائي 64 حرف>
ADMIN_EMAIL=admin@mystore.com
ADMIN_PASSWORD=MyStr0ng!Pass
```

هذه **4 متغيرات فقط** تحتاج إضافتها في Render. الباقي له قيم افتراضية.

---

## ملاحظات مهمة

- ❌ **لا ترفع** ملف `serviceAccountKey.json` على GitHub — هو موجود في `.gitignore`
- ❌ **لا ترفع** ملف `.env` — هو أيضاً في `.gitignore`
- ✅ في Render، المتغيرات تُضاف من لوحة التحكم مباشرة
- ✅ الخطة المجانية في Render تنام بعد 15 دقيقة بدون طلبات (أول طلب بعدها يأخذ ~30 ثانية)
