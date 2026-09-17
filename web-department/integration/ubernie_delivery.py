#!/usr/bin/env python3
"""
Web Department — Ubernie Delivery Client

Zone availability is derived from the WAITLIST (single source of truth).
A zone is available iff waitlist.is_zone_active(area) == True.

Fees and ETAs are still placeholder values until we model zone economics.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from integration import waitlist

log = logging.getLogger("web-department.delivery")


# Placeholder zone economics (fees in cents, ETA in minutes).
# Real values come later from zone config; thresholds are what gate them.
_ZONE_ECONOMICS = {
    "soweto":         {"fee_minor": 2500, "eta_minutes": 35},
    "cape town cbd":  {"fee_minor": 3000, "eta_minutes": 30},
    "sandton":        {"fee_minor": 3500, "eta_minutes": 40},
    "durban north":   {"fee_minor": 3000, "eta_minutes": 35},
}
_DEFAULT_ECONOMICS = {"fee_minor": 3000, "eta_minutes": 40}


class UbernieDeliveryClient:
    def check_area(self, area: str) -> Dict[str, Any]:
        """Return delivery availability, driven by the waitlist."""
        area_norm = area.strip().lower()
        status = waitlist.zone_status(area_norm)

        if not status["active"]:
            return {
                "area": area,
                "available": False,
                "waitlist_url": f"/waitlist?area={area}",
                "message": (
                    f"Delivery not yet available in {area}. "
                    f"{status['shops_waiting']}/{status['shops_threshold']} shops, "
                    f"{status['riders_waiting']}/{status['riders_threshold']} riders."
                ),
                "zone_status": status,
                "source": "waitlist",
            }

        econ = _ZONE_ECONOMICS.get(area_norm, _DEFAULT_ECONOMICS)
        return {
            "area": area,
            "available": True,
            "fee_minor": econ["fee_minor"],
            "fee_display": f"R{econ['fee_minor'] / 100:.2f}",
            "eta_minutes": econ["eta_minutes"],
            "zone_status": status,
            "source": "waitlist",
        }
