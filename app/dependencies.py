"""
Dependencies - استخراج المستخدم الحالي والتحقق من الصلاحيات
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db
from app.auth import decode_access_token
from app.models import UserService, MerchantService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """استخراج المستخدم من JWT - يُرمى 401 إذا كان التوكن غير صالح"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز الدخول غير صالح أو منتهي",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="رمز دخول غير صالح")

    db = get_db()
    user = UserService.get_by_id(db, user_id)
    if user is None or not user.get("is_active", False):
        raise HTTPException(status_code=401, detail="المستخدم غير موجود أو معطل")
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """يسمح فقط بمرور المدير (Super Admin)"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="صلاحيات المدير مطلوبة")
    return user


def require_active_merchant(
    user: dict = Depends(get_current_user),
) -> dict:
    """يسمح فقط بمرور تاجر مفعّل - يُرجع بيانات التاجر"""
    if user.get("role") != "merchant":
        raise HTTPException(status_code=403, detail="صلاحيات التاجر مطلوبة")

    db = get_db()
    profile = MerchantService.get_by_user_id(db, user["id"])
    if profile is None or profile.get("status") != "active":
        raise HTTPException(
            status_code=403,
            detail="حساب التاجر غير مفعّل بعد أو معلّق",
        )
    return profile
