# 🔐 نظام المصادقة والدفع - التوثيق الكامل

## 📖 نظرة عامة

هذا الملف يوضح كيفية استخدام نظام المصادقة والدفع الكامل المدمج في التطبيق.

---

## 🔑 نظام المصادقة

### 1️⃣ تسجيل الدخول بـ OTP

**الخطوة 1: إرسال OTP**

```bash
POST /login
Content-Type: application/x-www-form-urlencoded

identifier=user@email.com  # أو رقم الهاتف
```

**الرد:**
```json
{
  "success": true,
  "message": "تم إرسال الكود إلى user@email.com",
  "otp": "123456"  // للاختبار فقط
}
```

**الخطوة 2: التحقق من الكود**

```bash
POST /verify-otp
Content-Type: application/x-www-form-urlencoded

otp=123456
```

**الرد:**
```json
{
  "success": true,
  "message": "تم تسجيل الدخول بنجاح",
  "user_id": "user-123"
}
```

### 2️⃣ APIs المصادقة

#### إرسال OTP (API)
```bash
POST /api/send-otp
Content-Type: application/json

{
  "identifier": "user@email.com"
}
```

#### التحقق من OTP (API)
```bash
POST /api/verify-otp
Content-Type: application/json

{
  "identifier": "user@email.com",
  "otp": "123456"
}
```

#### جلب المستخدم الحالي
```bash
GET /api/get-current-user
```

**الرد:**
```json
{
  "success": true,
  "user": {
    "user_id": "123",
    "email": "user@email.com",
    "phone": "+966501234567",
    "balance": 1500.50,
    "created_at": "2026-03-07T10:30:00"
  }
}
```

#### تسجيل الخروج
```bash
GET /logout
```

---

## 💳 نظام الدفع

### 1️⃣ طرق الدفع المتاحة

```bash
GET /api/payment/methods
```

**الرد:**
```json
{
  "success": true,
  "methods": {
    "wallet": {
      "name": "💰 المحفظة",
      "description": "الدفع من رصيدك",
      "available": true,
      "balance": 1500.50,
      "fee": 0,
      "icon": "💳"
    },
    "card": {
      "name": "🏦 بطاقة ائتمان",
      "description": "فيزا أو ماستركارد",
      "available": true,
      "fee": 2.5,
      "icon": "🏦"
    },
    "transfer": {
      "name": "🏧 تحويل بنكي",
      "description": "تحويل مباشر للحساب",
      "available": true,
      "fee": 0,
      "icon": "🏧"
    }
  }
}
```

### 2️⃣ الدفع من المحفظة

```bash
POST /api/payment/wallet
Content-Type: application/json

{
  "items": [
    {
      "id": "product-1",
      "name": "منتج 1",
      "price": 50,
      "quantity": 2
    }
  ],
  "total": 100
}
```

**الرد:**
```json
{
  "success": true,
  "message": "تم الدفع بنجاح",
  "order_id": "order-123"
}
```

### 3️⃣ الدفع عبر بوابة (بطاقة)

**الخطوة 1: بدء عملية الدفع**

```bash
POST /api/payment/gateway/initiate
Content-Type: application/json

{
  "items": [
    {
      "id": "product-1",
      "name": "منتج 1",
      "price": 100,
      "quantity": 1
    }
  ],
  "total": 100,
  "method": "card"
}
```

**الرد:**
```json
{
  "success": true,
  "message": "جاري معالجة الدفع",
  "order_id": "order-456",
  "payment_id": "pay-789",
  "redirect_url": "/payment/gateway/pay-789"
}
```

**الخطوة 2: تحويل العميل للبوابة**
```
https://api.edfapay.com/payment?payment_id=pay-789&callback=...
```

**الخطوة 3: Callback من البوابة إلى التطبيق**
```bash
POST /api/payment/gateway/callback
Content-Type: application/json

{
  "payment_id": "pay-789",
  "transaction_id": "txn-123456",
  "status": "success",
  "signature": "hash..."
}
```

---

## 🔧 إعداد البوابة

### EdfaPay

1. **التسجيل:**
   - اذهب إلى: https://edfapay.com
   - أنشئ حسابك

2. **الحصول على API Key:**
   - من Dashboard → API Keys
   - انسخ `API_KEY` و `API_SECRET`

3. **الإعداد في .env:**
```env
PAYMENT_API_KEY=your_edfapay_api_key
PAYMENT_GATEWAY_SECRET=your_edfapay_secret
PAYMENT_GATEWAY_URL=https://api.edfapay.com/payment
PAYMENT_CALLBACK_URL=https://your-app.com/api/payment/gateway/callback
```

4. **Webhook في البوابة:**
   - من Dashboard → Webhooks
   - أضف: `https://your-app.com/api/payment/gateway/callback`
   - اختر الأحداث: `payment.completed`, `payment.failed`

---

## 📊 بنية قاعدة البيانات الإضافية

### Collection: `pending_payments`
```
{
  payment_id: string,
  user_id: string,
  order_id: string,
  amount: float,
  method: string ('card', 'transfer'),
  status: string ('pending', 'completed', 'failed'),
  gateway_transaction_id: string,
  created_at: timestamp,
  verified_at: timestamp
}
```

### Collection: `payments`
```
{
  user_id: string,
  order_id: string,
  amount: float,
  method: string ('wallet', 'card', 'transfer'),
  status: string ('completed', 'failed'),
  timestamp: timestamp
}
```

---

## 🚀 التشغيل على Render

### 1. إنشاء حساب على Render
- اذهب إلى: https://render.com
- اربط حسابك بـ GitHub

### 2. إنشاء Web Service جديد
- اختر `New` → `Web Service`
- اختر المستودع

### 3. الإعدادات
- **Name:** tr-store
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

### 4. متغيرات البيئة
أضف في Environment:
```
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your-secret-key-here
PAYMENT_API_KEY=your-edfapay-key
PAYMENT_GATEWAY_SECRET=your-edfapay-secret
FIREBASE_CONFIG_PATH=./serviceAccountKey.json
```

### 5. Firebase
- أضف `serviceAccountKey.json` كـ secret
- أو استخدم GitHub Secrets

---

## 🔒 الأمان

### نقاط مهمة:
1. **HTTPS فقط في الإنتاج**
   - `SESSION_COOKIE_SECURE=True`
   - `SESSION_COOKIE_HTTPONLY=True`

2. **التوقيع الرقمي**
   - تحقق من توقيع Callback من البوابة

3. **Rate Limiting**
   - حد أقصى للمحاولات: 3 محاولات لـ OTP
   - صلاحية OTP: 5 دقائق

4. **المفاتيح السرية**
   - استخدم Environment Variables
   - لا تضع المفاتيح في الكود

---

## 🧪 الاختبار

### 1. محلي (Development)
```bash
# تثبيت المكتبات
pip install -r requirements.txt

# تعيين البيانات
export FIREBASE_CONFIG_PATH=./serviceAccountKey.json

# التشغيل
python run.py
```

### 2. اختبار APIs
```bash
# إرسال OTP
curl -X POST http://localhost:5000/api/send-otp \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test@example.com"}'

# التحقق من OTP
curl -X POST http://localhost:5000/api/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test@example.com", "otp": "123456"}'
```

---

## ❌ استكشاف الأخطاء

### مشكلة: OTP لا يأتي
**الحل:**
- تحقق من صحة البريد/الهاتف
- تحقق من إعدادات Email/SMS السيرفر
- تحقق من السجلات (logs)

### مشكلة: فشل الدفع
**الحل:**
- تحقق من API Key صحيح
- تحقق من Connection الإنترنت
- جرب مع حساب اختبار للبوابة

### مشكلة: جلسة مفقودة
**الحل:**
- تحقق من `SECRET_KEY` متطابق
- تحقق من `SESSION_TYPE` تم ضبطه
- امسح cookies وجرب مرة أخرى

---

## 📝 ملاحظات

- نظام OTP يستخدم ذاكرة (يجب استبداله بـ Redis في الإنتاج)
- Walletالرصيد محفوظ في Firebase
- جميع المعاملات مسجلة في `transactions` collection

---

**آخر تحديث:** فبراير 2026
