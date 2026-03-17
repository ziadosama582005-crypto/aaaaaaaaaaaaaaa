"""
نقاط النهاية الخاصة بالتاجر - التسجيل وتسجيل الدخول والبيانات الشخصية
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token
from app.models import UserService, MerchantService
from app.schemas import MerchantRegisterRequest, LoginRequest, TokenResponse, MerchantSettingsRequest
from app.dependencies import get_current_user, require_active_merchant
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=201)
@limiter.limit("5/minute")
def register_merchant(request: Request, body: MerchantRegisterRequest):
    """تسجيل تاجر جديد - الحساب يكون بحالة (قيد الانتظار) حتى موافقة المدير"""
    db = get_db()

    if UserService.get_by_email(db, body.email):
        raise HTTPException(status_code=409, detail="البريد الإلكتروني مسجل مسبقاً")

    user = UserService.create(
        db,
        email=body.email,
        hashed_password=hash_password(body.password),
        role="merchant",
    )

    profile = MerchantService.create(
        db,
        user_id=user["id"],
        store_name=body.store_name,
        address=body.address,
        phone=body.phone,
        email=body.email,
    )

    return {
        "message": "تم التسجيل بنجاح. حسابك قيد المراجعة من الإدارة.",
        "merchant_id": profile["id"],
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest):
    """تسجيل دخول (مدير أو تاجر) - يُرجع JWT Token"""
    db = get_db()

    user = UserService.get_by_email(db, body.email)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="بريد إلكتروني أو كلمة مرور خاطئة")

    if not user.get("is_active", False):
        raise HTTPException(status_code=403, detail="الحساب معطل")

    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return TokenResponse(access_token=token)


@router.get("/me")
def get_my_profile(user: dict = Depends(get_current_user)):
    """عرض بيانات المستخدم الحالي"""
    data = {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
    }

    if user["role"] == "merchant":
        db = get_db()
        profile = MerchantService.get_by_user_id(db, user["id"])
        if profile:
            data["merchant"] = {
                "id": profile["id"],
                "store_name": profile["store_name"],
                "address": profile.get("address"),
                "phone": profile.get("phone"),
                "status": profile["status"],
                "short_code": profile.get("short_code"),
                "theme_color": profile.get("theme_color", "#ffa502"),
                "store_description": profile.get("store_description"),
                "logo_url": profile.get("logo_url"),
                "tiers": profile.get("tiers"),
            }

    return data


@router.put("/settings")
def update_merchant_settings(
    body: MerchantSettingsRequest,
    merchant: dict = Depends(require_active_merchant),
):
    """تحديث إعدادات المتجر (الوصف، الشعار، اللون)"""
    db = get_db()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")
    MerchantService.update(db, merchant["id"], **updates)
    return {"detail": "تم تحديث الإعدادات"}
