"""
نقاط النهاية الخاصة بمتجر العميل - تسجيل دخول بالإيميل + استعراض المنتجات + استبدال
"""

import random
import string
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.database import get_db
from app.models import (
    MerchantService, CustomerService, ProductService,
    RedemptionService, VerificationCodeService, PointsService,
)
from app.schemas import StoreLoginRequest, StoreVerifyRequest, StoreRedeemRequest

router = APIRouter(prefix="/api/store", tags=["Store"])

CODE_EXPIRY_MINUTES = 10


def _generate_code() -> str:
    return ''.join(random.choices(string.digits, k=6))


# ──────────────────── تسجيل الدخول بكود ────────────────────

@router.post("/send-code")
def send_verification_code(body: StoreLoginRequest):
    """إرسال كود التحقق للعميل — يظهر الكود في الاستجابة (بدون إيميل حقيقي)"""
    db = get_db()

    # التأكد من أن التاجر موجود ونشط
    merchant = MerchantService.get_by_id(db, body.merchant_id)
    if not merchant or merchant.get("status") != "active":
        raise HTTPException(status_code=404, detail="المتجر غير موجود أو غير نشط")

    # التأكد من أن العميل مسجل عند هذا التاجر
    customers = CustomerService.list_by_merchant(db, body.merchant_id)
    customer = next((c for c in customers if c.get("email", "").lower() == body.email.lower()), None)
    if not customer:
        raise HTTPException(status_code=404, detail="لا يوجد حساب بهذا البريد عند هذا التاجر")

    code = _generate_code()
    VerificationCodeService.create(db, email=body.email.lower(), code=code, merchant_id=body.merchant_id)

    # في بيئة حقيقية يُرسل الكود عبر الإيميل
    # هنا نعرضه مباشرة للتسهيل
    return {"detail": "تم إرسال كود التحقق", "code": code}


@router.post("/verify-code")
def verify_code(body: StoreVerifyRequest):
    """التحقق من الكود وإرجاع بيانات العميل"""
    db = get_db()

    record = VerificationCodeService.get_latest(db, body.email.lower(), body.merchant_id)
    if not record:
        raise HTTPException(status_code=400, detail="لا يوجد كود تحقق لهذا البريد")

    # التحقق من الانتهاء
    created = datetime.fromisoformat(record["created_at"])
    if datetime.now(timezone.utc) - created > timedelta(minutes=CODE_EXPIRY_MINUTES):
        raise HTTPException(status_code=400, detail="انتهت صلاحية الكود، اطلب كود جديد")

    if record["code"] != body.code:
        raise HTTPException(status_code=400, detail="الكود غير صحيح")

    # تأكيد الكود
    VerificationCodeService.mark_used(db, record["id"])

    # جلب بيانات العميل
    customers = CustomerService.list_by_merchant(db, body.merchant_id)
    customer = next((c for c in customers if c.get("email", "").lower() == body.email.lower()), None)
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")

    merchant = MerchantService.get_by_id(db, body.merchant_id)

    return {
        "customer": {
            "id": customer["id"],
            "name": customer["name"],
            "email": customer.get("email"),
            "points_balance": customer.get("points_balance", 0),
        },
        "merchant": {
            "id": merchant["id"],
            "store_name": merchant["store_name"],
        }
    }


# ──────────────────── صفحة المتجر ────────────────────

@router.get("/merchant/{merchant_id}")
def get_store_info(merchant_id: str):
    """بيانات المتجر العامة"""
    db = get_db()
    merchant = MerchantService.get_by_id(db, merchant_id)
    if not merchant or merchant.get("status") != "active":
        raise HTTPException(status_code=404, detail="المتجر غير موجود أو غير نشط")

    return {
        "id": merchant["id"],
        "store_name": merchant["store_name"],
        "address": merchant.get("address"),
        "phone": merchant.get("phone"),
    }


@router.get("/merchant/{merchant_id}/products")
def get_store_products(merchant_id: str):
    """قائمة المنتجات المتوفرة للمتجر"""
    db = get_db()
    merchant = MerchantService.get_by_id(db, merchant_id)
    if not merchant or merchant.get("status") != "active":
        raise HTTPException(status_code=404, detail="المتجر غير موجود")

    products = ProductService.list_by_merchant(db, merchant_id, active_only=True)
    # إخفاء المنتجات بمخزون 0
    products = [p for p in products if p.get("stock", -1) != 0]
    return products


@router.post("/redeem")
def redeem_product(body: StoreRedeemRequest, customer_id: str = Query(...), merchant_id: str = Query(...)):
    """استبدال منتج بالنقاط"""
    db = get_db()

    customer = CustomerService.get_by_id(db, customer_id)
    if not customer or customer.get("merchant_id") != merchant_id:
        raise HTTPException(status_code=404, detail="العميل غير موجود")

    product = ProductService.get_by_id(db, body.product_id)
    if not product or product.get("merchant_id") != merchant_id:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")

    if not product.get("is_active", True):
        raise HTTPException(status_code=400, detail="المنتج غير متوفر حالياً")

    if product.get("stock", -1) == 0:
        raise HTTPException(status_code=400, detail="المنتج نفد من المخزون")

    balance = customer.get("points_balance", 0)
    if balance < product["points_cost"]:
        raise HTTPException(
            status_code=400,
            detail=f"رصيدك غير كافٍ. تحتاج {product['points_cost']} نقطة، رصيدك {balance}",
        )

    # خصم النقاط
    new_balance = balance - product["points_cost"]
    CustomerService.update_balance(db, customer_id, new_balance)

    # تقليل المخزون إذا ليس unlimited
    if product.get("stock", -1) > 0:
        ProductService.update(db, body.product_id, stock=product["stock"] - 1)

    # تسجيل الحركة في سجل النقاط
    PointsService.create(
        db,
        customer_id=customer_id,
        merchant_id=merchant_id,
        action="deduct",
        amount=product["points_cost"],
        balance_after=new_balance,
        note=f"استبدال: {product['name']}",
    )

    # إنشاء طلب الاستبدال
    redemption = RedemptionService.create(
        db,
        customer_id=customer_id,
        merchant_id=merchant_id,
        product_id=body.product_id,
        product_name=product["name"],
        points_spent=product["points_cost"],
    )

    return {
        "detail": "تم الاستبدال بنجاح!",
        "redemption_id": redemption["id"],
        "new_balance": new_balance,
    }


@router.get("/my-redemptions")
def my_redemptions(customer_id: str = Query(...), merchant_id: str = Query(...)):
    """سجل استبدالات العميل"""
    db = get_db()

    customer = CustomerService.get_by_id(db, customer_id)
    if not customer or customer.get("merchant_id") != merchant_id:
        raise HTTPException(status_code=404, detail="العميل غير موجود")

    return RedemptionService.list_by_customer(db, customer_id)
