#!/usr/bin/env python3
"""
Web Department — Tax AI Hook (DB-backed)

Every confirmed order is logged as a tax record for VAT.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from db import repositories as repo

log = logging.getLogger("web-department.taxai")


def record_transaction(
    *,
    order_id: str,
    payment_id: str | None,
    merchant_id: str,
    amount_minor: int,
    vat_minor: int,
    description: str,
    customer_reference: str | None = None,
) -> Dict[str, Any]:
    record = repo.record_tax(
        order_id=order_id,
        payment_id=payment_id,
        merchant_id=merchant_id,
        amount_minor=amount_minor,
        vat_minor=vat_minor,
        description=description,
        customer_reference=customer_reference,
    )
    log.info("Tax record written: order=%s vat_minor=%d", order_id, vat_minor)
    return record


def calculate_vat(amount_minor_inclusive: int, vat_rate: float = 0.15) -> int:
    return round(amount_minor_inclusive * vat_rate / (1 + vat_rate))
