"""
نماذج قاعدة البيانات - العلاقات بين المدير والتجار والعملاء والنقاط
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Enum as SAEnum, Text
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# ──────────────────────────── Enums ────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MERCHANT = "merchant"


class MerchantStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class PointsAction(str, enum.Enum):
    ADD = "add"
    DEDUCT = "deduct"


# ──────────────────────────── Helper ────────────────────────────

def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ──────────────────────────── Models ────────────────────────────

class User(Base):
    """
    جدول المستخدمين الموحّد - يشمل المدير والتجار
    التمييز عبر حقل role
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.MERCHANT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    # علاقة واحد-لواحد مع بيانات التاجر
    merchant_profile = relationship(
        "MerchantProfile", back_populates="user", uselist=False
    )


class MerchantProfile(Base):
    """
    بيانات التاجر الإضافية - اسم المتجر، العنوان، حالة الموافقة
    """
    __tablename__ = "merchant_profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    store_name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(
        SAEnum(MerchantStatus), default=MerchantStatus.PENDING, nullable=False
    )
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # العلاقات
    user = relationship("User", back_populates="merchant_profile")
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")


class Customer(Base):
    """
    عميل تابع لتاجر معيّن - كل تاجر يرى عملائه فقط
    """
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(
        String, ForeignKey("merchant_profiles.id"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True, index=True)
    points_balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    # العلاقات
    merchant = relationship("MerchantProfile", back_populates="customers")
    points_history = relationship(
        "PointsTransaction", back_populates="customer", cascade="all, delete-orphan"
    )


class PointsTransaction(Base):
    """
    سجل حركات النقاط - كل عملية إضافة أو خصم
    """
    __tablename__ = "points_transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(
        String, ForeignKey("customers.id"), nullable=False, index=True
    )
    merchant_id = Column(String, nullable=False, index=True)
    action = Column(SAEnum(PointsAction), nullable=False)
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # العلاقة
    customer = relationship("Customer", back_populates="points_history")
