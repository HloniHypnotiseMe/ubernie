#!/usr/bin/env python3
"""
Web Department — Rider Dispatch Engine (DB-backed)

Finds the best available rider for a delivery job.
Riders come from the waitlist; availability comes from rider_events.
"""
from __future__ import annotations

import logging
import math
import os
from typing import Any, Dict, List, Optional

from db import repositories as repo
from integration import waitlist

log = logging.getLogger("web-department.dispatch")

_ZONE_CENTERS = {
    "soweto":        {"lat": -26.2678, "lng": 27.8585},
    "cape town cbd": {"lat": -33.9249, "lng": 18.4241},
    "sandton":       {"lat": -26.1076, "lng": 28.0567},
    "durban north":  {"lat": -29.7864, "lng": 31.0340},
}


def list_riders_in_zone(area: str) -> List[Dict[str, Any]]:
    if not waitlist.is_zone_active(area):
        return []
    riders = waitlist.active_riders_in_zone(area)
    enriched = []
    for r in riders:
        events = repo.rider_events(r["id"])
        assigned = sum(1 for e in events if e["event"] == "assigned")
        completed = sum(1 for e in events if e["event"] == "completed")
        released = sum(1 for e in events if e["event"] == "released")
        current_jobs = max(0, assigned - completed - released)
        status = "AVAILABLE" if current_jobs == 0 else "ON_DELIVERY"
        enriched.append({
            "id": r["id"],
            "full_name": r["full_name"],
            "area": r["area"],
            "vehicle": r.get("vehicle"),
            "phone": r.get("phone"),
            "status": status,
            "current_jobs": current_jobs,
            "completed_jobs": completed,
        })
    return enriched


def find_best_rider(area: str, shop_lat: Optional[float] = None, shop_lng: Optional[float] = None) -> Optional[Dict[str, Any]]:
    area_norm = area.strip().lower()
    if not waitlist.is_zone_active(area_norm):
        return None
    riders = list_riders_in_zone(area_norm)
    if not riders:
        return None

    center = _ZONE_CENTERS.get(area_norm)
    if shop_lat is None or shop_lng is None:
        if not center:
            available = [r for r in riders if r["status"] == "AVAILABLE"]
            return {"rider": available[0], "score": 100.0, "distance_km": 0.0, "alternatives": []} if available else None
        shop_lat, shop_lng = center["lat"], center["lng"]

    scored = []
    for r in riders:
        if r["status"] != "AVAILABLE":
            continue
        rider_lat, rider_lng = _rider_position(area_norm, r["id"])
        score = _score_rider(r, rider_lat, rider_lng, shop_lat, shop_lng)
        scored.append({"rider": r, "score": score, "distance_km": _haversine(rider_lat, rider_lng, shop_lat, shop_lng)})

    if not scored:
        return None
    scored.sort(key=lambda x: x["score"], reverse=True)
    best = scored[0]
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
    event = repo.record_rider_event(rider_id=rider_id, order_id=order_id, event="assigned", status="ON_DELIVERY")
    repo.update_order_status(order_id, rider_id=rider_id, status="dispatched", mark_dispatched=True)
    return event


def release(rider_id: str, order_id: str, reason: str = "completed") -> Dict[str, Any]:
    event = repo.record_rider_event(rider_id=rider_id, order_id=order_id, event=reason, status="AVAILABLE")
    if reason == "completed":
        repo.update_order_status(order_id, status="delivered", mark_delivered=True)
    return event


def _score_rider(rider, rider_lat, rider_lng, shop_lat, shop_lng) -> float:
    distance_km = _haversine(rider_lat, rider_lng, shop_lat, shop_lng)
    distance_score = max(0.0, 40.0 - (distance_km * 4.0))
    rating_score = 20.0
    load_score = max(0.0, 20.0 - (rider.get("current_jobs", 0) * 5.0))
    acceptance_score = 20.0
    return distance_score + rating_score + load_score + acceptance_score


def _haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def _rider_position(area: str, rider_id: str) -> tuple:
    """Deterministic jitter so riders don't all sit at the same point."""
    center = _ZONE_CENTERS.get(area)
    if not center:
        return (0.0, 0.0)
    # Deterministic hash-based jitter around center (per rider id)
    h = abs(hash(rider_id))
    lat_jitter = ((h % 1000) / 1000.0 - 0.5) * 0.02
    lng_jitter = (((h // 1000) % 1000) / 1000.0 - 0.5) * 0.02
    return (center["lat"] + lat_jitter, center["lng"] + lng_jitter)
