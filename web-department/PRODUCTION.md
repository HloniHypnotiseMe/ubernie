# Ubernie Web Department — production contract

This is the authoritative merchant website-generation and commerce service for Ubernie.

## Production invariants

- ENVIRONMENT=production
- REMOTEPAY_MODE=live — mock and legacy fallbacks are disabled by the API in production. All mock checkout, mock pay, mock cancel and mock return routes must return 404 in production.
- JWT_SECRET must be unique and non-default.
- REMOTEPAY_WEBHOOK_SECRET is mandatory.
- CORS_ALLOWED_ORIGINS must contain only real Ubernie/C6 origins.
- PostgreSQL is the production database; SQLite is development-only. Set `DATABASE_URL` using `postgresql+psycopg://USER:PASSWORD@HOST:5432/ubernie`; the production image installs psycopg v3 (`psycopg[binary]`) and rejects generic `postgresql://` and `postgresql+psycopg2://` URLs.
- Generated sites live on a persistent volume and are served through the reverse proxy.
- Browser redirects are not payment proof. Only a verified RemotePay webhook marks a payment paid.
- /api/orders/confirm refuses to confirm an unpaid, mismatched, or incorrectly valued payment.

## Service routes

- /health — liveness
- /dashboard/ — merchant dashboard
- /rider/ — rider app
- /signup/ — merchant/rider signup
- /track/ — customer tracking UI
- /sites/<shop_id>/ — generated merchant site
- /api/webhooks/remotepay — payment-state webhook

## Reverse proxy

Expose the service behind Caddy/Nginx rather than publishing port 8100 publicly. Set WEB_DEPARTMENT_PUBLIC_URL to the public API origin used by generated sites.

## Verification

From this directory:

    python -m compileall -q .
    pytest -q

Then prove the real chain separately:

generated site → RemotePay payment link → SimplyBlu payment → verified webhook → payment PAID → order CONFIRMED → dispatch → POD/delivery

## Business intelligence intake (initial foundation)

- `POST /api/intelligence/sources` — admin-only source registration. Collection is disabled by default; enabling requires recorded terms, permission and robots review.
- `POST /api/intelligence/jobs` — admin-only durable queue record. This endpoint does not fetch a page; a separately deployed worker is still required.
- `POST /api/intelligence/candidates` — admin-only evidence-backed business candidate intake. Candidate records remain private and pending review.
- `POST /api/intelligence/candidates/{id}/review` — admin-only approve/reject decision. Approval records a review decision but does not publish a public directory listing.

The initial implementation is an intake/evidence foundation, not yet a production crawler. Before enabling any source, confirm the source's terms, lawful collection basis, robots/access policy and rate limit. A future worker must additionally enforce DNS/IP SSRF protections, per-host throttling, robots policy at fetch time, bounded response sizes and safe content parsing.
