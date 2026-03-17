"""
مخططات Pydantic - التحقق من المدخلات وتنسيق المخرجات
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


def validate_gmail(email: str) -> str:
    if not email.lower().endswith('@gmail.com'):
        raise ValueError('يجب أن ينتهي البريد بـ @gmail.com')
    return email.lower()


# ──────────────────────── Auth ────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email')
    @classmethod
    def check_gmail(cls, v):
        return validate_gmail(v)


# ──────────────────────── Merchant ────────────────────────

class MerchantRegisterRequest(BaseModel):
    store_name: str = Field(..., min_length=2, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: EmailStr
    password: str = Field(..., min_length=6)

    @field_validator('email')
    @classmethod
    def check_gmail(cls, v):
        return validate_gmail(v)


class MerchantOut(BaseModel):
    id: str
    store_name: str
    address: Optional[str]
    phone: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MerchantWithEmail(MerchantOut):
    email: str  # من جدول users


# ──────────────────────── Customer ────────────────────────

class CustomerCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @field_validator('email')
    @classmethod
    def check_gmail(cls, v):
        if v is None:
            return v
        return validate_gmail(v)


class CustomerOut(BaseModel):
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    points_balance: float
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerSearch(BaseModel):
    query: str = Field(..., min_length=1, description="بحث بالإيميل أو رقم الجوال")


# ──────────────────────── Points ────────────────────────

class PointsRequest(BaseModel):
    customer_id: str
    action: str = Field(..., pattern="^(add|deduct)$")
    amount: float = Field(..., gt=0)
    note: Optional[str] = None


class PointsTransactionOut(BaseModel):
    id: str
    customer_id: str
    action: str
    amount: float
    balance_after: float
    note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────── Admin ────────────────────────

class MerchantApprovalRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|suspend)$")


class AdminStatsOut(BaseModel):
    total_merchants: int
    active_merchants: int
    pending_merchants: int
    total_customers: int
    total_points_issued: float
