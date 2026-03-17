"""
نقطة الدخول الرئيسية لتطبيق Loyalty Points System
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, SessionLocal
from app.models import User, UserRole
from app.auth import hash_password
from app.routers import admin, merchants, customers, points

settings = get_settings()


def seed_admin():
    """إنشاء حساب المدير الافتراضي إذا لم يكن موجوداً"""
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not exists:
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            print(f"✅ تم إنشاء حساب المدير: {settings.ADMIN_EMAIL}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # عند بدء التشغيل
    init_db()
    seed_admin()
    print("🚀 النظام جاهز للعمل")
    yield
    # عند الإيقاف
    print("👋 تم إيقاف النظام")


app = FastAPI(
    title=settings.APP_NAME,
    description="نظام نقاط ولاء متعدد التجار - Multi-Tenant Loyalty Points System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - السماح بالطلبات من أي مصدر (يُعدّل في الإنتاج)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تسجيل الراوترات
app.include_router(merchants.router)
app.include_router(admin.router)
app.include_router(customers.router)
app.include_router(points.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "running",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
