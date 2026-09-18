#!/usr/bin/env python3
"""Two-Sided Waitlist Engine (DB-backed)."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from db import repositories as repo

log = logging.getLogger("web-department.waitlist")

MIN_SHOPS = int(os.getenv("WAITLIST_MIN_SHOPS", "15"))
MIN_RIDERS = int(os.getenv("WAITLIST_MIN_RIDERS", "3"))


def register_shop(*, business_name, area, industry, email, phone, estimated_daily_orders=0, user_id=None):
    result = repo.add_waitlist_entry(
        record_type="shop",
        area=area,
        email=email,
        phone=phone,
        business_name=business_name,
        industry=industry,
        estimated_daily_orders=estimated_daily_orders,
        user_id=user_id,
    )
    log.info("Shop registered: %s in %s", business_name, result["area"])
    return result


def register_rider(*, full_name, area, vehicle, phone, email, licence_number="", user_id=None):
    result = repo.add_waitlist_entry(
        record_type="rider",
        area=area,
        email=email,
        phone=phone,
        full_name=full_name,
        vehicle=vehicle,
        licence_number=licence_number,
        user_id=user_id,
    )
    log.info("Rider registered: %s in %s", full_name, result["area"])
    return result


def zone_status(area: str) -> Dict[str, Any]:
    area_norm = area.strip().lower()
    counts = repo.zone_counts(area_norm)
    shop_count = counts["shops"]
    rider_count = counts["riders"]
    ready = shop_count >= MIN_SHOPS and rider_count >= MIN_RIDERS
    zone = repo.get_zone(area_norm)

    if ready and (zone is None or not zone.active):
        zone = repo.upsert_zone(area_norm, shop_count, rider_count, active=True)
        log.info("ZONE ACTIVATED: %s (shops=%d, riders=%d)", area_norm, shop_count, rider_count)
    elif zone is None:
        zone = repo.upsert_zone(area_norm, shop_count, rider_count, active=False)
    elif zone.shop_count != shop_count or zone.rider_count != rider_count:
        zone = repo.upsert_zone(area_norm, shop_count, rider_count, active=zone.active)

    shop_progress = min(shop_count / MIN_SHOPS, 1.0) if MIN_SHOPS else 1.0
    rider_progress = min(rider_count / MIN_RIDERS, 1.0) if MIN_RIDERS else 1.0

    return {
        "area": area_norm,
        "shops_waiting": shop_count,
        "shops_threshold": MIN_SHOPS,
        "shops_progress_pct": round(shop_progress * 100, 1),
        "riders_waiting": rider_count,
        "riders_threshold": MIN_RIDERS,
        "riders_progress_pct": round(rider_progress * 100, 1),
        "ready_to_activate": ready,
        "active": bool(zone.active),
        "activated_at": zone.activated_at.isoformat() if zone.activated_at else None,
        "status": "ACTIVE" if zone.active else "WAITING",
    }


def is_zone_active(area: str) -> bool:
    return zone_status(area)["active"]


def list_zones() -> List[Dict[str, Any]]:
    return [zone_status(a) for a in repo.list_zones()]


def active_riders_in_zone(area: str) -> List[Dict[str, Any]]:
    area_norm = area.strip().lower()
    if not is_zone_active(area_norm):
        return []
    return repo.active_riders_in_area(area_norm)
