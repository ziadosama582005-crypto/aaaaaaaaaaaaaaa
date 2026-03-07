# 🏪 TR Store - متجر رقمي متكامل

## 📋 نظرة عامة

متجر إلكتروني كامل ومتقدم مبني بـ **Flask** و **Firebase**، مع نظام مصادقة قوي وتكامل مع بوابات الدفع.

## ✨ المميزات

### 🛍️ للمستخدمين
- ✅ تسجيل دخول آمن بـ OTP (Email/Phone)
- ✅ عرض المنتجات والأقسام
- ✅ سلة التسوق المتقدمة
- ✅ نظام دفع متعدد الطرق (محفظة، بطاقة، تحويل)
- ✅ محفظة رقمية مع رصيد
- ✅ سجل الطلبات والمعاملات
- ✅ ملف شخصي

### 👨‍💼 للأدمن (قريباً)
- ✅ لوحة تحكم متقدمة
- ✅ إدارة المنتجات والأقسام
- ✅ إدارة الطلبات
- ✅ إدارة المستخدمين
- ✅ الإحصائيات والتقارير

## 🛠️ التقنيات المستخدمة

- **Backend:** Python Flask 2.3+
- **Database:** Firebase/Firestore
- **Frontend:** HTML, CSS, JavaScript Vanilla
- **Authentication:** OTP-based (Email/Phone)
- **Payment Gateway:** EdfaPay (أو أي بوابة أخرى)
- **Hosting:** Render

## 📁 بنية المشروع

```
aaaaaaaaaaaaaaa/
├── app.py                              # التطبيق الرئيسي
├── config.py                           # الإعدادات
├── firebase_utils.py                   # خدمات Firebase
├── run.py                              # ملف التشغيل
├── Procfile                            # للـ Render/Heroku
├── requirements.txt                    # المكتبات
├── setup.sh                            # سكريبت الإعداد
├── .env                                # متغيرات البيئة
├── .gitignore
│
├── routes/
│   ├── api.py                          # APIs الأساسية
│   ├── auth.py                         # APIs المصادقة
│   ├── payment.py                      # APIs الدفع
│   └── __init__.py
│
├── services/
│   ├── auth_service.py                 # خدمة المصادقة
│   └── payment_service.py              # خدمة الدفع
│
├── templates/
│   ├── base.html                       # القالب الأساسي
│   ├── index.html                      # الرئيسية
│   ├── category.html
│   ├── product.html
│   ├── cart.html
│   ├── checkout.html
│   ├── orders.html
│   ├── wallet.html
│   ├── auth/
│   │   ├── login.html
│   │   ├── verify_otp.html
│   │   └── profile.html
│   └── error pages...
│
├── static/
│   ├── css/style.css                   # التنسيقات
│   └── js/main.js                      # JavaScript
│
├── AUTHENTICATION_PAYMENT_GUIDE.md     # دليل المصادقة والدفع
└── README.md
```

## 🚀 البدء السريع

### 1️⃣ التثبيت المحلي

```bash
# استنساخ المشروع
git clone https://github.com/your-repo/aaaaaaaaaaaaaaa.git
cd aaaaaaaaaaaaaaa

# إنشاء بيئة افتراضية
python3 -m venv venv
source venv/bin/activate  # على Windows: venv\Scripts\activate

# تثبيت المكتبات
pip install -r requirements.txt

# إعداد البيئة
bash setup.sh  # أو شغل python run.py مباشرة
```

### 2️⃣ إعداد Firebase

1. اذهب إلى [Firebase Console](https://console.firebase.google.com)
2. أنشئ مشروع جديد
3. اذهب إلى **Project Settings** → **Service Accounts**
4. اضغط **Generate New Private Key**
5. احفظ الملف كـ `serviceAccountKey.json` في جذر المشروع

### 3️⃣ إعداد البوابة (EdfaPay)

1. سجل على https://edfapay.com
2. خذ API Key من Dashboard
3. أضفها في `.env`:

```env
PAYMENT_API_KEY=your_key_here
PAYMENT_GATEWAY_SECRET=your_secret_here
```

### 4️⃣ التشغيل

```bash
# للتطوير
python run.py

# للإنتاج
gunicorn app:app
```

الموقع سيكون متاح على: **http://localhost:5000**

---

## 📊 نموذج قاعدة البيانات

### Collections الرئيسية:

#### `users`
```json
{
  "user_id": "123",
  "email": "user@example.com",
  "phone": "+966501234567",
  "name": "محمد",
  "balance": 1500.50,
  "created_at": "2026-03-07",
  "is_banned": false
}
```

#### `products`
```json
{
  "name": "منتج 1",
  "category_id": "cat-1",
  "price": 99.99,
  "description": "وصف",
  "image_url": "...",
  "is_active": true
}
```

#### `orders`
```json
{
  "user_id": "123",
  "items": [...],
  "total_amount": 299.97,
  "payment_method": "wallet",
  "status": "completed",
  "created_at": "2026-03-07"
}
```

---

## 🔗 APIs الرئيسية

### المصادقة
- `POST /login` - تسجيل الدخول
- `POST /verify-otp` - التحقق من الكود
- `GET /logout` - تسجيل الخروج
- `GET /profile` - الملف الشخصي
- `POST /api/send-otp` - إرسال OTP (API)
- `POST /api/verify-otp` - التحقق (API)

### الدفع
- `GET /api/payment/methods` - طرق الدفع
- `POST /api/payment/wallet` - دفع من المحفظة
- `POST /api/payment/gateway/initiate` - بدء دفع
- `POST /api/payment/gateway/callback` - رد البوابة

### المتجر
- `GET /api/get-products` - جميع المنتجات
- `GET /api/get-categories` - الأقسام
- `POST /api/create-order` - إنشاء طلب

---

## 🚀 النشر على Render

### 1️⃣ إعداد المستودع
```bash
# تأكد من وجود:
# - Procfile
# - requirements.txt
# - app.py
```

### 2️⃣ إنشاء Web Service على Render

1. اذهب إلى [render.com](https://render.com)
2. اضغط **New** → **Web Service**
3. اربط حسابك بـ GitHub
4. اختر المستودع

### 3️⃣ الإعدادات
```
Build Command:   pip install -r requirements.txt
Start Command:   gunicorn app:app
```

### 4️⃣ متغيرات البيئة
أضف في **Environment**:
```
FLASK_ENV=production
DEBUG=False
SECRET_KEY=(أضف قيمة عشوائية قوية)
PAYMENT_API_KEY=(مفتاح البوابة)
PAYMENT_GATEWAY_SECRET=(السر)
```

---

## 🔐 الأمان

✅ تشفير + HTTPS في الإنتاج
✅ OTP قوي مع حد أقصى محاولات
✅ جلسات آمنة
✅ التحقق من التوقيع الرقمي للمعاملات
✅ حماية CSRF

---

## 📚 التوثيق الكاملة

- [دليل المصادقة والدفع](AUTHENTICATION_PAYMENT_GUIDE.md) - شامل وتفصيلي

---

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:
1. Fork المستودع
2. أنشئ Branch جديد
3. Commit التغييرات
4. Push واطلب PR

---

## 📞 الدعم

للمزيد من الدعم أو الأسئلة، تواصل معنا.

---

## 📄 الترخيص

جميع الحقوق محفوظة © 2026

---

**آخر تحديث:** 7 مارس 2026
**الإصدار:** 1.0.0 - Beta

