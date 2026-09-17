# Ubernie Architecture Decision Log

## 2026-06-09 – Next Phase Decision

**Decision:** Build all four requested systems in the following order:

1. Global Database Schema
2. Conversion Event Tracking System
3. Affiliate Payout Engine
4. Master Orchestrator Agent

**Rationale:**
- Global Schema is the foundation for all cross-system intelligence.
- Event Tracking requires the schema.
- Payout Engine requires both schema + events.
- Master Orchestrator is the final integration layer.

This prevents data fragmentation and ensures the 4-engine ecosystem (C6 + Ubernie + RemotePay + Affiliates) can operate with a single source of truth.

**Status:** Execution completed.

**Phase 1 (Global Schema + Contracts)** completed earlier.

**Phase 2 (Agent Intelligence Layer)** now completed:
- Discovery Agent + Search Demand tracking
- Industry Factory Agent + Subdomain Factory
- Business In A Box Agent (Starter/Growth/Scale bundles)
- RemotePay Activation Agent
- Master Orchestrator Agent (coordinates all agents)

The self-expanding intelligence layer is now live.
---

## 2026-09-17 – Web Department: Integration Layer Before Deployment

**Decision:** Build the integration layer (RemotePay, Ubernie Delivery, Tax AI) before the deployment layer.

**Rationale:**
- Deployment is cheap and reversible; revenue path is the critical path.
- Must prove ONE shop end-to-end (real payment, real delivery, real tax record) before scaling to 100+ shops.
- Deploying mock sites would burn merchant credibility on first contact.
- Integration requirements (env vars, endpoints, secrets) define deployment requirements, not the other way around.

**Alternatives considered:**
- (A) Deploy first — rejected: ships broken UX.
- (B) Integrate first — CHOSEN.
- (C) Parallel — rejected: splits focus, risk of half-built layers.

**Integration target refinement (sub-decision):**
- Integrate with `/api/v1/payment-links` (SimplyBlu + ledger) as primary, NOT `/api/v1/payments` (PayFast legacy).
- Reason: `payment-links` has idempotency, multi-tenancy (merchant_id/brand_id/source_system), and persistent ledger — required for the Ubernie flywheel and Tax AI consumption.

**Resilience decision (sub-decision):**
- RemotePay client uses a 3-tier fallback: payment-links → payments (legacy) → mock.
- `REMOTEPAY_MODE` env var controls behavior: auto | live | legacy | mock.
- Justification: unblocks web-department development while RemotePay's SimplyBlu + MongoDB are being configured. Auto-upgrades when RemotePay is ready. Mock is clearly logged and never used in production.

**Dependencies:**
- RemotePay backend running with DATABASE_URL (MongoDB) + SimplyBlu creds for full functionality.
- Currently: not running, so we test via mock path — REAL integration deferred to when RemotePay is up.

**Revisit criteria:**
- Once 1 real shop completes 1 real paid order + 1 real delivery + 1 real tax record: proceed to deployment layer.

**Related:** commit a33ff4a (web-department scaffold)

---

## 2026-09-17 – Corrected Build Order: Waitlist Engine Before Dispatch

**Decision:** Build the two-sided waitlist engine (shops + riders) BEFORE rider dispatch.

**Context:** Original plan proposed rider dispatch next. This was wrong — dispatch assumes riders exist, but riders only exist after the waitlist activates a zone. Building dispatch first would have produced dead code.

**Rationale:**
- The waitlist is the entry point for the entire flywheel.
- Shops and riders both enter through it; nothing else functions without it.
- Dispatch requires active riders, which requires an activated zone, which requires the waitlist thresholds (15 shops + 3 riders).

**Corrected order:**
1. Waitlist engine (shops + riders) ← DONE (this commit)
2. Rider dispatch (reads from waitlist active zones)
3. Real RemotePay integration (riders must be paid)
4. Deployment layer (deploy only working shops)

**Single source of truth:**
- `integration/waitlist.py` is authoritative for "is this zone active?"
- `integration/ubernie_delivery.py` now queries the waitlist instead of hardcoding zones.
- Removed the `_ACTIVE_ZONES` dict — no more hardcoded truth.

**Success criteria (met):**
- 15 shops in Soweto → zone shows 15/15 shops
- 3 riders in Soweto → zone auto-activates
- `/api/delivery/check?area=Soweto` flips from available:false → available:true
- Pure data change; zero code change required for activation.

**Related:** commits a33ff4a, 23cc74c, 27f854b

---

## 2026-09-17 – Rider Dispatch Engine

**Decision:** Build rider dispatch reading from the waitlist's active-zone riders.

**Rationale:**
- Completes the flywheel: order → payment → tax → **rider assigned** → delivered.
- Riders are sourced from the waitlist (single source of truth), not fabricated.
- Dispatch is gated by zone activation: cannot assign a rider in an inactive zone.

**Architecture:**
- `integration/rider_dispatch.py` — scoring engine (distance/rating/load/acceptance).
- Riders registered via waitlist are implicitly AVAILABLE.
- Availability state (available/busy) lives in `data/rider_state.jsonl` (append-only).
- `find_best_rider()` returns top + 2 alternatives for auditability.

**Load balancing:**
- Scoring penalizes riders with active jobs (-5 per job).
- 3 riders + 3 orders → all 3 get distinct assignments (verified by test).

**Completion flow:**
- `POST /api/riders/{id}/complete?order_id=X` frees the rider.
- Freed rider is immediately eligible for new orders.

**Success criteria (met):**
- Order confirmed → best rider auto-assigned.
- Second concurrent order → different rider (load balancing works).
- Completed delivery → rider returns to AVAILABLE.
- All driven by data (waitlist + rider_state), zero hardcoded zones.

**Related:** commits a33ff4a, 23cc74c, 27f854b, [this commit]

---

## 2026-09-17 – SimplyBlu is the Official Payment Provider

**Decision:** SimplyBlu (via `/api/v1/payment-links`) is the official RemotePay
payment path. PayFast and PayGate are deferred to a later phase as secondary
providers only.

**Rationale:**
- `payment-links` supports idempotency, multi-tenancy, and the persistent ledger.
- PayFast (`/api/v1/payments`) is legacy in-memory — not suitable for production.
- The web-department RemotePayClient already targets `payment-links` as primary.

**Impact on web-department:**
- Mock fallback stays only for local dev until SimplyBlu creds are set.
- No code change required — client auto-upgrades to real SimplyBlu when env ready.
- Future PayFast/PayGate integration goes through a provider-adapter layer (deferred).

**Config needed (when ready):**
- `SIMPLYBLU_API_URL`, `SIMPLYBLU_PUBLIC_KEY`, `SIMPLYBLU_PRIVATE_KEY` in RemotePay `.env`
- `DATABASE_URL` (MongoDB) in RemotePay `.env`
- `PAYMENT_PROVIDER=simplyblu`

**Related:** DEC-2026-09-17-001 (integration before deployment)

---

## 2026-09-17 – Generated Sites Call the Web Department API

**Decision:** Wire generated shop sites to call the web-department API for
delivery checks, payment creation, and order confirmation.

**Context:** All 6 flywheel layers worked (verified end-to-end via curl), but
generated sites pointed at relative paths (`/api/remotepay/create-payment`) that
resolve to nothing on a deployed subdomain. Machinery without a client is
unproven in practice.

**Changes:**
- `builder/site_renderer.py` injects `WEB_DEPARTMENT_PUBLIC_URL` into every page
  as `window.C6_CONFIG.apiBaseUrl`.
- New `assets/c6-api.js` — a minimal client used by all generated pages
  (`checkDelivery`, `createPayment`, `confirmOrder`).
- Updated `cart.js` — checkout button now calls the API and handles the response.
- New endpoint `POST /api/sites/{shop_id}/generate` — generate a storefront via API.
- Static mount at `/sites/{shop_id}/` — preview generated sites from the API.

**Not yet done (deferred):**
- Product grid population from real product data (currently no products rendered).
- Thank-you page after confirm (currently shows inline status).
- Real payment redirect flow (currently mock-completes after 400ms).

**Success criteria:**
- Generated site loads in browser.
- Cart works.
- Delivery check returns real waitlist status.
- Clicking "Pay" hits the API, creates an order, confirms it, dispatches a rider.

**Related:** commits a33ff4a, 23cc74c, 27f854b, 625ca63

---

## 2026-09-17 – Full Storefront Renderer

**Decision:** Expand the site renderer from a shell into a full interactive storefront.

**What was added:**
- `data/products.json` + `data/shop.json` written per site (source of truth for the JS).
- `assets/products.js` — client-side product grid renderer, fetches products.json.
- `assets/cart.js` — full cart UI: add, remove, total, checkout modal, order submission.
- `assets/c6-api.js` — delivery check, createPayment, confirmOrder.
- New page: `thank-you.html` — reads last order from sessionStorage.
- Menu, About, Contact pages now populated from shop data.
- `openDeliveryWidget()` restored — calls `/api/delivery/check` live.

**Full browser flow now works:**
1. Open `http://127.0.0.1:8100/sites/{shop_id}/index.html`
2. See hero + featured products (loaded from `data/products.json`)
3. Click "Add" on a product → cart badge updates
4. Open cart modal → see line items + total
5. Click "Checkout" → checkout.html
6. Fill customer details, click "Check delivery" → real waitlist check
7. Click "Pay with RemotePay" → API call → dispatch → thank-you redirect

**Known limitations (accepted for now):**
- Payment still mock (SimplyBlu credentials pending).
- Checkout flow confirms immediately instead of redirecting to actual payment gateway.
- Product images not supported yet (text-only cards).

**Related:** commits a33ff4a → 9ad77f9
