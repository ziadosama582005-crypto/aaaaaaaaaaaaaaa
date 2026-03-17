"""
نقاط النهاية الخاصة بالمدير (Super Admin)
- عرض التجار والموافقة/الرفض/التعليق
- إحصائيات عامة
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.dependencies import require_admin
from app.models import (
    User, MerchantProfile, MerchantStatus,
    Customer, PointsTransaction, PointsAction,
)
from app.schemas import MerchantApprovalRequest, AdminStatsOut

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/merchants")
def list_merchants(
    status: str | None = Query(None, description="فلترة بالحالة: pending, active, rejected, suspended"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """عرض جميع التجار مع إمكانية الفلترة بالحالة"""
    query = db.query(MerchantProfile).join(User)

    if status:
        try:
            status_enum = MerchantStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="حالة غير صالحة")
        query = query.filter(MerchantProfile.status == status_enum)

    merchants = query.order_by(MerchantProfile.created_at.desc()).all()

    return [
        {
            "id": m.id,
            "store_name": m.store_name,
            "address": m.address,
            "phone": m.phone,
            "email": m.user.email,
            "status": m.status.value,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "approved_at": m.approved_at.isoformat() if m.approved_at else None,
        }
        for m in merchants
    ]


@router.patch("/merchants/{merchant_id}")
def update_merchant_status(
    merchant_id: str,
    body: MerchantApprovalRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """موافقة أو رفض أو تعليق تاجر"""
    merchant = db.query(MerchantProfile).filter(MerchantProfile.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="التاجر غير موجود")

    action_map = {
        "approve": MerchantStatus.ACTIVE,
        "reject": MerchantStatus.REJECTED,
        "suspend": MerchantStatus.SUSPENDED,
    }
    merchant.status = action_map[body.action]
    if body.action == "approve":
        merchant.approved_at = datetime.now(timezone.utc)

    db.commit()
    return {"message": f"تم تحديث حالة التاجر إلى: {merchant.status.value}"}


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """إحصائيات عامة للمدير"""
    total_merchants = db.query(MerchantProfile).count()
    active_merchants = (
        db.query(MerchantProfile)
        .filter(MerchantProfile.status == MerchantStatus.ACTIVE)
        .count()
    )
    pending_merchants = (
        db.query(MerchantProfile)
        .filter(MerchantProfile.status == MerchantStatus.PENDING)
        .count()
    )
    total_customers = db.query(Customer).count()
    total_issued = (
        db.query(func.coalesce(func.sum(PointsTransaction.amount), 0.0))
        .filter(PointsTransaction.action == PointsAction.ADD)
        .scalar()
    )

    return AdminStatsOut(
        total_merchants=total_merchants,
        active_merchants=active_merchants,
        pending_merchants=pending_merchants,
        total_customers=total_customers,
        total_points_issued=float(total_issued),
    )
