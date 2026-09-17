#!/usr/bin/env python3
"""
Web Department — Two-Sided Waitlist Engine

Shops and riders register interest in delivery for an area.
A zone ACTIVATES when BOTH thresholds are met:
  - 15 shops waiting
  - 3 riders waiting

Everything is append-only JSONL (data/waitlist.jsonl) — MongoDB later.
The waitlist is the SINGLE SOURCE OF TRUTH for "is this zone live?"
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("web-department.waitlist")

_LEDGER_PATH = Path(os.getenv("WAITLIST_LEDGER", "data/waitlist.jsonl"))
_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

# Thresholds (configurable via env)
MIN_SHOPS = int(os.getenv("WAITLIST_MIN_SHOPS", "15"))
MIN_RIDERS = int(os.getenv("WAITLIST_MIN_RIDERS", "3"))


# ---------------------------------------------------------------------------
# Persistence (append-only JSONL — simple, safe, greppable)
# ---------------------------------------------------------------------------
def _append(record: Dict[str, Any]) -> None:
    with _LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def _read_all() -> List[Dict[str, Any]]:
    if not _LEDGER_PATH.exists():
        return []
    out: List[Dict[str, Any]] = []
    with _LEDGER_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("Skipping malformed waitlist line: %s", line[:80])
    return out


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------
def register_shop(
    *,
    business_name: str,
    area: str,
    industry: str,
    email: str,
    phone: str,
    estimated_daily_orders: int = 0,
) -> Dict[str, Any]:
    """Shop joins the waitlist for delivery in its area."""
    area_norm = _normalize_area(area)
    record = {
        "record_type": "shop",
        "id": f"shop_{uuid.uuid4().hex[:12]}",
        "business_name": business_name,
        "area": area_norm,
        "industry": industry,
        "email": email,
        "phone": phone,
        "estimated_daily_orders": estimated_daily_orders,
        "status": "WAITING",
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    _append(record)
    log.info("Shop registered: %s in %s", business_name, area_norm)
    return {"id": record["id"], "area": area_norm, "status": "WAITING"}


def register_rider(
    *,
    full_name: str,
    area: str,
    vehicle: str,
    phone: str,
    email: str,
    licence_number: str = "",
) -> Dict[str, Any]:
    """Rider joins the waitlist for delivery jobs in their area."""
    area_norm = _normalize_area(area)
    record = {
        "record_type": "rider",
        "id": f"rider_{uuid.uuid4().hex[:12]}",
        "full_name": full_name,
        "area": area_norm,
        "vehicle": vehicle,
        "phone": phone,
        "email": email,
        "licence_number": licence_number,
        "status": "WAITING",
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    _append(record)
    log.info("Rider registered: %s in %s", full_name, area_norm)
    return {"id": record["id"], "area": area_norm, "status": "WAITING"}


def zone_status(area: str) -> Dict[str, Any]:
    """Return shops/riders counts and readiness for one area."""
    area_norm = _normalize_area(area)
    records = _read_all()

    shops = [r for r in records if r.get("record_type") == "shop" and r.get("area") == area_norm]
    riders = [r for r in records if r.get("record_type") == "rider" and r.get("area") == area_norm]

    shop_count = len(shops)
    rider_count = len(riders)

    # Check for activation record
    activation = next(
        (r for r in records
         if r.get("record_type") == "zone_activated" and r.get("area") == area_norm),
        None,
    )

    ready = shop_count >= MIN_SHOPS and rider_count >= MIN_RIDERS
    active = activation is not None or ready

    # If thresholds met and no activation recorded yet, fire activation
    if ready and not activation:
        activation = _activate_zone(area_norm, shop_count, rider_count)
        active = True

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
        "active": active,
        "activated_at": activation.get("activated_at") if activation else None,
        "status": "ACTIVE" if active else "WAITING",
    }


def is_zone_active(area: str) -> bool:
    """Fast check — used by delivery client to decide availability."""
    return zone_status(area)["active"]


def list_zones() -> List[Dict[str, Any]]:
    """All areas currently in the waitlist, sorted by shops desc."""
    records = _read_all()
    areas = sorted({
        r["area"] for r in records
        if r.get("record_type") in ("shop", "rider") and r.get("area")
    })
    return [zone_status(a) for a in areas]


def active_riders_in_zone(area: str) -> List[Dict[str, Any]]:
    """Return registered riders in an active zone (for dispatch)."""
    area_norm = _normalize_area(area)
    if not is_zone_active(area_norm):
        return []
    records = _read_all()
    return [
        r for r in records
        if r.get("record_type") == "rider"
        and r.get("area") == area_norm
        and r.get("status") == "WAITING"
    ]


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------
def _activate_zone(area: str, shop_count: int, rider_count: int) -> Dict[str, Any]:
    """Record a zone activation event exactly once."""
    activation = {
        "record_type": "zone_activated",
        "id": f"zone_{uuid.uuid4().hex[:12]}",
        "area": area,
        "shop_count_at_activation": shop_count,
        "rider_count_at_activation": rider_count,
        "activated_at": datetime.now(timezone.utc).isoformat(),
    }
    _append(activation)
    log.info("🎉 ZONE ACTIVATED: %s (shops=%d, riders=%d)", area, shop_count, rider_count)
    return activation


def _normalize_area(area: str) -> str:
    return area.strip().lower()
