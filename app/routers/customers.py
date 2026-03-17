"""
نقاط النهاية الخاصة بإدارة العملاء - إضافة وعرض والبحث
كل تاجر يرى عملائه فقط (Multi-Tenant)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.dependencies import require_active_merchant
from app.models import MerchantProfile, Customer
from app.schemas import CustomerCreateRequest, CustomerOut

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("/", response_model=CustomerOut, status_code=201)
def add_customer(
    body: CustomerCreateRequest,
    merchant: MerchantProfile = Depends(require_active_merchant),
    db: Session = Depends(get_db),
):
    """إضافة عميل جديد لمتجر التاجر"""

    # التحقق من عدم تكرار العميل (بنفس الإيميل أو الجوال لنفس التاجر)
    if body.email or body.phone:
        existing = db.query(Customer).filter(
            Customer.merchant_id == merchant.id
        )
        conditions = []
        if body.email:
            conditions.append(Customer.email == body.email)
        if body.phone:
            conditions.append(Customer.phone == body.phone)
        existing = existing.filter(or_(*conditions)).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="عميل بنفس البريد أو رقم الجوال موجود مسبقاً",
            )

    customer = Customer(
        merchant_id=merchant.id,
        name=body.name,
        email=body.email,
        phone=body.phone,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=list[CustomerOut])
def list_customers(
    merchant: MerchantProfile = Depends(require_active_merchant),
    db: Session = Depends(get_db),
):
    """عرض جميع عملاء التاجر"""
    customers = (
        db.query(Customer)
        .filter(Customer.merchant_id == merchant.id)
        .order_by(Customer.created_at.desc())
        .all()
    )
    return customers


@router.get("/search", response_model=list[CustomerOut])
def search_customers(
    q: str = Query(..., min_length=1, description="بحث بالإيميل أو رقم الجوال أو الاسم"),
    merchant: MerchantProfile = Depends(require_active_merchant),
    db: Session = Depends(get_db),
):
    """البحث عن عميل بالإيميل أو رقم الجوال أو الاسم"""
    pattern = f"%{q}%"
    customers = (
        db.query(Customer)
        .filter(
            Customer.merchant_id == merchant.id,
            or_(
                Customer.email.ilike(pattern),
                Customer.phone.ilike(pattern),
                Customer.name.ilike(pattern),
            ),
        )
        .all()
    )
    return customers


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    merchant: MerchantProfile = Depends(require_active_merchant),
    db: Session = Depends(get_db),
):
    """عرض بيانات عميل محدد"""
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.merchant_id == merchant.id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return customer
