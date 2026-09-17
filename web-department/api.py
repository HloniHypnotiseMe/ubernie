#!/usr/bin/env python3
"""
Web Department — API

Endpoints the generated shop sites call:
  GET  /health
  GET  /api/waitlist/zones
  GET  /api/waitlist/zone/{area}
  POST /api/waitlist/shop
  POST /api/waitlist/rider
  POST /api/remotepay/create-payment
  GET  /api/delivery/check?area=X
  POST /api/orders/confirm
  GET  /api/orders/{order_id}
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

from integration import waitlist, rider_dispatch
from builder.site_generator import SiteGenerator
from builder.site_renderer import SiteRenderer
from integration.remotepay_client import RemotePayClient, RemotePayError
from integration.ubernie_delivery import UbernieDeliveryClient
from integration.taxai_hook import calculate_vat, record_transaction

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("web-department.api")

app = FastAPI(title="C6 Web Department", version="0.2.0")

import os as _os_mount
_SITES_DIR = _os_mount.getenv("GENERATED_SITES_DIR", "generated-sites")
_os_mount.makedirs(_SITES_DIR, exist_ok=True)

app.mount("/sites", StaticFiles(directory=_SITES_DIR, html=True), name="sites")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

remotepay = RemotePayClient()
delivery = UbernieDeliveryClient()

_ORDERS: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Schemas — Waitlist
# ---------------------------------------------------------------------------
class ShopWaitlistRequest(BaseModel):
    business_name: str = Field(min_length=1)
    area: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    email: str = Field(min_length=3)
    phone: str = Field(min_length=5)
    estimated_daily_orders: int = 0


class RiderWaitlistRequest(BaseModel):
    full_name: str = Field(min_length=1)
    area: str = Field(min_length=1)
    vehicle: str = Field(default="Zeebee Greenscooter")
    phone: str = Field(min_length=5)
    email: str = Field(min_length=3)
    licence_number: str = ""


# ---------------------------------------------------------------------------
# Schemas — Orders
# ---------------------------------------------------------------------------
class CartItem(BaseModel):
    id: str
    name: str
    price: float
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


class GenerateSiteRequest(BaseModel):
    business_name: str = Field(min_length=1)
    industry: str = Field(default="retail")
    address: str = Field(default="")
    phone: str = ""
    email: str = ""
    tagline: str = ""
    story: str = ""
    menu_items: List[Dict[str, Any]] = []
    products: List[Dict[str, Any]] = []
    services: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Health
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


# ---------------------------------------------------------------------------
# Waitlist endpoints
# ---------------------------------------------------------------------------
@app.post("/api/waitlist/shop")
async def join_waitlist_shop(req: ShopWaitlistRequest):
    result = waitlist.register_shop(
        business_name=req.business_name,
        area=req.area,
        industry=req.industry,
        email=req.email,
        phone=req.phone,
        estimated_daily_orders=req.estimated_daily_orders,
    )
    status = waitlist.zone_status(req.area)
    return {"registration": result, "zone": status}


@app.post("/api/waitlist/rider")
async def join_waitlist_rider(req: RiderWaitlistRequest):
    result = waitlist.register_rider(
        full_name=req.full_name,
        area=req.area,
        vehicle=req.vehicle,
        phone=req.phone,
        email=req.email,
        licence_number=req.licence_number,
    )
    status = waitlist.zone_status(req.area)
    return {"registration": result, "zone": status}


@app.get("/api/waitlist/zone/{area}")
async def get_zone(area: str):
    return waitlist.zone_status(area)


@app.get("/api/waitlist/zones")
async def get_all_zones():
    return {"zones": waitlist.list_zones()}


# ---------------------------------------------------------------------------
# Delivery (now waitlist-driven)
# ---------------------------------------------------------------------------
@app.get("/api/delivery/check")
async def check_delivery(area: str):
    if not area:
        raise HTTPException(status_code=400, detail="area is required")
    return delivery.check_area(area)


# ---------------------------------------------------------------------------
# Orders / payments
# ---------------------------------------------------------------------------
@app.post("/api/remotepay/create-payment")
async def create_payment(req: CreatePaymentRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_rands = sum(i.price * i.qty for i in req.items)
    total_minor = int(round(total_rands * 100))

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


@app.post("/api/orders/confirm")
async def confirm_order(req: ConfirmOrderRequest):
    order = _ORDERS.get(req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] == "confirmed":
        return {"status": "already_confirmed", "order_id": req.order_id}

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

    # ---- Dispatch a rider if delivery was requested and zone is active ----
    dispatch_result: Dict[str, Any] = {"dispatched": False}
    delivery_area = (order.get("delivery") or {}).get("area")
    if delivery_area:
        match = rider_dispatch.find_best_rider(delivery_area)
        if match:
            assignment = rider_dispatch.assign(
                order_id=req.order_id,
                rider_id=match["rider"]["id"],
                area=delivery_area,
            )
            order["status"] = "dispatched"
            order["rider"] = match["rider"]
            order["assignment"] = assignment
            dispatch_result = {
                "dispatched": True,
                "rider": match["rider"],
                "score": match["score"],
                "distance_km": match["distance_km"],
                "alternatives": match["alternatives"],
            }
        else:
            order["status"] = "confirmed_pending_dispatch"
            dispatch_result = {
                "dispatched": False,
                "reason": "no_available_rider",
                "message": "Order confirmed. No rider currently available; will retry.",
            }

    return {
        "status": order["status"],
        "order_id": req.order_id,
        "vat_minor": vat_minor,
        "vat_display": f"R{vat_minor / 100:.2f}",
        "tax_record": tax_entry,
        "dispatch": dispatch_result,
    }


@app.get("/api/riders/zone/{area}")
async def get_riders_in_zone(area: str):
    return {
        "area": area,
        "zone_active": waitlist.is_zone_active(area),
        "riders": rider_dispatch.list_riders_in_zone(area),
    }


@app.post("/api/riders/{rider_id}/complete")
async def complete_delivery(rider_id: str, order_id: str):
    record = rider_dispatch.release(rider_id=rider_id, order_id=order_id, reason="completed")
    order = _ORDERS.get(order_id)
    if order:
        order["status"] = "delivered"
        order["delivered_at"] = record["at"]
    return {"status": "completed", "release": record}


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    order = _ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ---------------------------------------------------------------------------
# Site generation (per-shop storefront)
# ---------------------------------------------------------------------------
import os as _os

@app.post("/api/sites/{shop_id}/generate")
async def generate_site(shop_id: str, req: GenerateSiteRequest):
    """Generate a static storefront for a shop and return a preview URL."""
    base_dir = _os.getenv("GENERATED_SITES_DIR", "generated-sites")
    output_dir = f"{base_dir}/{shop_id}"

    shop_data = {
        "id": shop_id,
        "name": req.business_name,
        "industry": req.industry,
        "address": req.address,
        "phone": req.phone,
        "email": req.email,
        "tagline": req.tagline or f"Welcome to {req.business_name}",
        "story": req.story,
        "menu_items": req.menu_items,
        "products": req.products,
        "services": req.services,
        "remotepay_merchant_id": f"merchant_{shop_id}",
        "ubernie_shop_id": shop_id,
    }

    import traceback
    try:
        config = SiteGenerator(shop_data).generate()
        renderer = SiteRenderer(config, output_dir)
        result = renderer.render()
    except Exception as e:
        tb = traceback.format_exc()
        print("=== SITE GENERATION FAILED ===")
        print(tb)
        print("=== END TRACEBACK ===")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

    # Serve statically at /sites/{shop_id}/index.html
    return {
        "shop_id": shop_id,
        "status": "generated",
        "output_dir": result["rendered_to"],
        "api_base_url": result.get("api_base_url"),
        "preview_url": f"/sites/{shop_id}/index.html",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8100, reload=True)
