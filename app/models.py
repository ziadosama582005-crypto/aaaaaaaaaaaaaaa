"""
خدمة Firestore - عمليات CRUD على المجموعات
Collections: users, merchants, customers, points_transactions, products, redemptions, verification_codes
"""

import uuid
from datetime import datetime, timezone

from google.cloud.firestore_v1.base_query import FieldFilter


def generate_id() -> str:
    return str(uuid.uuid4())


def utcnow_str() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_short_code(db) -> str:
    """Generate next short code like A1/0001, A1/0002, ..., A1/9999, A2/0001, ..."""
    counter_ref = db.collection("counters").document("merchant_code")
    doc = counter_ref.get()
    if doc.exists:
        num = doc.to_dict().get("value", 0) + 1
    else:
        num = 1
    counter_ref.set({"value": num})

    prefix_num = (num - 1) // 9999
    seq = ((num - 1) % 9999) + 1
    letter = chr(ord('A') + prefix_num // 9)
    digit = (prefix_num % 9) + 1
    return f"{letter}{digit}/{seq:04d}"


# ═══════════════════════ Users ═══════════════════════

class UserService:
    COLLECTION = "users"

    @staticmethod
    def create(db, *, email: str, hashed_password: str, role: str, is_active: bool = True) -> dict:
        uid = generate_id()
        data = {
            "email": email,
            "hashed_password": hashed_password,
            "role": role,
            "is_active": is_active,
            "created_at": utcnow_str(),
        }
        db.collection(UserService.COLLECTION).document(uid).set(data)
        data["id"] = uid
        return data

    @staticmethod
    def get_by_id(db, user_id: str) -> dict | None:
        doc = db.collection(UserService.COLLECTION).document(user_id).get()
        if doc.exists:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    @staticmethod
    def get_by_email(db, email: str) -> dict | None:
        docs = (
            db.collection(UserService.COLLECTION)
            .where(filter=FieldFilter("email", "==", email))
            .limit(1)
            .stream()
        )
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None


# ═══════════════════════ Merchants ═══════════════════════

class MerchantService:
    COLLECTION = "merchants"

    @staticmethod
    def create(db, *, user_id: str, store_name: str, address: str = None,
               phone: str = None, email: str = "") -> dict:
        mid = generate_id()
        short_code = _next_short_code(db)
        data = {
            "user_id": user_id,
            "store_name": store_name,
            "address": address,
            "phone": phone,
            "email": email,
            "short_code": short_code,
            "status": "pending",
            "approved_at": None,
            "created_at": utcnow_str(),
        }
        db.collection(MerchantService.COLLECTION).document(mid).set(data)
        data["id"] = mid
        return data

    @staticmethod
    def get_by_id(db, merchant_id: str) -> dict | None:
        doc = db.collection(MerchantService.COLLECTION).document(merchant_id).get()
        if doc.exists:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    @staticmethod
    def get_by_short_code(db, short_code: str) -> dict | None:
        docs = (
            db.collection(MerchantService.COLLECTION)
            .where(filter=FieldFilter("short_code", "==", short_code))
            .limit(1)
            .stream()
        )
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    @staticmethod
    def get_by_user_id(db, user_id: str) -> dict | None:
        docs = (
            db.collection(MerchantService.COLLECTION)
            .where(filter=FieldFilter("user_id", "==", user_id))
            .limit(1)
            .stream()
        )
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    @staticmethod
    def list_all(db, status: str = None) -> list[dict]:
        query = db.collection(MerchantService.COLLECTION)
        if status:
            query = query.where(filter=FieldFilter("status", "==", status))
        docs = query.stream()
        result = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            result.append(d)
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    @staticmethod
    def update_status(db, merchant_id: str, status: str, approved_at: str = None):
        update = {"status": status}
        if approved_at:
            update["approved_at"] = approved_at
        db.collection(MerchantService.COLLECTION).document(merchant_id).update(update)

    @staticmethod
    def update(db, merchant_id: str, **fields):
        db.collection(MerchantService.COLLECTION).document(merchant_id).update(fields)


# ═══════════════════════ Customers ═══════════════════════

class CustomerService:
    COLLECTION = "customers"

    @staticmethod
    def create(db, *, merchant_id: str, name: str,
               email: str = None, phone: str = None) -> dict:
        cid = generate_id()
        data = {
            "merchant_id": merchant_id,
            "name": name,
            "email": email,
            "phone": phone,
            "points_balance": 0.0,
            "created_at": utcnow_str(),
        }
        db.collection(CustomerService.COLLECTION).document(cid).set(data)
        data["id"] = cid
        return data

    @staticmethod
    def get_by_id(db, customer_id: str) -> dict | None:
        doc = db.collection(CustomerService.COLLECTION).document(customer_id).get()
        if doc.exists:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    @staticmethod
    def list_by_merchant(db, merchant_id: str) -> list[dict]:
        docs = (
            db.collection(CustomerService.COLLECTION)
            .where(filter=FieldFilter("merchant_id", "==", merchant_id))
            .stream()
        )
        result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    @staticmethod
    def find_duplicate(db, merchant_id: str, email: str = None, phone: str = None) -> dict | None:
        """البحث عن عميل مكرر بنفس الإيميل أو الجوال لنفس التاجر"""
        col = db.collection(CustomerService.COLLECTION)
        if email:
            docs = col.where(filter=FieldFilter("merchant_id", "==", merchant_id)).where(filter=FieldFilter("email", "==", email)).limit(1).stream()
            for doc in docs:
                return {"id": doc.id, **doc.to_dict()}
        if phone:
            docs = col.where(filter=FieldFilter("merchant_id", "==", merchant_id)).where(filter=FieldFilter("phone", "==", phone)).limit(1).stream()
            for doc in docs:
                return {"id": doc.id, **doc.to_dict()}
        return None

    @staticmethod
    def search(db, merchant_id: str, query: str) -> list[dict]:
        """البحث في عملاء التاجر - بالاسم أو الإيميل أو الجوال"""
        all_customers = CustomerService.list_by_merchant(db, merchant_id)
        q = query.lower()
        return [
            c for c in all_customers
            if q in (c.get("name") or "").lower()
            or q in (c.get("email") or "").lower()
            or q in (c.get("phone") or "")
        ]

    @staticmethod
    def update_balance(db, customer_id: str, new_balance: float):
        db.collection(CustomerService.COLLECTION).document(customer_id).update({
            "points_balance": new_balance
        })

    @staticmethod
    def update_total_earned(db, customer_id: str, total_earned: float):
        db.collection(CustomerService.COLLECTION).document(customer_id).update({
            "total_earned": total_earned
        })


# ═══════════════════════ Points Transactions ═══════════════════════

class PointsService:
    COLLECTION = "points_transactions"

    @staticmethod
    def create(db, *, customer_id: str, merchant_id: str, action: str,
               amount: float, balance_after: float, note: str = None) -> dict:
        tid = generate_id()
        data = {
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "action": action,
            "amount": amount,
            "balance_after": balance_after,
            "note": note,
            "created_at": utcnow_str(),
        }
        db.collection(PointsService.COLLECTION).document(tid).set(data)
        data["id"] = tid
        return data

    @staticmethod
    def get_history(db, customer_id: str, limit: int = 50) -> list[dict]:
        docs = (
            db.collection(PointsService.COLLECTION)
            .where(filter=FieldFilter("customer_id", "==", customer_id))
            .stream()
        )
        result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result[:limit]

    @staticmethod
    def sum_added(db) -> float:
        """مجموع النقاط المضافة (للإحصائيات)"""
        docs = (
            db.collection(PointsService.COLLECTION)
            .where(filter=FieldFilter("action", "==", "add"))
            .stream()
        )
        total = 0.0
        for doc in docs:
            total += doc.to_dict().get("amount", 0.0)
        return total


# ═══════════════════════ Products ═══════════════════════

class ProductService:
    COLLECTION = "products"

    @staticmethod
    def create(db, *, merchant_id: str, name: str, description: str = None,
               image_url: str = None, points_cost: float, stock: int = -1,
               category: str = None, product_type: str = "normal",
               required_fields: list = None) -> dict:
        pid = generate_id()
        data = {
            "merchant_id": merchant_id,
            "name": name,
            "description": description,
            "image_url": image_url,
            "points_cost": points_cost,
            "stock": stock,
            "category": category,
            "product_type": product_type,
            "required_fields": required_fields,
            "is_active": True,
            "created_at": utcnow_str(),
        }
        db.collection(ProductService.COLLECTION).document(pid).set(data)
        data["id"] = pid
        return data

    @staticmethod
    def get_by_id(db, product_id: str) -> dict | None:
        doc = db.collection(ProductService.COLLECTION).document(product_id).get()
        if doc.exists:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    @staticmethod
    def list_by_merchant(db, merchant_id: str, active_only: bool = False) -> list[dict]:
        query = db.collection(ProductService.COLLECTION).where(filter=FieldFilter("merchant_id", "==", merchant_id))
        docs = query.stream()
        result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        if active_only:
            result = [p for p in result if p.get("is_active", True)]
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    @staticmethod
    def update(db, product_id: str, **fields):
        db.collection(ProductService.COLLECTION).document(product_id).update(fields)

    @staticmethod
    def delete(db, product_id: str):
        db.collection(ProductService.COLLECTION).document(product_id).delete()


# ═══════════════════════ Redemptions ═══════════════════════

class RedemptionService:
    COLLECTION = "redemptions"

    @staticmethod
    def create(db, *, customer_id: str, merchant_id: str, product_id: str,
               product_name: str, points_spent: float, customer_notes: str = None) -> dict:
        rid = generate_id()
        data = {
            "customer_id": customer_id,
            "merchant_id": merchant_id,
            "product_id": product_id,
            "product_name": product_name,
            "points_spent": points_spent,
            "customer_notes": customer_notes,
            "status": "pending",
            "created_at": utcnow_str(),
        }
        db.collection(RedemptionService.COLLECTION).document(rid).set(data)
        data["id"] = rid
        return data

    @staticmethod
    def list_by_merchant(db, merchant_id: str) -> list[dict]:
        docs = db.collection(RedemptionService.COLLECTION).where(filter=FieldFilter("merchant_id", "==", merchant_id)).stream()
        result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    @staticmethod
    def list_by_customer(db, customer_id: str) -> list[dict]:
        docs = db.collection(RedemptionService.COLLECTION).where(filter=FieldFilter("customer_id", "==", customer_id)).stream()
        result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    @staticmethod
    def update_status(db, redemption_id: str, status: str):
        db.collection(RedemptionService.COLLECTION).document(redemption_id).update({"status": status})

    @staticmethod
    def get_by_id(db, redemption_id: str) -> dict | None:
        doc = db.collection(RedemptionService.COLLECTION).document(redemption_id).get()
        if doc.exists:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None


# ═══════════════════════ Verification Codes ═══════════════════════

class VerificationCodeService:
    COLLECTION = "verification_codes"

    @staticmethod
    def create(db, *, email: str, code: str, merchant_id: str) -> dict:
        vid = generate_id()
        data = {
            "email": email,
            "code": code,
            "merchant_id": merchant_id,
            "used": False,
            "created_at": utcnow_str(),
        }
        db.collection(VerificationCodeService.COLLECTION).document(vid).set(data)
        data["id"] = vid
        return data

    @staticmethod
    def get_latest(db, email: str, merchant_id: str) -> dict | None:
        docs = (
            db.collection(VerificationCodeService.COLLECTION)
            .where(filter=FieldFilter("email", "==", email))
            .where(filter=FieldFilter("merchant_id", "==", merchant_id))
            .where(filter=FieldFilter("used", "==", False))
            .stream()
        )
        result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        if not result:
            return None
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result[0]

    @staticmethod
    def mark_used(db, code_id: str):
        db.collection(VerificationCodeService.COLLECTION).document(code_id).update({"used": True})
