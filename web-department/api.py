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

import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

from integration import waitlist, rider_dispatch
from db.engine import init_db
from auth.security import hash_password, verify_password, create_access_token
from auth.dependencies import current_user, require_role
from db import repositories as repo
from db.repositories import PaymentStateConflict, OrderStateConflict
from builder.site_generator import SiteGenerator
from builder.site_renderer import SiteRenderer
from integration.remotepay_client import RemotePayClient, RemotePayError
from integration.catalogue import CatalogueError, canonicalize_cart
from integration.ubernie_delivery import UbernieDeliveryClient
from integration.taxai_hook import calculate_vat, record_transaction

logging.basicConfig(level=logging.INFO)
init_db()  # create tables if not exist
log = logging.getLogger("web-department.api")

app = FastAPI(title="Ubernie Web Department", version="0.3.0")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if x.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"] if ENVIRONMENT != "production" else []

if ENVIRONMENT == "production" and os.getenv("JWT_SECRET", "dev-secret-change-in-production") == "dev-secret-change-in-production":
    raise RuntimeError("JWT_SECRET must be set to a non-default value in production")
if ENVIRONMENT == "production" and os.getenv("REMOTEPAY_MODE", "auto").lower() != "live":
    raise RuntimeError("REMOTEPAY_MODE=live is required in production; mock/legacy fallback is disabled")

import os as _os_mount
_SITES_DIR = _os_mount.getenv("GENERATED_SITES_DIR", "generated-sites")
_os_mount.makedirs(_SITES_DIR, exist_ok=True)

app.mount("/sites", StaticFiles(directory=_SITES_DIR, html=True), name="sites")

import os as _os_dash
_STATIC_DIR = _os_dash.path.join(_os_dash.path.dirname(_os_dash.path.abspath(__file__)), "static")
_os_dash.makedirs(_STATIC_DIR, exist_ok=True)
app.mount("/dashboard", StaticFiles(directory=_os_dash.path.join(_STATIC_DIR, "dashboard"), html=True), name="dashboard")
app.mount("/rider", StaticFiles(directory=_os_dash.path.join(_STATIC_DIR, "rider"), html=True), name="rider")
app.mount("/signup", StaticFiles(directory=_os_dash.path.join(_STATIC_DIR, "signup"), html=True), name="signup")
app.mount("/track", StaticFiles(directory=_os_dash.path.join(_STATIC_DIR, "track"), html=True), name="track")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-RemotePay-Signature"],
)

remotepay = RemotePayClient()
delivery = UbernieDeliveryClient()

def _block_mock_checkout_in_production() -> None:
    """Keep the development-only mock gateway unreachable in production."""
    if ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")




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


class RemotePayWebhookRequest(BaseModel):
    payment_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    brand_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    order_id: str | None = None
    status: str
    amount_minor: int | None = None
    currency: str = Field(min_length=3, max_length=3)


# ---------------------------------------------------------------------------
# Auth Schemas
# ---------------------------------------------------------------------------
class ShopSignupRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1)
    business_name: str = Field(min_length=1)
    phone: str = Field(min_length=5)
    area: str = Field(min_length=1)


class RiderSignupRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1)
    phone: str = Field(min_length=5)
    area: str = Field(min_length=1)
    vehicle: str = "Zeebee Greenscooter"
    licence_number: str = ""


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


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
    import traceback
    try:
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
    except Exception as e:
        tb = traceback.format_exc()
        print("\n=== WAITLIST SHOP REGISTRATION FAILED ===")
        print(tb)
        print("=== END TRACEBACK ===\n")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.post("/api/waitlist/rider")
async def join_waitlist_rider(req: RiderWaitlistRequest):
    import traceback
    try:
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
    except Exception as e:
        tb = traceback.format_exc()
        print("\n=== WAITLIST RIDER REGISTRATION FAILED ===")
        print(tb)
        print("=== END TRACEBACK ===\n")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


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

    try:
        canonical_items, total_minor = canonicalize_cart(
            shop_id=req.shop_id,
            items=[item.model_dump() for item in req.items],
            generated_sites_dir=os.getenv("GENERATED_SITES_DIR", "generated-sites"),
        )
    except CatalogueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    # Merchant identity is derived from the published shop, never trusted from checkout input.
    merchant_id = f"merchant_{req.shop_id}"

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
            merchant_id=merchant_id,
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

    transaction_id = payment.get("transaction_id")

    # Persist order + payment records before reporting an incomplete provider identity,
    # so a created provider payment is not lost from the local reconciliation trail.
    repo.create_order(
        order_id=order_id,
        shop_id=req.shop_id,
        merchant_id=merchant_id,
        items=canonical_items,
        total_minor=total_minor,
        delivery=delivery_result,
    )
    repo.create_payment_record(
        payment_id=payment["payment_id"],
        order_id=order_id,
        amount_minor=total_minor,
        provider=payment["provider_path"],
        provider_reference=transaction_id,
        payment_url=payment["payment_url"],
    )

    if not transaction_id:
        raise HTTPException(
            status_code=502,
            detail="RemotePay response is missing transaction identity; payment was recorded for reconciliation",
        )

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
    order = repo.get_order(req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] in ("confirmed", "dispatched", "delivered", "confirmed_pending_dispatch"):
        return {"status": "already_confirmed", "order_id": req.order_id}

    payment = repo.get_payment(req.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment["order_id"] != req.order_id:
        raise HTTPException(status_code=409, detail="Payment does not belong to order")
    if payment["amount_minor"] != order["total_minor"]:
        raise HTTPException(status_code=409, detail="Payment amount does not match order")
    if payment["status"] != "paid":
        raise HTTPException(status_code=409, detail="Payment is not verified as paid")

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

    repo.update_order_status(
        req.order_id,
        status="confirmed",
        payment_id=req.payment_id,
        vat_minor=vat_minor,
        mark_confirmed=True,
    )

    dispatch_result: Dict[str, Any] = {"dispatched": False}
    delivery_area = (order.get("delivery") or {}).get("area")
    if delivery_area:
        match = rider_dispatch.find_best_rider(delivery_area)
        if match:
            rider_dispatch.assign(
                order_id=req.order_id,
                rider_id=match["rider"]["id"],
                area=delivery_area,
            )
            dispatch_result = {
                "dispatched": True,
                "rider": match["rider"],
                "score": match["score"],
                "distance_km": match["distance_km"],
                "alternatives": match["alternatives"],
            }
        else:
            repo.update_order_status(req.order_id, status="confirmed_pending_dispatch")
            dispatch_result = {
                "dispatched": False,
                "reason": "no_available_rider",
                "message": "Order confirmed. No rider currently available; will retry.",
            }

    final = repo.get_order(req.order_id)
    return {
        "status": final["status"],
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
async def complete_delivery(rider_id: str, order_id: str, user: dict = Depends(current_user)):
    if user["role"] != "admin" and user["user_id"] != rider_id:
        raise HTTPException(status_code=403, detail="You can only complete your own deliveries")
    record = rider_dispatch.release(rider_id=rider_id, order_id=order_id, reason="completed")
    return {"status": "completed", "release": record}


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, user: dict = Depends(current_user)):
    order = repo.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Admin: unrestricted. Shop: must own. Rider: must be assigned or unassigned+in their area.
    if user["role"] == "admin":
        return order
    if user["role"] == "shop":
        u = repo.get_user_by_id(user["user_id"])
        if u and u.shop_id and order["shop_id"] == u.shop_id:
            return order
        raise HTTPException(status_code=403, detail="Not your order")
    if user["role"] == "rider":
        if order.get("rider_id") and order["rider_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not assigned to you")
        return order
    raise HTTPException(status_code=403, detail="Forbidden")


# ---------------------------------------------------------------------------
# Site generation (per-shop storefront)
# ---------------------------------------------------------------------------
import os as _os

@app.post("/api/sites/{shop_id}/generate")
async def generate_site(shop_id: str, req: GenerateSiteRequest, user: dict = Depends(current_user)):
    """Generate a static storefront for a shop. Only the owning shop or admin can trigger."""
    if user["role"] != "admin":
        u = repo.get_user_by_id(user["user_id"])
        if not u or u.role != "shop":
            raise HTTPException(status_code=403, detail="Only shops or admin can generate sites")
        if u.shop_id != shop_id:
            raise HTTPException(status_code=403, detail="You can only generate your own site")
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
    _block_mock_checkout_in_production()
    payment = repo.get_payment(payment_id)
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
    _block_mock_checkout_in_production()
    payment = repo.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Mark paid with monotonic compare-and-set transitions.
    try:
        paid = repo.mark_payment_paid(payment_id)
        if paid:
            repo.mark_order_paid(paid["order_id"], payment_id)
    except (PaymentStateConflict, OrderStateConflict) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    order_id = payment["order_id"]

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
    _block_mock_checkout_in_production()
    try:
        repo.mark_payment_cancelled(payment_id)
    except PaymentStateConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RedirectResponse(url=f"/mock-return?payment_id={payment_id}&cancelled=1", status_code=303)


@app.get("/mock-return", response_class=HTMLResponse)
async def mock_return(payment_id: str, order_id: str = "", cancelled: str = ""):
    """
    Merchant return URL — where the gateway sends the customer after payment.

    In production, this would be a page on the shop's site (thank-you.html) that
    reads the payment_id from the URL and calls /api/orders/confirm.
    For this mock, we redirect straight to that behavior.
    """
    _block_mock_checkout_in_production()
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

    # Mock payments are already marked paid above; use the same authoritative
    # confirmation path as production rather than maintaining a second flow.
    payment = repo.get_payment(payment_id)
    if not payment:
        return HTMLResponse("<h1>Unknown payment</h1>", status_code=404)
    oid = order_id or payment["order_id"]
    try:
        confirm = await confirm_order(ConfirmOrderRequest(order_id=oid, payment_id=payment_id))
    except HTTPException as exc:
        return HTMLResponse(f"<h1>Payment confirmation failed</h1><p>{exc.detail}</p>", status_code=exc.status_code)

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


@app.post("/api/webhooks/remotepay")
async def remotepay_webhook(req: RemotePayWebhookRequest, request: Request):
    """Authoritative RemotePay payment-state boundary.

    The webhook marks the local payment paid only after signature verification.
    Browser redirects are never treated as payment proof.
    """
    raw = await request.body()
    secret = os.getenv("REMOTEPAY_WEBHOOK_SECRET", "")
    supplied = request.headers.get("X-RemotePay-Signature", "")
    if ENVIRONMENT == "production":
        if not secret:
            raise HTTPException(status_code=503, detail="RemotePay webhook secret is not configured")
        expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payment = repo.get_payment(req.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if req.order_id and req.order_id != payment["order_id"]:
        raise HTTPException(status_code=409, detail="Payment/order mismatch")
    order = repo.get_order(payment["order_id"])
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not payment.get("provider_reference"):
        raise HTTPException(status_code=409, detail="Payment transaction identity is missing; reconciliation is required")
    if req.transaction_id != payment["provider_reference"]:
        raise HTTPException(status_code=409, detail="Payment transaction mismatch")
    if req.merchant_id != order["merchant_id"]:
        raise HTTPException(status_code=409, detail="Payment merchant mismatch")
    if req.brand_id != "ubernie" or req.source_system != "c6_web_department":
        raise HTTPException(status_code=409, detail="Payment brand/source mismatch")
    if req.currency.upper() != payment["currency"].upper():
        raise HTTPException(status_code=409, detail="Payment currency mismatch")
    if req.amount_minor is not None and req.amount_minor != payment["amount_minor"]:
        raise HTTPException(status_code=409, detail="Payment amount mismatch")

    status = req.status.lower()
    if status in {"paid", "completed", "success", "succeeded"}:
        try:
            paid = repo.mark_payment_paid(req.payment_id)
            if not paid:
                raise HTTPException(status_code=404, detail="Payment not found")
            repo.mark_order_paid(payment["order_id"], req.payment_id)
        except (PaymentStateConflict, OrderStateConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"accepted": True, "status": "paid", "payment_id": req.payment_id, "order_id": payment["order_id"]}
    if status in {"cancelled", "canceled", "failed", "expired"}:
        target_status = "cancelled" if status in {"cancelled", "canceled"} else status
        try:
            repo.mark_payment_cancelled(req.payment_id, status=target_status)
        except PaymentStateConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"accepted": True, "status": target_status, "payment_id": req.payment_id, "order_id": payment["order_id"]}
    return {"accepted": True, "status": status, "payment_id": req.payment_id, "order_id": payment["order_id"]}


@app.get("/api/payments/{payment_id}")
async def get_payment(payment_id: str):
    """Return payment state (used by the return URL to verify)."""
    payment = repo.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.post("/api/auth/signup/shop")
async def signup_shop(req: ShopSignupRequest):
    """Register a shop owner + automatically add them to the waitlist."""
    try:
        user = repo.create_user(
            role="shop", email=req.email, password_hash=hash_password(req.password),
            full_name=req.full_name, phone=req.phone, area=req.area,
            business_name=req.business_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

    # Add to waitlist
    waitlist.register_shop(
        business_name=req.business_name, area=req.area, industry="retail",
        email=req.email, phone=req.phone, user_id=user["id"],
    )

    token = create_access_token(user_id=user["id"], role=user["role"], email=user["email"])
    return {"user": user, "access_token": token, "token_type": "bearer"}


@app.post("/api/auth/signup/rider")
async def signup_rider(req: RiderSignupRequest):
    try:
        user = repo.create_user(
            role="rider", email=req.email, password_hash=hash_password(req.password),
            full_name=req.full_name, phone=req.phone, area=req.area,
            vehicle=req.vehicle, licence_number=req.licence_number,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

    waitlist.register_rider(
        full_name=req.full_name, area=req.area, vehicle=req.vehicle,
        phone=req.phone, email=req.email, licence_number=req.licence_number,
        user_id=user["id"],
    )

    token = create_access_token(user_id=user["id"], role=user["role"], email=user["email"])
    return {"user": user, "access_token": token, "token_type": "bearer"}


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    u = repo.get_user_by_email(req.email)
    if not u or not u.password_hash or not verify_password(req.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user_id=u.id, role=u.role, email=u.email)
    return {
        "user": {
            "id": u.id, "role": u.role, "email": u.email,
            "full_name": u.full_name, "area": u.area, "shop_id": u.shop_id,
        },
        "access_token": token,
        "token_type": "bearer",
    }


@app.get("/api/auth/me")
async def whoami(user: dict = Depends(current_user)):
    u = repo.get_user_by_id(user["user_id"])
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": u.id, "role": u.role, "email": u.email,
        "full_name": u.full_name, "area": u.area,
        "shop_id": u.shop_id,
    }


# ---------------------------------------------------------------------------
# Shop dashboard endpoints (JWT: role=shop only)
# ---------------------------------------------------------------------------
@app.get("/api/shop/stats")
async def get_shop_stats(user: dict = Depends(require_role("shop", "admin"))):
    u = repo.get_user_by_id(user["user_id"])
    if not u or not u.shop_id:
        raise HTTPException(status_code=404, detail="No shop_id for this account")
    return repo.shop_stats(u.shop_id)


@app.get("/api/shop/orders")
async def get_shop_orders(limit: int = 100, user: dict = Depends(require_role("shop", "admin"))):
    u = repo.get_user_by_id(user["user_id"])
    if not u or not u.shop_id:
        raise HTTPException(status_code=404, detail="No shop_id for this account")
    return {"shop_id": u.shop_id, "orders": repo.list_orders_for_shop(u.shop_id, limit)}


# ---------------------------------------------------------------------------
# Rider app endpoints (JWT: role=rider only)
# ---------------------------------------------------------------------------
@app.get("/api/rider/stats")
async def get_rider_stats(user: dict = Depends(require_role("rider", "admin"))):
    return repo.rider_stats(user["user_id"])


@app.get("/api/rider/jobs")
async def get_rider_jobs(limit: int = 100, user: dict = Depends(require_role("rider", "admin"))):
    return repo.list_jobs_for_rider(user["user_id"], limit)


# ---------------------------------------------------------------------------
# Public order tracking (no auth — customer-facing)
# ---------------------------------------------------------------------------
@app.get("/api/track/{order_id}")
async def track_order(order_id: str):
    """Public order tracking — returns only safe fields, no PII."""
    order = repo.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Safe subset — no customer email, no payment references
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "items": [{"name": i.get("name"), "qty": i.get("qty")} for i in (order["items"] or [])],
        "total_minor": order["total_minor"],
        "delivery": {
            "area": (order.get("delivery") or {}).get("area"),
            "eta_minutes": (order.get("delivery") or {}).get("eta_minutes"),
            "fee_display": (order.get("delivery") or {}).get("fee_display"),
        } if order.get("delivery") else None,
        "created_at": order.get("created_at"),
        "dispatched_at": order.get("dispatched_at"),
        "delivered_at": order.get("delivered_at"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8100")), reload=ENVIRONMENT != "production")