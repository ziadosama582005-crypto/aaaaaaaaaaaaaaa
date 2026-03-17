"""
نقاط النهاية الخاصة بالتاجر - التسجيل وتسجيل الدخول والبيانات الشخصية
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token
from app.models import User, UserRole, MerchantProfile
from app.schemas import (
    MerchantRegisterRequest, LoginRequest,
    TokenResponse, MerchantOut,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register_merchant(body: MerchantRegisterRequest, db: Session = Depends(get_db)):
    """تسجيل تاجر جديد - الحساب يكون بحالة (قيد الانتظار) حتى موافقة المدير"""

    # التحقق من عدم وجود بريد مسجل مسبقاً
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="البريد الإلكتروني مسجل مسبقاً")

    # إنشاء المستخدم
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        role=UserRole.MERCHANT,
    )
    db.add(user)
    db.flush()  # للحصول على user.id

    # إنشاء بيانات التاجر
    profile = MerchantProfile(
        user_id=user.id,
        store_name=body.store_name,
        address=body.address,
        phone=body.phone,
    )
    db.add(profile)
    db.commit()

    return {
        "message": "تم التسجيل بنجاح. حسابك قيد المراجعة من الإدارة.",
        "merchant_id": profile.id,
    }


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """تسجيل دخول (مدير أو تاجر) - يُرجع JWT Token"""

    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="بريد إلكتروني أو كلمة مرور خاطئة")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="الحساب معطل")

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(access_token=token)


@router.get("/me")
def get_my_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """عرض بيانات المستخدم الحالي"""
    data = {
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
    }

    if user.role == UserRole.MERCHANT:
        profile = (
            db.query(MerchantProfile)
            .filter(MerchantProfile.user_id == user.id)
            .first()
        )
        if profile:
            data["merchant"] = {
                "id": profile.id,
                "store_name": profile.store_name,
                "address": profile.address,
                "phone": profile.phone,
                "status": profile.status.value,
            }

    return data
