# 📧 نظام إرسال الإيميلات - Email System

## كيف يعمل؟

عندما يدخل العميل صفحة المتجر (`store.html`) ويكتب إيميله، النظام:
1. يتحقق أن العميل مسجل عند التاجر
2. ينشئ كود تحقق من 6 أرقام (صالح 10 دقائق)
3. **يحاول إرسال الكود عبر الإيميل**
4. إذا فشل الإرسال → يعرض الكود مباشرة في الصفحة (fallback)

---

## إعداد متغيرات البيئة في Render

أضف هذه المتغيرات في **Render > Dashboard > Environment**:

| المتغير | القيمة | ملاحظة |
|---|---|---|
| `SMTP_EMAIL` | `your-email@gmail.com` | الإيميل المرسل منه |
| `SMTP_PASSWORD` | `xxxxxxxxxxxx` | App Password (بدون شرطات) |
| `SMTP_SERVER` | `smtp.gmail.com` | سيرفر Gmail |
| `SMTP_PORT` | `587` | بورت STARTTLS |

---

## كيفية الحصول على App Password من Gmail

### الخطوة 1: تفعيل التحقق بخطوتين
1. افتح [إعدادات أمان Google](https://myaccount.google.com/signinoptions/two-step-verification)
2. فعّل **التحقق بخطوتين** (2-Step Verification)

### الخطوة 2: إنشاء App Password
1. افتح [كلمات مرور التطبيقات](https://myaccount.google.com/apppasswords)
2. اكتب اسم التطبيق (مثلاً: `Loyalty System`)
3. اضغط **Create**
4. ستظهر كلمة مرور مثل: `guwb-scoj-fvmq-ydbh`

### الخطوة 3: نسخ الباسورد بالشكل الصحيح
- ✅ **صح:** `guwbscojfvmqydbh` (بدون شرطات، بدون مسافات)
- ❌ **غلط:** `guwb-scoj-fvmq-ydbh` (بالشرطات)
- ❌ **غلط:** ` guwbscojfvmqydbh ` (مسافات قبل/بعد)

---

## أخطاء شائعة وحلولها

### ❌ `Network is unreachable`
- **السبب:** Render المجاني يحظر SMTP أحياناً
- **الحل:** النظام يعرض الكود مباشرة كبديل (fallback)

### ❌ `authentication failed`
- **السبب:** كلمة المرور خاطئة
- **الحل:**
  - تأكد أن `SMTP_PASSWORD` هو App Password وليس كلمة مرور حسابك
  - احذف الشرطات من الباسورد
  - تأكد من عدم وجود مسافات

### ❌ `Connection timed out`
- **السبب:** السيرفر لا يستجيب خلال 10 ثواني
- **الحل:** تأكد أن `SMTP_SERVER` و `SMTP_PORT` صحيحين

---

## الملفات المتعلقة

| الملف | الوصف |
|---|---|
| `app/email_service.py` | دالة إرسال الإيميل عبر SMTP |
| `app/config.py` | إعدادات SMTP (متغيرات البيئة) |
| `app/routers/store.py` | endpoint إرسال الكود `/api/store/send-code` |
| `app/models.py` | `VerificationCodeService` - حفظ الأكواد في Firestore |

---

## البورتات المدعومة

| البورت | البروتوكول | الاستخدام |
|---|---|---|
| `587` | STARTTLS | Gmail, Outlook (الافتراضي) |
| `465` | SSL | بعض السيرفرات القديمة |

النظام يكتشف تلقائياً: إذا البورت `465` يستخدم `SMTP_SSL`، غير كذا يستخدم `STARTTLS`.

---

## ملاحظة مهمة

إذا لم يتم إعداد `SMTP_EMAIL` و `SMTP_PASSWORD`، النظام يعمل بشكل طبيعي ولكن **يعرض الكود مباشرة في الصفحة** بدون إرساله بالإيميل.
