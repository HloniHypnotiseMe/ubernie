#!/usr/bin/env python3
"""Data access layer — atomic writes, fresh reads."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func

from db.engine import SessionLocal
from db.models import (
    Order, Payment, RiderEvent, TaxRecord, WaitlistEntry, Zone,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


import re

def _make_shop_id(business_name: str) -> str:
    """Slugify a business name + 4-char random suffix."""
    import secrets
    slug = re.sub(r"[^a-z0-9]+", "_", business_name.lower()).strip("_")[:32]
    suffix = secrets.token_hex(2)  # 4 chars
    return f"{slug}_{suffix}"



# ---------------------------------------------------------------------------
# Waitlist
# ---------------------------------------------------------------------------
def add_waitlist_entry(**kwargs) -> Dict[str, Any]:
    area_norm = kwargs["area"].strip().lower()
    s = SessionLocal()
    try:
        entry = WaitlistEntry(
            record_type=kwargs["record_type"],
            area=area_norm,
            email=kwargs["email"],
            phone=kwargs["phone"],
            business_name=kwargs.get("business_name"),
            full_name=kwargs.get("full_name"),
            industry=kwargs.get("industry"),
            vehicle=kwargs.get("vehicle"),
            licence_number=kwargs.get("licence_number"),
            estimated_daily_orders=kwargs.get("estimated_daily_orders", 0),
            status="WAITING",
        )
        # The WaitlistEntry model needs a user_id column — add via model
        if kwargs.get("user_id"):
            entry.user_id = kwargs["user_id"]
        s.add(entry)
        s.commit()
        entry_id = entry.id
        return {"id": entry_id, "area": area_norm, "status": "WAITING"}
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def zone_counts(area: str) -> Dict[str, int]:
    area_norm = area.strip().lower()
    s = SessionLocal()
    try:
        shops = s.query(WaitlistEntry).filter_by(area=area_norm, record_type="shop", status="WAITING").count()
        riders = s.query(WaitlistEntry).filter_by(area=area_norm, record_type="rider", status="WAITING").count()
        return {"shops": shops, "riders": riders}
    finally:
        s.close()


def list_zones() -> List[str]:
    s = SessionLocal()
    try:
        rows = s.query(WaitlistEntry.area).distinct().all()
        return sorted({r[0] for r in rows})
    finally:
        s.close()


def get_zone(area: str) -> Optional[Zone]:
    area_norm = area.strip().lower()
    s = SessionLocal()
    try:
        return s.get(Zone, area_norm)
    finally:
        s.close()


def upsert_zone(area: str, shop_count: int, rider_count: int, active: bool) -> Zone:
    area_norm = area.strip().lower()
    s = SessionLocal()
    try:
        z = s.get(Zone, area_norm)
        if z is None:
            z = Zone(area=area_norm, shop_count=shop_count, rider_count=rider_count, active=False)
            s.add(z)
        z.shop_count = shop_count
        z.rider_count = rider_count
        if active and not z.active:
            z.active = True
            z.activated_at = _now()
        z.updated_at = _now()
        s.commit()
        s.refresh(z)
        # Force detached copy so caller sees the values
        result = Zone(area=z.area, shop_count=z.shop_count, rider_count=z.rider_count,
                      active=z.active, activated_at=z.activated_at, updated_at=z.updated_at)
        return result
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def active_riders_in_area(area: str) -> List[Dict[str, Any]]:
    area_norm = area.strip().lower()
    s = SessionLocal()
    try:
        rows = s.query(WaitlistEntry).filter_by(area=area_norm, record_type="rider", status="WAITING").all()
        out = []
        for r in rows:
            # Prefer the linked user_id (real account); fall back to waitlist id
            rid = r.user_id or r.id
            out.append({
                "id": rid,
                "waitlist_id": r.id,
                "full_name": r.full_name,
                "area": r.area,
                "vehicle": r.vehicle,
                "phone": r.phone,
                "email": r.email,
            })
        return out
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
def create_order(**kw) -> Dict[str, Any]:
    s = SessionLocal()
    try:
        o = Order(
            id=kw["order_id"],
            shop_id=kw["shop_id"],
            merchant_id=kw["merchant_id"],
            items=kw["items"],
            total_minor=kw["total_minor"],
            delivery=kw.get("delivery"),
            status=kw.get("status", "awaiting_payment"),
        )
        s.add(o)
        s.commit()
        return _order_to_dict(o)
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    s = SessionLocal()
    try:
        o = s.get(Order, order_id)
        return _order_to_dict(o) if o else None
    finally:
        s.close()


def update_order_status(order_id: str, **kw) -> Optional[Dict[str, Any]]:
    s = SessionLocal()
    try:
        o = s.get(Order, order_id)
        if not o:
            return None
        if kw.get("status") is not None:
            o.status = kw["status"]
        if kw.get("payment_id") is not None:
            o.payment_id = kw["payment_id"]
        if kw.get("rider_id") is not None:
            o.rider_id = kw["rider_id"]
        if kw.get("vat_minor") is not None:
            o.vat_minor = kw["vat_minor"]
        if kw.get("mark_paid"):
            o.paid_at = _now()
        if kw.get("mark_confirmed"):
            o.confirmed_at = _now()
        if kw.get("mark_dispatched"):
            o.dispatched_at = _now()
        if kw.get("mark_delivered"):
            o.delivered_at = _now()
        s.commit()
        s.refresh(o)
        return _order_to_dict(o)
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _order_to_dict(o: Order) -> Dict[str, Any]:
    return {
        "order_id": o.id,
        "shop_id": o.shop_id,
        "merchant_id": o.merchant_id,
        "items": o.items,
        "total_minor": o.total_minor,
        "currency": o.currency,
        "delivery": o.delivery,
        "status": o.status,
        "payment_id": o.payment_id,
        "rider_id": o.rider_id,
        "vat_minor": o.vat_minor,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "paid_at": o.paid_at.isoformat() if o.paid_at else None,
        "confirmed_at": o.confirmed_at.isoformat() if o.confirmed_at else None,
        "dispatched_at": o.dispatched_at.isoformat() if o.dispatched_at else None,
        "delivered_at": o.delivered_at.isoformat() if o.delivered_at else None,
    }


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------
def create_payment_record(**kw) -> Dict[str, Any]:
    s = SessionLocal()
    try:
        p = Payment(
            id=kw["payment_id"],
            order_id=kw["order_id"],
            amount_minor=kw["amount_minor"],
            provider=kw["provider"],
            payment_url=kw.get("payment_url"),
            status=kw.get("status", "pending"),
        )
        s.add(p)
        s.commit()
        return _payment_to_dict(p)
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_payment(payment_id: str) -> Optional[Dict[str, Any]]:
    s = SessionLocal()
    try:
        p = s.get(Payment, payment_id)
        return _payment_to_dict(p) if p else None
    finally:
        s.close()


def mark_payment_paid(payment_id: str) -> Optional[Dict[str, Any]]:
    s = SessionLocal()
    try:
        p = s.get(Payment, payment_id)
        if not p:
            return None
        p.status = "paid"
        p.paid_at = _now()
        s.commit()
        s.refresh(p)
        return _payment_to_dict(p)
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def mark_payment_cancelled(payment_id: str) -> Optional[Dict[str, Any]]:
    s = SessionLocal()
    try:
        p = s.get(Payment, payment_id)
        if not p:
            return None
        p.status = "cancelled"
        s.commit()
        s.refresh(p)
        return _payment_to_dict(p)
    finally:
        s.close()


def _payment_to_dict(p: Payment) -> Dict[str, Any]:
    return {
        "payment_id": p.id,
        "order_id": p.order_id,
        "amount_minor": p.amount_minor,
        "currency": p.currency,
        "provider": p.provider,
        "provider_reference": p.provider_reference,
        "status": p.status,
        "payment_url": p.payment_url,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "paid_at": p.paid_at.isoformat() if p.paid_at else None,
    }


# ---------------------------------------------------------------------------
# Riders
# ---------------------------------------------------------------------------
def record_rider_event(**kw) -> Dict[str, Any]:
    s = SessionLocal()
    try:
        e = RiderEvent(rider_id=kw["rider_id"], order_id=kw.get("order_id"),
                       event=kw["event"], status=kw["status"])
        s.add(e)
        s.commit()
        return {"id": e.id, "rider_id": e.rider_id, "order_id": e.order_id,
                "event": e.event, "status": e.status, "at": e.at.isoformat()}
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def rider_events(rider_id: str) -> List[Dict[str, Any]]:
    s = SessionLocal()
    try:
        rows = s.query(RiderEvent).filter_by(rider_id=rider_id).order_by(RiderEvent.at).all()
        return [{"id": r.id, "order_id": r.order_id, "event": r.event,
                 "status": r.status, "at": r.at.isoformat()} for r in rows]
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Tax
# ---------------------------------------------------------------------------
def record_tax(**kw) -> Dict[str, Any]:
    s = SessionLocal()
    try:
        t = TaxRecord(
            order_id=kw["order_id"],
            payment_id=kw.get("payment_id"),
            merchant_id=kw["merchant_id"],
            amount_minor=kw["amount_minor"],
            vat_minor=kw["vat_minor"],
            description=kw.get("description"),
            customer_reference=kw.get("customer_reference"),
        )
        s.add(t)
        s.commit()
        return {
            "id": t.id, "order_id": t.order_id, "payment_id": t.payment_id,
            "amount_minor": t.amount_minor, "vat_minor": t.vat_minor,
            "vat_rate": t.vat_rate, "currency": t.currency,
            "recorded_at": t.recorded_at.isoformat(),
        }
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Users / Auth
# ---------------------------------------------------------------------------
def create_user(
    *,
    role: str,
    email: str,
    password_hash: str,
    full_name: str,
    phone: str | None = None,
    area: str | None = None,
    business_name: str | None = None,
    vehicle: str | None = None,
    licence_number: str | None = None,
) -> dict:
    from db.models import User
    from sqlalchemy.exc import IntegrityError
    s = SessionLocal()
    try:
        shop_id = _make_shop_id(business_name) if role == "shop" and business_name else None
        u = User(
            role=role, email=email.lower().strip(), password_hash=password_hash,
            full_name=full_name, phone=phone, area=(area.strip().lower() if area else None),
            business_name=business_name, shop_id=shop_id,
            vehicle=vehicle, licence_number=licence_number,
        )
        s.add(u)
        s.commit()
        s.refresh(u)
        return {
            "id": u.id, "role": u.role, "email": u.email, "full_name": u.full_name,
            "area": u.area, "shop_id": u.shop_id,
        }
    except IntegrityError:
        s.rollback()
        raise ValueError("Email already registered")
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_user_by_email(email: str):
    from db.models import User
    s = SessionLocal()
    try:
        return s.query(User).filter_by(email=email.lower().strip()).first()
    finally:
        s.close()


def get_user_by_id(user_id: str):
    from db.models import User
    s = SessionLocal()
    try:
        return s.get(User, user_id)
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Shop-scoped queries
# ---------------------------------------------------------------------------
def list_orders_for_shop(shop_id: str, limit: int = 100):
    s = SessionLocal()
    try:
        rows = (s.query(Order)
                  .filter_by(shop_id=shop_id)
                  .order_by(Order.created_at.desc())
                  .limit(limit)
                  .all())
        return [_order_to_dict(o) for o in rows]
    finally:
        s.close()


def shop_stats(shop_id: str):
    s = SessionLocal()
    try:
        orders = s.query(Order).filter_by(shop_id=shop_id).all()
        total_orders = len(orders)
        total_revenue_minor = sum(o.total_minor or 0 for o in orders if o.status in ("confirmed", "dispatched", "delivered"))
        pending_orders = sum(1 for o in orders if o.status == "awaiting_payment")
        delivered = sum(1 for o in orders if o.status == "delivered")
        return {
            "shop_id": shop_id,
            "total_orders": total_orders,
            "total_revenue_minor": total_revenue_minor,
            "total_revenue_display": f"R{total_revenue_minor / 100:.2f}",
            "pending_orders": pending_orders,
            "delivered_orders": delivered,
        }
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Rider-scoped queries
# ---------------------------------------------------------------------------
def list_jobs_for_rider(rider_id: str, limit: int = 100):
    """Active jobs (status=dispatched) + recent completed history."""
    s = SessionLocal()
    try:
        # Active: order.rider_id == rider_id AND status == dispatched
        active = (s.query(Order)
                    .filter_by(rider_id=rider_id, status="dispatched")
                    .order_by(Order.created_at.desc())
                    .limit(limit)
                    .all())
        # Completed: order.rider_id == rider_id AND status == delivered
        completed = (s.query(Order)
                       .filter_by(rider_id=rider_id, status="delivered")
                       .order_by(Order.delivered_at.desc())
                       .limit(limit)
                       .all())
        return {
            "active": [_order_to_dict(o) for o in active],
            "completed": [_order_to_dict(o) for o in completed],
        }
    finally:
        s.close()


def rider_stats(rider_id: str):
    """Stats for a rider: active, completed, earnings estimate."""
    s = SessionLocal()
    try:
        active = s.query(Order).filter_by(rider_id=rider_id, status="dispatched").count()
        completed = s.query(Order).filter_by(rider_id=rider_id, status="delivered").count()
        # Earnings: for each delivered order, estimate the rider's cut.
        # Until we record rider_payout separately, use 85% of a nominal R25 fee.
        earnings_minor = completed * int(round(25.00 * 0.85 * 100))  # R21.25 per delivery
        return {
            "rider_id": rider_id,
            "active_jobs": active,
            "completed_jobs": completed,
            "earnings_minor": earnings_minor,
            "earnings_display": f"R{earnings_minor / 100:.2f}",
        }
    finally:
        s.close()
