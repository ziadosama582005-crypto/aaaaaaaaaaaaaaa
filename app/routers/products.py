"""
نقاط النهاية الخاصة بإدارة المنتجات - CRUD للتاجر + إدارة طلبات الاستبدال
"""

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.dependencies import require_active_merchant
from app.models import ProductService, RedemptionService, CustomerService, MerchantService
from app.schemas import (
    ProductCreateRequest, ProductUpdateRequest, ProductOut,
    RedemptionOut, RedemptionActionRequest,
)
from app.email_service import send_redemption_rejected_email

router = APIRouter(prefix="/api/products", tags=["Products"])


# ──────────────────── المنتجات ────────────────────

@router.post("/", response_model=ProductOut, status_code=201)
def create_product(
    body: ProductCreateRequest,
    merchant: dict = Depends(require_active_merchant),
):
    db = get_db()
    product = ProductService.create(
        db,
        merchant_id=merchant["id"],
        name=body.name,
        description=body.description,
        image_url=body.image_url,
        points_cost=body.points_cost,
        stock=body.stock,
        category=body.category,
        product_type=body.product_type,
        required_fields=body.required_fields,
    )
    return product


@router.get("/", response_model=list[ProductOut])
def list_products(merchant: dict = Depends(require_active_merchant)):
    db = get_db()
    return ProductService.list_by_merchant(db, merchant["id"])


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    body: ProductUpdateRequest,
    merchant: dict = Depends(require_active_merchant),
):
    db = get_db()
    product = ProductService.get_by_id(db, product_id)
    if not product or product.get("merchant_id") != merchant["id"]:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")

    ProductService.update(db, product_id, **updates)
    product.update(updates)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: str,
    merchant: dict = Depends(require_active_merchant),
):
    db = get_db()
    product = ProductService.get_by_id(db, product_id)
    if not product or product.get("merchant_id") != merchant["id"]:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")

    ProductService.delete(db, product_id)
    return {"detail": "تم حذف المنتج"}


# ──────────────────── طلبات الاستبدال ────────────────────

@router.get("/redemptions", response_model=list[RedemptionOut])
def list_redemptions(merchant: dict = Depends(require_active_merchant)):
    db = get_db()
    redemptions = RedemptionService.list_by_merchant(db, merchant["id"])
    # إضافة اسم العميل
    for r in redemptions:
        cust = CustomerService.get_by_id(db, r["customer_id"])
        r["customer_name"] = cust["name"] if cust else "غير معروف"
    return redemptions


@router.patch("/redemptions/{redemption_id}")
def update_redemption(
    redemption_id: str,
    body: RedemptionActionRequest,
    merchant: dict = Depends(require_active_merchant),
):
    db = get_db()
    redemption = RedemptionService.get_by_id(db, redemption_id)
    if not redemption or redemption.get("merchant_id") != merchant["id"]:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    if redemption["status"] != "pending":
        raise HTTPException(status_code=400, detail="لا يمكن تعديل هذا الطلب")

    # إذا رفض → أرجع النقاط للعميل
    if body.action == "reject":
        customer = CustomerService.get_by_id(db, redemption["customer_id"])
        if customer:
            new_balance = customer.get("points_balance", 0) + redemption["points_spent"]
            CustomerService.update_balance(db, redemption["customer_id"], new_balance)

            # إرسال إشعار بالإيميل للعميل
            customer_email = customer.get("email")
            if customer_email:
                merchant_data = MerchantService.get_by_id(db, merchant["id"])
                store_name = merchant_data.get("store_name", "المتجر") if merchant_data else "المتجر"
                send_redemption_rejected_email(
                    customer_email, store_name,
                    redemption.get("product_name", "منتج"),
                    redemption["points_spent"], new_balance,
                )

    status_map = {"approve": "approved", "reject": "rejected"}
    RedemptionService.update_status(db, redemption_id, status_map[body.action])
    return {"detail": "تم تحديث حالة الطلب"}
