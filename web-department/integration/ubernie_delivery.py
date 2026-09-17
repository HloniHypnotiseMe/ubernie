#!/usr/bin/env python3
"""
Web Department — Ubernie Delivery Client

Checks whether delivery is available in a given area.
Falls back to a local area list if the delivery engine isn't running.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

log = logging.getLogger("web-department.delivery")


# Zone registry (in-memory stub; real source is the waitlist engine DB)
_ACTIVE_ZONES = {
    "soweto": {"fee_minor": 2500, "eta_minutes": 35},
    "cape town cbd": {"fee_minor": 3000, "eta_minutes": 30},
    "sandton": {"fee_minor": 3500, "eta_minutes": 40},
    "durban north": {"fee_minor": 3000, "eta_minutes": 35},
}


class UbernieDeliveryClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or os.getenv("UBERNIE_DELIVERY_API_URL", "")).rstrip("/")
        self.timeout = timeout

    def check_area(self, area: str) -> Dict[str, Any]:
        """Return delivery availability for an area."""
        area_norm = area.strip().lower()

        # Try remote first if configured
        if self.base_url:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    r = client.get(f"{self.base_url}/api/delivery/check", params={"area": area})
                    r.raise_for_status()
                    return r.json()
            except Exception as exc:  # noqa: BLE001
                log.warning("Remote delivery check failed, using local registry: %s", exc)

        # Local fallback
        if area_norm in _ACTIVE_ZONES:
            zone = _ACTIVE_ZONES[area_norm]
            return {
                "area": area,
                "available": True,
                "fee_minor": zone["fee_minor"],
                "fee_display": f"R{zone['fee_minor'] / 100:.2f}",
                "eta_minutes": zone["eta_minutes"],
                "source": "local_registry",
            }

        return {
            "area": area,
            "available": False,
            "waitlist_url": f"/waitlist?area={area}",
            "message": f"Delivery not yet available in {area}. Join the waitlist.",
            "source": "local_registry",
        }
