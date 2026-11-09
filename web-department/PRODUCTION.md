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
