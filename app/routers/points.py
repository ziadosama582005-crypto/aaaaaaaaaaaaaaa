"""
نقاط النهاية الخاصة بإدارة النقاط - إضافة وخصم وعرض السجل
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.dependencies import require_active_merchant
from app.models import CustomerService, PointsService, MerchantService
from app.schemas import PointsRequest, PointsTransactionOut
from app.email_service import send_points_added_email, send_points_deducted_email

router = APIRouter(prefix="/api/points", tags=["Points"])


@router.post("/", response_model=PointsTransactionOut, status_code=201)
def manage_points(
    body: PointsRequest,
    merchant: dict = Depends(require_active_merchant),
):
    """إضافة أو خصم نقاط لعميل - يجب أن يكون العميل تابعاً للتاجر"""
    db = get_db()

    customer = CustomerService.get_by_id(db, body.customer_id)
    if not customer or customer.get("merchant_id") != merchant["id"]:
        raise HTTPException(status_code=404, detail="العميل غير موجود أو لا يتبع متجرك")

    balance = customer.get("points_balance", 0.0)

    if body.action == "deduct":
        if balance < body.amount:
            raise HTTPException(
                status_code=400,
                detail=f"رصيد العميل غير كافٍ. الرصيد الحالي: {balance}",
            )
        new_balance = balance - body.amount
    else:
        new_balance = balance + body.amount

    # تحديث الرصيد
    CustomerService.update_balance(db, body.customer_id, new_balance)

    # تسجيل الحركة
    transaction = PointsService.create(
        db,
        customer_id=body.customer_id,
        merchant_id=merchant["id"],
        action=body.action,
        amount=body.amount,
        balance_after=new_balance,
        note=body.note,
    )

    # إرسال إشعار بالإيميل للعميل
    customer_email = customer.get("email")
    if customer_email:
        merchant_data = MerchantService.get_by_id(db, merchant["id"])
        store_name = merchant_data.get("store_name", "المتجر") if merchant_data else "المتجر"
        if body.action == "add":
            send_points_added_email(customer_email, store_name, body.amount, new_balance, body.note)
        else:
            send_points_deducted_email(customer_email, store_name, body.amount, new_balance, body.note)

    return transaction


@router.get("/history/{customer_id}", response_model=list[PointsTransactionOut])
def get_points_history(
    customer_id: str,
    limit: int = Query(50, ge=1, le=200),
    merchant: dict = Depends(require_active_merchant),
):
    """عرض سجل حركات النقاط لعميل محدد"""
    db = get_db()

    customer = CustomerService.get_by_id(db, customer_id)
    if not customer or customer.get("merchant_id") != merchant["id"]:
        raise HTTPException(status_code=404, detail="العميل غير موجود أو لا يتبع متجرك")

    return PointsService.get_history(db, customer_id, limit)


@router.get("/balance/{customer_id}")
def get_customer_balance(
    customer_id: str,
    merchant: dict = Depends(require_active_merchant),
):
    """عرض رصيد النقاط الحالي لعميل"""
    db = get_db()

    customer = CustomerService.get_by_id(db, customer_id)
    if not customer or customer.get("merchant_id") != merchant["id"]:
        raise HTTPException(status_code=404, detail="العميل غير موجود")

    return {
        "customer_id": customer["id"],
        "name": customer["name"],
        "points_balance": customer.get("points_balance", 0.0),
    }
