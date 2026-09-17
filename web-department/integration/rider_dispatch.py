#!/usr/bin/env python3
"""
Web Department — Rider Dispatch Engine

Finds the best available rider for a delivery job.

Riders come from the waitlist (single source of truth for who exists in a zone).
Rider AVAILABILITY state lives here (available / busy / offline) — separate concern
from waitlist registration.

Scoring (max 100):
  - proximity to shop:  40 pts
  - rating:             20 pts
  - current load:       20 pts (fewer jobs = better)
  - acceptance rate:    20 pts

Persistence: append-only JSONL (data/rider_state.jsonl).
Riders registered via waitlist are implicitly AVAILABLE on first lookup.
"""
from __future__ import annotations

import json
import logging
import math
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from integration import waitlist

log = logging.getLogger("web-department.dispatch")

_STATE_PATH = Path(os.getenv("RIDER_STATE_LEDGER", "data/rider_state.jsonl"))
_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Placeholder zone center coords (used when shop coords unknown).
# Real shops will carry lat/lng; this is a bridge until then.
_ZONE_CENTERS = {
    "soweto":        {"lat": -26.2678, "lng": 27.8585},
    "cape town cbd": {"lat": -33.9249, "lng": 18.4241},
    "sandton":       {"lat": -26.1076, "lng": 28.0567},
    "durban north":  {"lat": -29.7864, "lng": 31.0340},
}

# Placeholder rider coords jittered around zone center (until riders carry GPS)
_RIDER_JITTER = {
    "rider_1": (0.005, 0.005),
    "rider_2": (-0.008, 0.003),
    "rider_3": (0.002, -0.006),
}


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------
def _append_state(record: Dict[str, Any]) -> None:
    with _STATE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def _read_state() -> List[Dict[str, Any]]:
    if not _STATE_PATH.exists():
        return []
    out: List[Dict[str, Any]] = []
    with _STATE_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("Skipping malformed rider_state line: %s", line[:80])
    return out


def _rider_current_state(rider_id: str) -> Dict[str, Any]:
    """Derive current state from the append-only log."""
    records = [r for r in _read_state() if r.get("rider_id") == rider_id]
    if not records:
        return {"status": "AVAILABLE", "current_jobs": 0, "completed_jobs": 0}

    # Latest event wins for status
    latest = records[-1]
    completed = sum(1 for r in records if r.get("event") == "completed")
    assigned = sum(1 for r in records if r.get("event") == "assigned")
    released = sum(1 for r in records if r.get("event") == "released")

    # active jobs = assigned - completed - released
    current_jobs = max(0, assigned - completed - released)

    return {
        "status": latest.get("status", "AVAILABLE"),
        "current_jobs": current_jobs,
        "completed_jobs": completed,
        "last_event": latest.get("event"),
        "last_event_at": latest.get("at"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def list_riders_in_zone(area: str) -> List[Dict[str, Any]]:
    """All registered riders in an active zone + their current state."""
    if not waitlist.is_zone_active(area):
        return []

    riders = waitlist.active_riders_in_zone(area)
    enriched = []
    for r in riders:
        state = _rider_current_state(r["id"])
        enriched.append({
            "id": r["id"],
            "full_name": r["full_name"],
            "area": r["area"],
            "vehicle": r.get("vehicle"),
            "phone": r.get("phone"),
            "status": state["status"],
            "current_jobs": state["current_jobs"],
            "completed_jobs": state["completed_jobs"],
        })
    return enriched


def find_best_rider(area: str, shop_lat: Optional[float] = None, shop_lng: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """Pick the best AVAILABLE rider for a job in an area."""
    area_norm = area.strip().lower()
    if not waitlist.is_zone_active(area_norm):
        log.warning("Cannot dispatch: zone %s not active", area_norm)
        return None

    riders = list_riders_in_zone(area_norm)
    if not riders:
        log.warning("No riders registered in %s", area_norm)
        return None

    center = _ZONE_CENTERS.get(area_norm)
    if shop_lat is None or shop_lng is None:
        if not center:
            log.warning("No coords for %s; cannot score by distance", area_norm)
            # Degenerate fallback: pick first available
            available = [r for r in riders if r["status"] == "AVAILABLE"]
            return available[0] if available else None
        shop_lat, shop_lng = center["lat"], center["lng"]

    scored = []
    for r in riders:
        if r["status"] != "AVAILABLE":
            continue
        rider_lat, rider_lng = _rider_position(area_norm, r["id"])
        score = _score_rider(r, rider_lat, rider_lng, shop_lat, shop_lng)
        scored.append({"rider": r, "score": score, "distance_km": _haversine(rider_lat, rider_lng, shop_lat, shop_lng)})

    if not scored:
        log.warning("No AVAILABLE riders in %s", area_norm)
        return None

    scored.sort(key=lambda x: x["score"], reverse=True)
    best = scored[0]
    log.info("Best rider for %s: %s (score=%.1f, dist=%.2fkm)",
             area_norm, best["rider"]["full_name"], best["score"], best["distance_km"])
    return {
        "rider": best["rider"],
        "score": round(best["score"], 1),
        "distance_km": round(best["distance_km"], 2),
        "alternatives": [
            {"rider": s["rider"], "score": round(s["score"], 1), "distance_km": round(s["distance_km"], 2)}
            for s in scored[1:3]
        ],
    }


def assign(order_id: str, rider_id: str, area: str) -> Dict[str, Any]:
    """Mark a rider as busy and log the assignment."""
    record = {
        "event": "assigned",
        "assignment_id": f"asn_{uuid.uuid4().hex[:12]}",
        "order_id": order_id,
        "rider_id": rider_id,
        "area": area.strip().lower(),
        "status": "ON_DELIVERY",
        "at": datetime.now(timezone.utc).isoformat(),
    }
    _append_state(record)
    log.info("Assigned rider %s to order %s", rider_id, order_id)
    return record


def release(rider_id: str, order_id: str, reason: str = "completed") -> Dict[str, Any]:
    """Mark a rider as available again after a delivery."""
    record = {
        "event": reason,   # "completed" | "released" | "cancelled"
        "rider_id": rider_id,
        "order_id": order_id,
        "status": "AVAILABLE",
        "at": datetime.now(timezone.utc).isoformat(),
    }
    _append_state(record)
    log.info("Released rider %s from order %s (%s)", rider_id, order_id, reason)
    return record


# ---------------------------------------------------------------------------
# Scoring & geometry
# ---------------------------------------------------------------------------
def _score_rider(rider: Dict[str, Any], rider_lat: float, rider_lng: float, shop_lat: float, shop_lng: float) -> float:
    distance_km = _haversine(rider_lat, rider_lng, shop_lat, shop_lng)

    # Distance: 40 pts, decays over 10 km
    distance_score = max(0.0, 40.0 - (distance_km * 4.0))

    # Rating: 20 pts (default 5.0 if unknown)
    rating = rider.get("rating", 5.0)
    rating_score = (rating / 5.0) * 20.0

    # Load: 20 pts, -5 per active job
    load = rider.get("current_jobs", 0)
    load_score = max(0.0, 20.0 - (load * 5.0))

    # Acceptance: 20 pts (default 1.0)
    acceptance = rider.get("acceptance_rate", 1.0)
    acceptance_score = acceptance * 20.0

    return distance_score + rating_score + load_score + acceptance_score


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _rider_position(area: str, rider_id: str) -> tuple:
    """Placeholder rider coords around zone center (until riders report GPS)."""
    center = _ZONE_CENTERS.get(area)
    if not center:
        return (0.0, 0.0)
    jitter = _RIDER_JITTER.get(rider_id, (0.0, 0.0))
    return (center["lat"] + jitter[0], center["lng"] + jitter[1])
