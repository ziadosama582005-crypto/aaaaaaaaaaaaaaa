"""
نقاط النهاية الخاصة بإدارة العملاء - إضافة وعرض والبحث
كل تاجر يرى عملائه فقط (Multi-Tenant)
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.dependencies import require_active_merchant
from app.models import CustomerService
from app.schemas import CustomerCreateRequest, CustomerOut

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("/", response_model=CustomerOut, status_code=201)
def add_customer(
    body: CustomerCreateRequest,
    merchant: dict = Depends(require_active_merchant),
):
    """إضافة عميل جديد لمتجر التاجر"""
    db = get_db()

    if body.email or body.phone:
        existing = CustomerService.find_duplicate(
            db, merchant["id"], email=body.email, phone=body.phone
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="عميل بنفس البريد أو رقم الجوال موجود مسبقاً",
            )

    customer = CustomerService.create(
        db,
        merchant_id=merchant["id"],
        name=body.name,
        email=body.email,
        phone=body.phone,
    )
    return customer


@router.get("/", response_model=list[CustomerOut])
def list_customers(merchant: dict = Depends(require_active_merchant)):
    """عرض جميع عملاء التاجر"""
    db = get_db()
    return CustomerService.list_by_merchant(db, merchant["id"])


@router.get("/search", response_model=list[CustomerOut])
def search_customers(
    q: str = Query(..., min_length=1, description="بحث بالإيميل أو رقم الجوال أو الاسم"),
    merchant: dict = Depends(require_active_merchant),
):
    """البحث عن عميل بالإيميل أو رقم الجوال أو الاسم"""
    db = get_db()
    return CustomerService.search(db, merchant["id"], q)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    merchant: dict = Depends(require_active_merchant),
):
    """عرض بيانات عميل محدد"""
    db = get_db()
    customer = CustomerService.get_by_id(db, customer_id)
    if not customer or customer.get("merchant_id") != merchant["id"]:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return customer
