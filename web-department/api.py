#!/usr/bin/env python3
"""
Web Department — API

Endpoints the generated shop sites call:
  GET  /health
  POST /api/remotepay/create-payment
  GET  /api/delivery/check?area=X
  POST /api/orders/confirm
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

from integration.remotepay_client import RemotePayClient, RemotePayError
from integration.ubernie_delivery import UbernieDeliveryClient
from integration.taxai_hook import calculate_vat, record_transaction

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("web-department.api")

app = FastAPI(title="C6 Web Department", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

remotepay = RemotePayClient()
delivery = UbernieDeliveryClient()

# In-memory order store (upgrade to Mongo later)
_ORDERS: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CartItem(BaseModel):
    id: str
    name: str
    price: float  # in Rands
    qty: int = Field(ge=1)


class CreatePaymentRequest(BaseModel):
    shop_id: str
    merchant_id: str
    items: List[CartItem]
    customer_email: str | None = None
    customer_name: str | None = None
    return_url: str | None = None
    cancel_url: str | None = None
    delivery_area: str | None = None


class ConfirmOrderRequest(BaseModel):
    order_id: str
    payment_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "C6 Web Department",
        "remotepay_mode": remotepay.mode,
        "remotepay_url": remotepay.base_url,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/remotepay/create-payment")
async def create_payment(req: CreatePaymentRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Compute total in cents
    total_rands = sum(i.price * i.qty for i in req.items)
    total_minor = int(round(total_rands * 100))

    # Optional delivery fee
    delivery_result: Dict[str, Any] | None = None
    if req.delivery_area:
        delivery_result = delivery.check_area(req.delivery_area)
        if delivery_result.get("available"):
            total_minor += delivery_result["fee_minor"]

    order_id = f"ord_{uuid.uuid4().hex[:16]}"
    description = f"Order {order_id} — {len(req.items)} item(s)"

    try:
        payment = remotepay.create_payment(
            amount_minor=total_minor,
            description=description,
            merchant_id=req.merchant_id,
            brand_id="ubernie",
            source_system="c6_web_department",
            customer_reference=req.customer_email,
            return_url=req.return_url,
            cancel_url=req.cancel_url,
            idempotency_key=f"idem_{order_id}",
            metadata={
                "shop_id": req.shop_id,
                "order_id": order_id,
                "delivery_area": req.delivery_area,
                "item_count": len(req.items),
            },
        )
    except RemotePayError as exc:
        raise HTTPException(status_code=502, detail=f"Payment creation failed: {exc}") from exc

    # Store order
    _ORDERS[order_id] = {
        "order_id": order_id,
        "shop_id": req.shop_id,
        "merchant_id": req.merchant_id,
        "items": [i.model_dump() for i in req.items],
        "total_minor": total_minor,
        "delivery": delivery_result,
        "payment": payment,
        "status": "awaiting_payment",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "order_id": order_id,
        "payment_id": payment["payment_id"],
        "payment_url": payment["payment_url"],
        "provider_path": payment["provider_path"],
        "amount_minor": total_minor,
        "amount_display": f"R{total_minor / 100:.2f}",
        "delivery": delivery_result,
    }


@app.get("/api/delivery/check")
async def check_delivery(area: str):
    if not area:
        raise HTTPException(status_code=400, detail="area is required")
    return delivery.check_area(area)


@app.post("/api/orders/confirm")
async def confirm_order(req: ConfirmOrderRequest):
    order = _ORDERS.get(req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] == "confirmed":
        return {"status": "already_confirmed", "order_id": req.order_id}

    # Record tax
    vat_minor = calculate_vat(order["total_minor"])
    tax_entry = record_transaction(
        order_id=req.order_id,
        payment_id=req.payment_id,
        merchant_id=order["merchant_id"],
        amount_minor=order["total_minor"],
        vat_minor=vat_minor,
        description=f"Order {req.order_id}",
        customer_reference=None,
    )

    order["status"] = "confirmed"
    order["tax_entry"] = tax_entry
    order["confirmed_at"] = datetime.now(timezone.utc).isoformat()

    # TODO: dispatch rider via Ubernie delivery engine
    return {
        "status": "confirmed",
        "order_id": req.order_id,
        "vat_minor": vat_minor,
        "vat_display": f"R{vat_minor / 100:.2f}",
        "tax_record": tax_entry,
    }


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    order = _ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8100, reload=True)
