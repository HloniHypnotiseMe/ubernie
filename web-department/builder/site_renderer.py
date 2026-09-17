#!/usr/bin/env python3
"""
C6 Website Department — Site Renderer

Renders generated site config into deployable HTML/CSS/JS.
Injects C6_API_BASE_URL so the generated JS knows where to call the
web-department API (payment, delivery, orders).
"""
from __future__ import annotations

import os
from pathlib import Path


class SiteRenderer:
    def __init__(self, site_config, output_dir, api_base_url: str | None = None):
        self.site = site_config
        self.output = Path(output_dir)
        self.output.mkdir(parents=True, exist_ok=True)
        self.api_base_url = (
            api_base_url
            or os.getenv("WEB_DEPARTMENT_PUBLIC_URL", "http://127.0.0.1:8100")
        ).rstrip("/")

    def render(self):
        """Render all pages + shared assets."""
        self._render_index()
        self._render_page("menu", self.site["pages"].get("menu"))
        self._render_page("shop", self.site["pages"].get("shop"))
        self._render_page("about", self.site["pages"].get("about"))
        self._render_page("contact", self.site["pages"].get("contact"))
        self._render_checkout()
        self._render_assets()
        return {"rendered_to": str(self.output), "api_base_url": self.api_base_url}

    def _render_index(self):
        home = self.site["pages"].get("home", {})
        hero = home.get("hero", {})
        config = self.site["config"]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['site_name']} — {config['tagline']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="assets/c6-config.js"></script>
    <script src="assets/c6-api.js"></script>
    <script src="assets/cart.js"></script>
    <style>
        :root {{ --primary: {config['primary_color']}; }}
        .btn-primary {{ background: var(--primary); color: white; }}
    </style>
</head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-sm sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <h1 class="text-2xl font-bold" style="color: var(--primary);">{config['site_name']}</h1>
            <div class="flex gap-6 items-center">
                <a href="index.html" class="hover:opacity-70">Home</a>
                <a href="menu.html" class="hover:opacity-70">Menu</a>
                <a href="about.html" class="hover:opacity-70">About</a>
                <a href="contact.html" class="hover:opacity-70">Contact</a>
                <button onclick="openCart()" class="btn-primary px-4 py-2 rounded-lg">
                    Cart <span id="cart-count">0</span>
                </button>
            </div>
        </div>
    </nav>

    <section class="py-20 px-4" style="background: linear-gradient(135deg, {config['primary_color']}22, transparent);">
        <div class="max-w-4xl mx-auto text-center">
            <h2 class="text-5xl font-bold mb-4">{hero.get('headline', config['site_name'])}</h2>
            <p class="text-xl text-gray-600 mb-8">{hero.get('subheadline', '')}</p>
            <a href="menu.html" class="btn-primary px-8 py-4 rounded-lg text-lg font-bold inline-block">
                {hero.get('cta', 'Order Now')}
            </a>
        </div>
    </section>

    <section class="py-16 px-4 bg-white">
        <div class="max-w-7xl mx-auto">
            <h3 class="text-3xl font-bold mb-8 text-center">Featured</h3>
            <div id="featured-products" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Populated by JS from /data/products.json -->
            </div>
        </div>
    </section>

    <section class="py-16 px-4" style="background: var(--primary); color: white;">
        <div class="max-w-4xl mx-auto text-center">
            <h3 class="text-3xl font-bold mb-4">🛵 Delivery Available</h3>
            <p class="text-lg mb-6">Get it delivered to your door in 30-45 minutes.</p>
            <button onclick="openDeliveryWidget()" class="bg-white text-gray-900 px-8 py-3 rounded-lg font-bold">
                Check Delivery
            </button>
        </div>
    </section>

    <footer class="bg-gray-900 text-white py-12 px-4">
        <div class="max-w-7xl mx-auto text-center">
            <p>{config['site_name']}</p>
            <p class="text-sm text-gray-400 mt-2">
                {config['contact'].get('phone', '')} · {config['contact'].get('email', '')}
            </p>
            <p class="text-xs text-gray-500 mt-4">Powered by RemotePay · C6 SaaS</p>
        </div>
    </footer>

    <div id="cart-modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div class="bg-white rounded-2xl p-8 max-w-md w-full mx-4">
            <h3 class="text-2xl font-bold mb-4">Your Cart</h3>
            <div id="cart-items"></div>
            <div class="mt-6 flex justify-between font-bold text-lg">
                <span>Total</span>
                <span id="cart-total">R0.00</span>
            </div>
            <button onclick="checkout()" class="btn-primary w-full py-4 rounded-lg mt-4 font-bold">
                Checkout with RemotePay
            </button>
            <button onclick="closeCart()" class="w-full py-2 mt-2 text-gray-500">Close</button>
        </div>
    </div>
</body>
</html>"""
        (self.output / "index.html").write_text(html, encoding="utf-8")

    def _render_page(self, name, config):
        if not config:
            return
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{config.get('title', name)} — {self.site['config']['site_name']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="assets/c6-config.js"></script>
    <script src="assets/c6-api.js"></script>
    <script src="assets/cart.js"></script>
</head>
<body>
    <nav class="bg-white shadow-sm px-4 py-4">
        <div class="max-w-7xl mx-auto">
            <a href="index.html" class="text-xl font-bold">{self.site['config']['site_name']}</a>
        </div>
    </nav>
    <main class="max-w-7xl mx-auto px-4 py-12">
        <h1 class="text-4xl font-bold mb-8">{config.get('title', name)}</h1>
        <div id="content-grid" class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Populated by JS -->
        </div>
    </main>
</body>
</html>"""
        (self.output / f"{name}.html").write_text(html, encoding="utf-8")

    def _render_checkout(self):
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Checkout</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="assets/c6-config.js"></script>
    <script src="assets/c6-api.js"></script>
    <script src="assets/cart.js"></script>
</head>
<body class="bg-gray-50">
    <div class="max-w-2xl mx-auto py-12 px-4">
        <h1 class="text-3xl font-bold mb-8">Checkout</h1>

        <div id="checkout-summary" class="bg-white rounded-xl p-6 shadow-sm mb-6">
            <div class="text-gray-500">Loading cart...</div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm mb-6">
            <h3 class="font-bold mb-4">Your Details</h3>
            <input id="customer-name" placeholder="Your name" class="w-full px-3 py-2 border rounded mb-3">
            <input id="customer-email" placeholder="Email" type="email" class="w-full px-3 py-2 border rounded mb-3">
            <input id="customer-address" placeholder="Delivery address" class="w-full px-3 py-2 border rounded mb-3">
            <input id="customer-area" placeholder="Area (e.g., Soweto)" class="w-full px-3 py-2 border rounded">
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm">
            <h3 class="font-bold mb-4">Delivery</h3>
            <button onclick="checkDeliveryAvailability()" class="px-4 py-2 border rounded-lg mb-4">Check availability</button>
            <div id="delivery-result" class="text-sm text-gray-600"></div>
            <label class="flex items-center gap-3 p-3 border rounded-lg mt-4">
                <input type="radio" name="delivery" value="ubernie" checked>
                <span>🛵 Ubernie Delivery</span>
            </label>
        </div>

        <button onclick="submitOrder()" id="pay-btn"
                class="w-full bg-green-600 hover:bg-green-700 text-white py-4 rounded-lg font-bold mt-6">
            Pay with RemotePay
        </button>

        <div id="order-status" class="mt-4 text-sm"></div>
    </div>
</body>
</html>"""
        (self.output / "checkout.html").write_text(html, encoding="utf-8")

    def _render_assets(self):
        assets_dir = self.output / "assets"
        assets_dir.mkdir(exist_ok=True)

        # --- config: API base URL + shop identifiers ---
        shop_id = self.site["shop"].get("id", "unknown")
        merchant_id = self.site["shop"].get("remotepay_merchant_id") or f"merchant_{shop_id}"
        config_js = (
            f"window.C6_CONFIG = {{\n"
            f"  apiBaseUrl: {self.api_base_url!r},\n"
            f"  shopId: {shop_id!r},\n"
            f"  merchantId: {merchant_id!r},\n"
            f"  brandId: 'ubernie',\n"
            f"  sourceSystem: 'c6_generated_site',\n"
            f"}};\n"
        )
        (assets_dir / "c6-config.js").write_text(config_js, encoding="utf-8")

        # --- c6-api.js: client for web-department API ---
        c6_api_js = """// C6 Web Department API client
const C6 = (() => {
  const base = () => (window.C6_CONFIG?.apiBaseUrl || '').replace(/\\/$/, '');
  const cfg = () => window.C6_CONFIG || {};

  async function checkDelivery(area) {
    const r = await fetch(base() + '/api/delivery/check?area=' + encodeURIComponent(area));
    if (!r.ok) throw new Error('Delivery check failed: ' + r.status);
    return r.json();
  }

  async function createPayment(items, opts = {}) {
    const payload = {
      shop_id: cfg().shopId,
      merchant_id: cfg().merchantId,
      items,
      customer_email: opts.email || null,
      customer_name: opts.name || null,
      delivery_area: opts.deliveryArea || null,
      return_url: opts.returnUrl || (location.origin + '/thank-you.html'),
      cancel_url: opts.cancelUrl || (location.origin + '/checkout.html'),
    };
    const r = await fetch(base() + '/api/remotepay/create-payment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error('Payment creation failed: ' + r.status);
    return r.json();
  }

  async function confirmOrder(orderId, paymentId) {
    const r = await fetch(base() + '/api/orders/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderId, payment_id: paymentId }),
    });
    if (!r.ok) throw new Error('Confirm failed: ' + r.status);
    return r.json();
  }

  return { checkDelivery, createPayment, confirmOrder };
})();
"""
        (assets_dir / "c6-api.js").write_text(c6_api_js, encoding="utf-8")

        # --- cart.js: cart UI + checkout flow ---
        cart_js = """// Shopping Cart — talks to C6 API
let cart = JSON.parse(localStorage.getItem('cart') || '[]');

function saveCart() { localStorage.setItem('cart', JSON.stringify(cart)); updateCartCount(); }

function addToCart(id, name, price) {
  const existing = cart.find(i => i.id === id);
  if (existing) existing.qty++;
  else cart.push({ id, name, price, qty: 1 });
  saveCart();
  alert(name + ' added to cart');
}

function updateCartCount() {
  const el = document.getElementById('cart-count');
  if (el) el.textContent = cart.reduce((s, i) => s + i.qty, 0);
}

function openCart() {
  const modal = document.getElementById('cart-modal');
  if (modal) modal.classList.remove('hidden');
  renderCart();
}

function closeCart() {
  const modal = document.getElementById('cart-modal');
  if (modal) modal.classList.add('hidden');
}

function renderCart() {
  const items = document.getElementById('cart-items');
  const total = document.getElementById('cart-total');
  if (!items) return;
  items.innerHTML = cart.map(i =>
    `<div class="flex justify-between py-2 border-b">
      <span>${i.name} x${i.qty}</span>
      <span>R${(i.price * i.qty).toFixed(2)}</span>
    </div>`
  ).join('');
  const sum = cart.reduce((s, i) => s + i.price * i.qty, 0);
  if (total) total.textContent = 'R' + sum.toFixed(2);
}

function checkout() { window.location.href = 'checkout.html'; }

async function checkDeliveryAvailability() {
  const area = document.getElementById('customer-area').value.trim();
  const el = document.getElementById('delivery-result');
  if (!area) { el.textContent = 'Enter an area first.'; return; }
  el.textContent = 'Checking...';
  try {
    const res = await C6.checkDelivery(area);
    if (res.available) {
      el.innerHTML = `✅ Delivery available in ${area} — ${res.fee_display} (~${res.eta_minutes} min)`;
    } else {
      el.innerHTML = `❌ ${res.message}`;
    }
  } catch (e) {
    el.textContent = 'Error: ' + e.message;
  }
}

async function submitOrder() {
  const btn = document.getElementById('pay-btn');
  const status = document.getElementById('order-status');
  btn.disabled = true;
  status.textContent = 'Creating order...';

  try {
    const name = document.getElementById('customer-name').value.trim();
    const email = document.getElementById('customer-email').value.trim();
    const area = document.getElementById('customer-area').value.trim();

    const order = await C6.createPayment(cart, { name, email, deliveryArea: area });

    status.innerHTML = `Order ${order.order_id} created. Amount: ${order.amount_display}. Redirecting to payment...`;

    // Simulate payment completion locally: hit /api/orders/confirm after a short delay.
    // In production, RemotePay redirects back with a payment_id and we confirm there.
    setTimeout(async () => {
      try {
        const confirm = await C6.confirmOrder(order.order_id, order.payment_id);
        const rider = confirm.dispatch?.rider;
        const riderLine = rider
          ? `<br>🛵 Rider <b>${rider.full_name}</b> assigned (${confirm.dispatch.distance_km} km, score ${confirm.dispatch.score})`
          : `<br>⏳ No rider available yet — will dispatch shortly.`;
        status.innerHTML = `<div class="p-4 bg-green-50 border border-green-200 rounded">
          ✅ <b>${confirm.status}</b><br>
          Order: ${confirm.order_id}<br>
          VAT recorded: ${confirm.vat_display}${riderLine}
        </div>`;
        cart = [];
        saveCart();
      } catch (e) {
        status.innerHTML = `<div class="p-4 bg-red-50 border border-red-200 rounded">Confirm error: ${e.message}</div>`;
        btn.disabled = false;
      }
    }, 400);

  } catch (e) {
    status.innerHTML = `<div class="p-4 bg-red-50 border border-red-200 rounded">Error: ${e.message}</div>`;
    btn.disabled = false;
  }
}

// Auto-render cart on checkout page
if (document.getElementById('checkout-summary')) {
  const sum = cart.reduce((s, i) => s + i.price * i.qty, 0);
  document.getElementById('checkout-summary').innerHTML = cart.length
    ? cart.map(i => `<div class="flex justify-between py-1"><span>${i.name} x${i.qty}</span><span>R${(i.price*i.qty).toFixed(2)}</span></div>`).join('')
      + `<div class="flex justify-between font-bold pt-3 border-t mt-3"><span>Subtotal</span><span>R${sum.toFixed(2)}</span></div>`
    : '<div class="text-gray-500">Your cart is empty.</div>';
}
updateCartCount();
"""
        (assets_dir / "cart.js").write_text(cart_js, encoding="utf-8")
