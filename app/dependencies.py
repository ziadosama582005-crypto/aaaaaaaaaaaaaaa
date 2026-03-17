"""
Dependencies - استخراج المستخدم الحالي والتحقق من الصلاحيات
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import decode_access_token
from app.models import User, UserRole, MerchantProfile, MerchantStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
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

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود أو معطل")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """يسمح فقط بمرور المدير (Super Admin)"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="صلاحيات المدير مطلوبة")
    return user


def require_active_merchant(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MerchantProfile:
    """يسمح فقط بمرور تاجر مفعّل - يُرجع بيانات التاجر"""
    if user.role != UserRole.MERCHANT:
        raise HTTPException(status_code=403, detail="صلاحيات التاجر مطلوبة")

    profile = (
        db.query(MerchantProfile)
        .filter(MerchantProfile.user_id == user.id)
        .first()
    )
    if profile is None or profile.status != MerchantStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="حساب التاجر غير مفعّل بعد أو معلّق",
        )
    return profile
