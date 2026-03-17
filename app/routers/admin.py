"""
نقاط النهاية الخاصة بالمدير (Super Admin)
- عرض التجار والموافقة/الرفض/التعليق
- إحصائيات عامة
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.dependencies import require_admin
from app.models import MerchantService, CustomerService, PointsService, utcnow_str
from app.schemas import MerchantApprovalRequest, AdminStatsOut

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/merchants")
def list_merchants(
    status: str | None = Query(None, description="فلترة بالحالة: pending, active, rejected, suspended"),
    _admin: dict = Depends(require_admin),
):
    """عرض جميع التجار مع إمكانية الفلترة بالحالة"""
    db = get_db()
    valid_statuses = {"pending", "active", "rejected", "suspended"}

    if status and status not in valid_statuses:
        raise HTTPException(status_code=400, detail="حالة غير صالحة")

    merchants = MerchantService.list_all(db, status=status)
    return merchants


@router.patch("/merchants/{merchant_id}")
def update_merchant_status(
    merchant_id: str,
    body: MerchantApprovalRequest,
    _admin: dict = Depends(require_admin),
):
    """موافقة أو رفض أو تعليق تاجر"""
    db = get_db()
    merchant = MerchantService.get_by_id(db, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="التاجر غير موجود")

    action_map = {
        "approve": "active",
        "reject": "rejected",
        "suspend": "suspended",
    }
    new_status = action_map[body.action]
    approved_at = utcnow_str() if body.action == "approve" else None
    MerchantService.update_status(db, merchant_id, new_status, approved_at)

    return {"message": f"تم تحديث حالة التاجر إلى: {new_status}"}


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(_admin: dict = Depends(require_admin)):
    """إحصائيات عامة للمدير"""
    db = get_db()

    all_merchants = MerchantService.list_all(db)
    total_merchants = len(all_merchants)
    active_merchants = sum(1 for m in all_merchants if m.get("status") == "active")
    pending_merchants = sum(1 for m in all_merchants if m.get("status") == "pending")

    all_customers = list(db.collection("customers").stream())
    total_customers = len(all_customers)

    total_issued = PointsService.sum_added(db)

    return AdminStatsOut(
        total_merchants=total_merchants,
        active_merchants=active_merchants,
        pending_merchants=pending_merchants,
        total_customers=total_customers,
        total_points_issued=total_issued,
    )
