"""
خدمة Firestore - عمليات CRUD على المجموعات
Collections: users, merchants, customers, points_transactions
"""

import uuid
from datetime import datetime, timezone


def generate_id() -> str:
    return str(uuid.uuid4())


def utcnow_str() -> str:
    return datetime.now(timezone.utc).isoformat()


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
            .where("email", "==", email)
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
        data = {
            "user_id": user_id,
            "store_name": store_name,
            "address": address,
            "phone": phone,
            "email": email,
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
    def get_by_user_id(db, user_id: str) -> dict | None:
        docs = (
            db.collection(MerchantService.COLLECTION)
            .where("user_id", "==", user_id)
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
            query = query.where("status", "==", status)
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
            .where("merchant_id", "==", merchant_id)
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
            docs = col.where("merchant_id", "==", merchant_id).where("email", "==", email).limit(1).stream()
            for doc in docs:
                return {"id": doc.id, **doc.to_dict()}
        if phone:
            docs = col.where("merchant_id", "==", merchant_id).where("phone", "==", phone).limit(1).stream()
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
            .where("customer_id", "==", customer_id)
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
            .where("action", "==", "add")
            .stream()
        )
        total = 0.0
        for doc in docs:
            total += doc.to_dict().get("amount", 0.0)
        return total
