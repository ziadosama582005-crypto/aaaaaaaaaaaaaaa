"""
نقاط النهاية الخاصة بإدارة النقاط - إضافة وخصم وعرض السجل
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_active_merchant
from app.models import MerchantProfile, Customer, PointsTransaction, PointsAction
from app.schemas import PointsRequest, PointsTransactionOut

router = APIRouter(prefix="/api/points", tags=["Points"])


@router.post("/", response_model=PointsTransactionOut, status_code=201)
def manage_points(
    body: PointsRequest,
    merchant: MerchantProfile = Depends(require_active_merchant),
    db: Session = Depends(get_db),
):
    """إضافة أو خصم نقاط لعميل - يجب أن يكون العميل تابعاً للتاجر"""

    # التأكد أن العميل تابع لهذا التاجر
    customer = (
        db.query(Customer)
        .filter(Customer.id == body.customer_id, Customer.merchant_id == merchant.id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود أو لا يتبع متجرك")

    action = PointsAction(body.action)

    # التحقق من كفاية الرصيد عند الخصم
    if action == PointsAction.DEDUCT:
        if customer.points_balance < body.amount:
            raise HTTPException(
                status_code=400,
                detail=f"رصيد العميل غير كافٍ. الرصيد الحالي: {customer.points_balance}",
            )
        customer.points_balance -= body.amount
    else:
        customer.points_balance += body.amount

    # تسجيل الحركة
    transaction = PointsTransaction(
        customer_id=customer.id,
        merchant_id=merchant.id,
        action=action,
        amount=body.amount,
        balance_after=customer.points_balance,
        note=body.note,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/history/{customer_id}", response_model=list[PointsTransactionOut])
def get_points_history(
    customer_id: str,
    limit: int = Query(50, ge=1, le=200),
    merchant: MerchantProfile = Depends(require_active_merchant),
    db: Session = Depends(get_db),
):
    """عرض سجل حركات النقاط لعميل محدد"""

    # التأكد أن العميل تابع للتاجر
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.merchant_id == merchant.id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود أو لا يتبع متجرك")

    history = (
        db.query(PointsTransaction)
        .filter(PointsTransaction.customer_id == customer_id)
        .order_by(PointsTransaction.created_at.desc())
        .limit(limit)
        .all()
    )
    return history


@router.get("/balance/{customer_id}")
def get_customer_balance(
    customer_id: str,
    merchant: MerchantProfile = Depends(require_active_merchant),
    db: Session = Depends(get_db),
):
    """عرض رصيد النقاط الحالي لعميل"""
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.merchant_id == merchant.id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")

    return {
        "customer_id": customer.id,
        "name": customer.name,
        "points_balance": customer.points_balance,
    }
