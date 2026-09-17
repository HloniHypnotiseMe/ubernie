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
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
_PAYMENTS: Dict[str, Dict[str, Any]] = {}


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
async def create_payment(req: CreatePaymentRequest, request: Request):
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

    # For mock payments, rewrite relative URL → absolute against this API's base
    if payment.get("provider_path") == "mock" and payment.get("payment_url", "").startswith("/"):
        payment["payment_url"] = f"{str(request.base_url).rstrip('/')}{payment['payment_url']}"

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
    _PAYMENTS[payment["payment_id"]] = {
        "payment_id": payment["payment_id"],
        "order_id": order_id,
        "amount_minor": total_minor,
        "status": "pending",
        "provider_path": payment["provider_path"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paid_at": None,
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


# ---------------------------------------------------------------------------
# Mock payment gateway + return handling
# ---------------------------------------------------------------------------
# This simulates what SimplyBlu will do: show a hosted checkout page, take a
# payment, redirect back to merchant with a payment_id in the URL.
#
# Real SimplyBlu flow will be identical — only the URL changes.

@app.get("/mock-checkout/{payment_id}", response_class=HTMLResponse)
async def mock_checkout_page(payment_id: str, request: Request):
    """Simulated SimplyBlu hosted checkout page."""
    payment = _PAYMENTS.get(payment_id)
    if not payment:
        return HTMLResponse(
            "<h1>Payment not found</h1><p>No payment with that ID exists.</p>",
            status_code=404,
        )

    amount = f"R{payment['amount_minor'] / 100:.2f}"
    order_id = payment["order_id"]
    base = str(request.base_url).rstrip("/")

    # Callback URL the gateway posts back to (in this mock: our own confirm endpoint)
    return_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SimplyBlu Mock Checkout</title>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full">
        <div class="text-center mb-6">
            <p class="text-xs text-gray-400 tracking-wide uppercase">Secure Checkout</p>
            <h1 class="text-2xl font-bold mt-1">SimplyBlu</h1>
            <p class="text-xs text-gray-500 mt-1">(mock gateway — no real money moves)</p>
        </div>

        <div class="bg-gray-50 rounded-lg p-4 mb-6">
            <div class="flex justify-between text-sm mb-2">
                <span class="text-gray-500">Order</span>
                <span class="font-mono">{order_id}</span>
            </div>
            <div class="flex justify-between text-sm mb-2">
                <span class="text-gray-500">Payment ID</span>
                <span class="font-mono text-xs">{payment_id}</span>
            </div>
            <div class="flex justify-between text-lg font-bold border-t pt-3 mt-3">
                <span>Amount</span>
                <span>{amount}</span>
            </div>
        </div>

        <p class="text-sm text-gray-600 mb-6">
            In production this page is hosted by SimplyBlu. Clicking "Pay now"
            simulates a successful payment and redirects back to the merchant.
        </p>

        <div class="space-y-3">
            <form method="POST" action="{base}/mock-checkout/{payment_id}/pay">
                <button type="submit" class="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-bold">
                    Pay {amount} now
                </button>
            </form>
            <form method="POST" action="{base}/mock-checkout/{payment_id}/cancel">
                <button type="submit" class="w-full border border-gray-300 text-gray-600 py-3 rounded-lg">
                    Cancel
                </button>
            </form>
        </div>

        <p class="text-center text-xs text-gray-400 mt-6">
            Powered by RemotePay · SimplyBlu integration (mock)
        </p>
    </div>
</body>
</html>"""
    return HTMLResponse(return_html)


@app.post("/mock-checkout/{payment_id}/pay")
async def mock_checkout_pay(payment_id: str, request: Request):
    """Simulate a successful payment at the gateway, then redirect back to merchant."""
    payment = _PAYMENTS.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Mark paid
    payment["status"] = "paid"
    payment["paid_at"] = datetime.now(timezone.utc).isoformat()

    # Find the order and get its return_url (stored during create_payment via payment metadata)
    order_id = payment["order_id"]
    order = _ORDERS.get(order_id)
    if order:
        order["status"] = "paid"
        order["paid_at"] = payment["paid_at"]

    # Redirect back to the merchant return_url.
    # In production this would be a URL we passed to SimplyBlu at create-payment time.
    # For now, we route to our own /mock-return endpoint which redirects to the
    # generated site's thank-you page with a payment_id query param.
    return RedirectResponse(
        url=f"/mock-return?payment_id={payment_id}&order_id={order_id}",
        status_code=303,
    )


@app.post("/mock-checkout/{payment_id}/cancel")
async def mock_checkout_cancel(payment_id: str, request: Request):
    """Simulate a cancelled payment."""
    payment = _PAYMENTS.get(payment_id)
    if payment:
        payment["status"] = "cancelled"
    return RedirectResponse(url=f"/mock-return?payment_id={payment_id}&cancelled=1", status_code=303)


@app.get("/mock-return", response_class=HTMLResponse)
async def mock_return(payment_id: str, order_id: str = "", cancelled: str = ""):
    """
    Merchant return URL — where the gateway sends the customer after payment.

    In production, this would be a page on the shop's site (thank-you.html) that
    reads the payment_id from the URL and calls /api/orders/confirm.
    For this mock, we redirect straight to that behavior.
    """
    if cancelled:
        return HTMLResponse(f"""
            <!DOCTYPE html><html><head><title>Cancelled</title>
            <script src="https://cdn.tailwindcss.com"></script></head>
            <body class="bg-gray-100 min-h-screen flex items-center justify-center">
                <div class="bg-white rounded-2xl p-8 text-center max-w-md">
                    <div class="text-5xl mb-4">❌</div>
                    <h1 class="text-2xl font-bold mb-2">Payment cancelled</h1>
                    <p class="text-gray-500">You can try again from the shop.</p>
                    <p class="text-xs text-gray-400 mt-4">Payment ID: {payment_id}</p>
                </div>
            </body></html>
        """)

    # Auto-confirm the order server-side
    payment = _PAYMENTS.get(payment_id)
    if not payment:
        return HTMLResponse("<h1>Unknown payment</h1>", status_code=404)

    oid = order_id or payment["order_id"]
    order = _ORDERS.get(oid)
    if not order:
        return HTMLResponse(f"<h1>Order {oid} not found</h1>", status_code=404)

    # If already confirmed, don't re-dispatch
    if order["status"] in ("confirmed", "dispatched", "confirmed_pending_dispatch"):
        confirm = {"status": order["status"], "order_id": oid, "note": "already confirmed"}
    else:
        # Run the confirm flow inline (same as /api/orders/confirm)
        vat_minor = calculate_vat(order["total_minor"])
        tax_entry = record_transaction(
            order_id=oid,
            payment_id=payment_id,
            merchant_id=order["merchant_id"],
            amount_minor=order["total_minor"],
            vat_minor=vat_minor,
            description=f"Order {oid}",
            customer_reference=None,
        )
        order["status"] = "confirmed"
        order["tax_entry"] = tax_entry
        order["confirmed_at"] = datetime.now(timezone.utc).isoformat()

        dispatch_info = {"dispatched": False}
        delivery_area = (order.get("delivery") or {}).get("area")
        if delivery_area:
            match = rider_dispatch.find_best_rider(delivery_area)
            if match:
                assignment = rider_dispatch.assign(order_id=oid, rider_id=match["rider"]["id"], area=delivery_area)
                order["status"] = "dispatched"
                order["rider"] = match["rider"]
                order["assignment"] = assignment
                dispatch_info = {
                    "dispatched": True,
                    "rider": match["rider"],
                    "score": match["score"],
                    "distance_km": match["distance_km"],
                }
            else:
                order["status"] = "confirmed_pending_dispatch"
                dispatch_info = {"dispatched": False, "reason": "no_available_rider"}

        confirm = {
            "status": order["status"],
            "order_id": oid,
            "vat_minor": vat_minor,
            "vat_display": f"R{vat_minor / 100:.2f}",
            "dispatch": dispatch_info,
        }

    rider = (confirm.get("dispatch") or {}).get("rider") or {}
    rider_line = (
        f"<p class='text-gray-600 mt-2'>🛵 Rider <b>{rider.get('full_name')}</b> is on the way.</p>"
        if rider else
        "<p class='text-gray-500 mt-2 text-sm'>No rider available yet — will dispatch shortly.</p>"
    )

    return HTMLResponse(f"""<!DOCTYPE html>
<html><head>
    <title>Payment Complete</title>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-sm p-8 max-w-md w-full text-center">
        <div class="text-6xl mb-4">✅</div>
        <h1 class="text-3xl font-bold mb-2">Thank you!</h1>
        <p class="text-gray-600 mb-6">Your order has been placed.</p>

        <div class="bg-gray-50 rounded-lg p-4 text-left text-sm space-y-2 mb-6">
            <div class="flex justify-between"><span class="text-gray-500">Order</span><span class="font-mono">{confirm['order_id']}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">Status</span><span class="capitalize">{confirm['status']}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">VAT recorded</span><span>{confirm.get('vat_display', '—')}</span></div>
        </div>

        {rider_line}

        <p class="text-xs text-gray-400 mt-6">
            This page is a stub. In production, the gateway redirects to the
            shop's own thank-you.html, which reads payment_id from the URL and
            calls /api/orders/confirm.
        </p>
    </div>
</body></html>""")


@app.get("/api/payments/{payment_id}")
async def get_payment(payment_id: str):
    """Return payment state (used by the return URL to verify)."""
    payment = _PAYMENTS.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8100, reload=True)
