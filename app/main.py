"""
نقطة الدخول الرئيسية لتطبيق Loyalty Points System
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response

from app.config import get_settings
from app.database import init_firebase, get_db
from app.models import UserService, MerchantService
from app.auth import hash_password
from app.routers import admin, merchants, customers, points, products, store

settings = get_settings()


def seed_admin():
    """إنشاء حساب المدير الافتراضي إذا لم يكن موجوداً"""
    db = get_db()
    existing = UserService.get_by_email(db, settings.ADMIN_EMAIL)
    if not existing:
        UserService.create(
            db,
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
        )
        print(f"✅ تم إنشاء حساب المدير: {settings.ADMIN_EMAIL}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # عند بدء التشغيل
    try:
        init_firebase()
        print("✅ Firebase متصل")
        seed_admin()
        print("🚀 النظام جاهز للعمل")
    except Exception as e:
        print(f"❌ خطأ في التشغيل: {e}")
        raise
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
app.include_router(products.router)
app.include_router(store.router)

# خدمة الملفات الثابتة (الواجهة)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["Health"])
def root():
    return RedirectResponse(url="/static/login.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="80" font-size="80">⭐</text></svg>'
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}


@app.get("/s/{short_code:path}", tags=["Store"])
def resolve_short_code(short_code: str):
    """تحويل الرابط القصير إلى صفحة المتجر"""
    db = get_db()
    merchant = MerchantService.get_by_short_code(db, short_code)
    if not merchant:
        raise HTTPException(status_code=404, detail="المتجر غير موجود")
    return RedirectResponse(url=f"/static/store.html?merchant={merchant['id']}")
