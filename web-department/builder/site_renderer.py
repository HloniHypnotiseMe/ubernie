#!/usr/bin/env python3
"""
C6 Website Department — Site Renderer

Renders a complete, interactive storefront:
- index.html: hero, featured products grid, delivery banner, footer
- menu.html/shop.html: full product grid with Add-to-cart
- about.html: shop story
- contact.html: contact info + hours
- checkout.html: cart summary, delivery check, pay button
- thank-you.html: post-confirm landing
- assets/c6-config.js: injected config (API URL, shop id)
- assets/c6-api.js: client for web-department API
- assets/cart.js: cart UI + checkout flow
- assets/products.js: product grid renderer
- data/products.json: product/menu data
- data/shop.json: shop metadata
"""
from __future__ import annotations

import json
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
        """Render everything."""
        self._write_data()
        self._render_index()
        self._render_menu()
        self._render_about()
        self._render_contact()
        self._render_checkout()
        self._render_thank_you()
        self._render_assets()
        return {"rendered_to": str(self.output), "api_base_url": self.api_base_url}

    # ----------------------------------------------------------------
    # Data files
    # ----------------------------------------------------------------
    def _write_data(self):
        data_dir = self.output / "data"
        data_dir.mkdir(exist_ok=True)

        shop = self.site["shop"]
        products = (
            shop.get("menu_items")
            or shop.get("products")
            or shop.get("services")
            or []
        )
        # Normalize: ensure id, name, price exist
        normalized = []
        for i, p in enumerate(products):
            normalized.append({
                "id": p.get("id") or f"p{i+1}",
                "name": p.get("name", f"Item {i+1}"),
                "description": p.get("description", ""),
                "price": float(p.get("price", 0)),
                "category": p.get("category", ""),
            })

        (data_dir / "products.json").write_text(
            json.dumps(normalized, indent=2), encoding="utf-8"
        )
        (data_dir / "shop.json").write_text(
            json.dumps({
                "id": shop.get("id"),
                "name": shop.get("name"),
                "tagline": shop.get("tagline"),
                "story": shop.get("story", ""),
                "address": shop.get("address", ""),
                "phone": shop.get("phone", ""),
                "email": shop.get("email", ""),
                "hours": shop.get("hours", {}),
            }, indent=2),
            encoding="utf-8",
        )

    # ----------------------------------------------------------------
    # Pages
    # ----------------------------------------------------------------
    def _nav(self) -> str:
        return """<nav class="bg-white shadow-sm sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <a href="index.html" class="text-2xl font-bold" style="color: var(--primary);" id="nav-shop-name">Shop</a>
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
</nav>"""

    def _footer(self) -> str:
        return """<footer class="bg-gray-900 text-white py-12 px-4 mt-16">
    <div class="max-w-7xl mx-auto text-center">
        <p id="footer-shop-name" class="text-lg font-bold">Shop</p>
        <p class="text-sm text-gray-400 mt-2" id="footer-contact">—</p>
        <p class="text-xs text-gray-500 mt-4">Powered by RemotePay · C6 SaaS</p>
    </div>
</footer>"""

    def _cart_modal(self) -> str:
        return """<div id="cart-modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
    <div class="bg-white rounded-2xl p-8 max-w-md w-full mx-4 max-h-[80vh] overflow-auto">
        <h3 class="text-2xl font-bold mb-4">Your Cart</h3>
        <div id="cart-items"></div>
        <div class="mt-6 flex justify-between font-bold text-lg border-t pt-4">
            <span>Total</span>
            <span id="cart-total">R0.00</span>
        </div>
        <button onclick="checkout()" class="btn-primary w-full py-4 rounded-lg mt-4 font-bold">
            Checkout
        </button>
        <button onclick="closeCart()" class="w-full py-2 mt-2 text-gray-500">Close</button>
    </div>
</div>"""

    def _head(self, title: str) -> str:
        config = self.site["config"]
        return f"""<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — {config['site_name']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="assets/c6-config.js"></script>
    <script src="assets/c6-api.js"></script>
    <script src="assets/products.js"></script>
    <script src="assets/cart.js"></script>
    <style>
        :root {{ --primary: {config['primary_color']}; }}
        .btn-primary {{ background: var(--primary); color: white; transition: opacity 0.15s; }}
        .btn-primary:hover {{ opacity: 0.9; }}
        .product-card {{ transition: transform 0.15s, box-shadow 0.15s; }}
        .product-card:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.08); }}
    </style>
</head>"""

    def _scripts_tail(self) -> str:
        return """<script>
    // Populate shop metadata from data/shop.json
    fetch('data/shop.json').then(r => r.json()).then(shop => {
        const nav = document.getElementById('nav-shop-name');
        if (nav) nav.textContent = shop.name;
        const footer = document.getElementById('footer-shop-name');
        if (footer) footer.textContent = shop.name;
        const contact = document.getElementById('footer-contact');
        if (contact) contact.textContent = [shop.phone, shop.email].filter(Boolean).join(' · ');
    });
    // Populate products wherever a container exists
    document.addEventListener('DOMContentLoaded', () => {
        const featured = document.getElementById('featured-products');
        if (featured) renderProductGrid('featured-products', { limit: 6 });
        const menu = document.getElementById('menu-products');
        if (menu) renderProductGrid('menu-products', {});
        const shop = document.getElementById('shop-products');
        if (shop) renderProductGrid('shop-products', {});
    });
</script>"""

    def _render_index(self):
        config = self.site["config"]
        home = self.site["pages"].get("home", {})
        hero = home.get("hero", {})

        html = f"""<!DOCTYPE html>
<html lang="en">
{self._head(config['site_name'])}
<body class="bg-gray-50 min-h-screen flex flex-col">
{self._nav()}

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
        <div class="flex justify-between items-center mb-8">
            <h3 class="text-3xl font-bold">Featured</h3>
            <a href="menu.html" class="text-sm" style="color: var(--primary);">See full menu →</a>
        </div>
        <div id="featured-products" class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="text-gray-400 text-sm col-span-3">Loading...</div>
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
        <div id="delivery-widget-result" class="mt-4 text-sm"></div>
    </div>
</section>

{self._footer()}
{self._cart_modal()}
{self._scripts_tail()}
</body>
</html>"""
        (self.output / "index.html").write_text(html, encoding="utf-8")

    def _render_menu(self):
        config = self.site["config"]
        products = (
            self.site["shop"].get("menu_items")
            or self.site["shop"].get("products")
            or self.site["shop"].get("services")
            or []
        )
        page_title = "Our Menu" if products and self.site["shop"].get("menu_items") else "Shop"
        empty = "" if products else (
            '<div class="text-gray-400 text-sm col-span-3 p-8 text-center border-2 border-dashed rounded-lg">'
            'No products listed yet. Add some to <code>shop_data["menu_items"]</code> when generating.'
            '</div>'
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
{self._head(page_title)}
<body class="bg-gray-50 min-h-screen flex flex-col">
{self._nav()}
<main class="max-w-7xl mx-auto px-4 py-12 flex-grow w-full">
    <h1 class="text-4xl font-bold mb-8">{page_title}</h1>
    <div id="menu-products" class="grid grid-cols-1 md:grid-cols-3 gap-6">
        {empty or '<div class="text-gray-400 text-sm col-span-3">Loading products...</div>'}
    </div>
</main>
{self._footer()}
{self._cart_modal()}
{self._scripts_tail()}
</body>
</html>"""
        (self.output / "menu.html").write_text(html, encoding="utf-8")

    def _render_about(self):
        config = self.site["config"]
        story = self.site["shop"].get("story") or f"{config['site_name']} proudly serves our community."

        html = f"""<!DOCTYPE html>
<html lang="en">
{self._head('About Us')}
<body class="bg-gray-50 min-h-screen flex flex-col">
{self._nav()}
<main class="max-w-3xl mx-auto px-4 py-12 flex-grow w-full">
    <h1 class="text-4xl font-bold mb-8">About Us</h1>
    <div class="bg-white rounded-xl p-8 shadow-sm prose max-w-none">
        <p class="text-gray-700 text-lg leading-relaxed">{story}</p>
    </div>
</main>
{self._footer()}
{self._cart_modal()}
{self._scripts_tail()}
</body>
</html>"""
        (self.output / "about.html").write_text(html, encoding="utf-8")

    def _render_contact(self):
        shop = self.site["shop"]
        hours = shop.get("hours") or {}

        hours_rows = "".join(
            f'<div class="flex justify-between py-2 border-b"><span>{day}</span><span>{h}</span></div>'
            for day, h in hours.items()
        ) or '<p class="text-gray-400 text-sm">Hours not listed.</p>'

        html = f"""<!DOCTYPE html>
<html lang="en">
{self._head('Contact')}
<body class="bg-gray-50 min-h-screen flex flex-col">
{self._nav()}
<main class="max-w-3xl mx-auto px-4 py-12 flex-grow w-full">
    <h1 class="text-4xl font-bold mb-8">Contact</h1>
    <div class="bg-white rounded-xl p-8 shadow-sm">
        <div class="mb-6">
            <h3 class="font-bold mb-2">Get in touch</h3>
            <p class="text-gray-700">📞 {shop.get('phone') or '—'}</p>
            <p class="text-gray-700">✉️ {shop.get('email') or '—'}</p>
            <p class="text-gray-700">📍 {shop.get('address') or '—'}</p>
        </div>
        <div>
            <h3 class="font-bold mb-2">Opening Hours</h3>
            {hours_rows}
        </div>
    </div>
</main>
{self._footer()}
{self._cart_modal()}
{self._scripts_tail()}
</body>
</html>"""
        (self.output / "contact.html").write_text(html, encoding="utf-8")

    def _render_checkout(self):
        html = f"""<!DOCTYPE html>
<html lang="en">
{self._head('Checkout')}
<body class="bg-gray-50 min-h-screen">
{self._nav()}
<div class="max-w-2xl mx-auto py-12 px-4">
    <h1 class="text-3xl font-bold mb-8">Checkout</h1>

    <div id="checkout-summary" class="bg-white rounded-xl p-6 shadow-sm mb-6"></div>

    <div class="bg-white rounded-xl p-6 shadow-sm mb-6">
        <h3 class="font-bold mb-4">Your Details</h3>
        <input id="customer-name" placeholder="Your name" class="w-full px-3 py-2 border rounded mb-3">
        <input id="customer-email" placeholder="Email" type="email" class="w-full px-3 py-2 border rounded mb-3">
        <input id="customer-phone" placeholder="Phone" class="w-full px-3 py-2 border rounded mb-3">
        <input id="customer-address" placeholder="Delivery address" class="w-full px-3 py-2 border rounded mb-3">
        <input id="customer-area" placeholder="Area (e.g., Soweto)" class="w-full px-3 py-2 border rounded">
    </div>

    <div class="bg-white rounded-xl p-6 shadow-sm">
        <h3 class="font-bold mb-4">Delivery</h3>
        <button onclick="checkDeliveryAvailability()" class="px-4 py-2 border rounded-lg mb-4 hover:bg-gray-50">
            Check availability
        </button>
        <div id="delivery-result" class="text-sm text-gray-600"></div>
    </div>

    <button onclick="submitOrder()" id="pay-btn"
            class="w-full bg-green-600 hover:bg-green-700 text-white py-4 rounded-lg font-bold mt-6">
        Pay with RemotePay
    </button>

    <div id="order-status" class="mt-4 text-sm"></div>
</div>
{self._cart_modal()}
{self._scripts_tail()}
</body>
</html>"""
        (self.output / "checkout.html").write_text(html, encoding="utf-8")

    def _render_thank_you(self):
        html = f"""<!DOCTYPE html>
<html lang="en">
{self._head('Thank You')}
<body class="bg-gray-50 min-h-screen flex flex-col">
{self._nav()}
<main class="max-w-2xl mx-auto px-4 py-20 flex-grow w-full text-center">
    <div class="text-6xl mb-4">✅</div>
    <h1 class="text-4xl font-bold mb-4">Thank you!</h1>
    <p class="text-gray-600 mb-8">Your order has been placed.</p>
    <div id="order-details" class="bg-white rounded-xl p-6 shadow-sm text-left mb-8">
        <p class="text-gray-500 text-sm">Order details will appear here.</p>
    </div>
    <a href="index.html" class="btn-primary px-8 py-3 rounded-lg font-bold inline-block">Back to home</a>
</main>
{self._footer()}
{self._cart_modal()}
{self._scripts_tail()}
</body>
</html>"""
        (self.output / "thank-you.html").write_text(html, encoding="utf-8")

    # ----------------------------------------------------------------
    # Assets
    # ----------------------------------------------------------------
    def _render_assets(self):
        assets_dir = self.output / "assets"
        assets_dir.mkdir(exist_ok=True)

        shop_id = self.site["shop"].get("id", "unknown")
        merchant_id = self.site["shop"].get("remotepay_merchant_id") or f"merchant_{shop_id}"

        config_js = (
            f"window.C6_CONFIG = {{\n"
            f"  apiBaseUrl: {json.dumps(self.api_base_url)},\n"
            f"  shopId: {json.dumps(shop_id)},\n"
            f"  merchantId: {json.dumps(merchant_id)},\n"
            f"  brandId: 'ubernie',\n"
            f"  sourceSystem: 'c6_generated_site',\n"
            f"}};\n"
        )
        (assets_dir / "c6-config.js").write_text(config_js, encoding="utf-8")

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
    if (!Array.isArray(items) || items.length === 0) {
      throw new Error('Your cart is empty. Add items before checking out.');
    }
    const payload = {
      shop_id: cfg().shopId,
      merchant_id: cfg().merchantId,
      items: items.map(i => ({
        id: String(i.id),
        name: String(i.name),
        price: Number(i.price),
        qty: Number(i.qty),
      })),
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
    if (!r.ok) {
      let detail = r.statusText;
      try {
        const body = await r.json();
        detail = body.detail || JSON.stringify(body);
      } catch (_) { /* body wasn't JSON */ }
      throw new Error('Payment creation failed: ' + r.status + ' — ' + detail);
    }
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

        products_js = """// Product grid renderer
async function renderProductGrid(containerId, opts = {}) {
  const container = document.getElementById(containerId);
  if (!container) return;

  try {
    const r = await fetch('data/products.json');
    if (!r.ok) throw new Error('Failed to load products');
    let products = await r.json();
    if (!products.length) {
      container.innerHTML = '<div class="text-gray-400 text-sm col-span-3 p-8 text-center border-2 border-dashed rounded-lg">No products listed yet.</div>';
      return;
    }
    if (opts.limit) products = products.slice(0, opts.limit);

    container.innerHTML = products.map(p => `
      <div class="product-card bg-white rounded-xl shadow-sm overflow-hidden">
        <div class="p-6">
          <h3 class="font-bold text-lg mb-1">${escapeHtml(p.name)}</h3>
          ${p.description ? `<p class="text-gray-500 text-sm mb-3">${escapeHtml(p.description)}</p>` : ''}
          <div class="flex justify-between items-center mt-4">
            <span class="font-bold text-lg">R${p.price.toFixed(2)}</span>
            <button onclick="addToCart('${p.id}', '${escapeJs(p.name)}', ${p.price})"
                    class="btn-primary px-4 py-2 rounded-lg text-sm">
              Add
            </button>
          </div>
        </div>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<div class="text-red-500 text-sm col-span-3">Error loading products: ${e.message}</div>`;
  }
}

function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function escapeJs(s) { return String(s).replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'"); }
"""
        (assets_dir / "products.js").write_text(products_js, encoding="utf-8")

        cart_js = """// Shopping Cart
let cart = JSON.parse(localStorage.getItem('cart') || '[]');

function saveCart() { localStorage.setItem('cart', JSON.stringify(cart)); updateCartCount(); }

function addToCart(id, name, price) {
  const existing = cart.find(i => i.id === id);
  if (existing) existing.qty++;
  else cart.push({ id, name, price, qty: 1 });
  saveCart();
  const modal = document.getElementById('cart-modal');
  if (modal) openCart(); else alert(name + ' added');
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
  if (!cart.length) {
    items.innerHTML = '<p class="text-gray-400 text-sm py-4">Your cart is empty.</p>';
  } else {
    items.innerHTML = cart.map((i, idx) => `
      <div class="flex justify-between items-center py-3 border-b">
        <div>
          <div class="font-medium">${i.name}</div>
          <div class="text-xs text-gray-500">R${i.price.toFixed(2)} x ${i.qty}</div>
        </div>
        <div class="flex items-center gap-3">
          <span class="font-mono">R${(i.price * i.qty).toFixed(2)}</span>
          <button onclick="removeFromCart(${idx})" class="text-red-400 text-xs">×</button>
        </div>
      </div>
    `).join('');
  }
  const sum = cart.reduce((s, i) => s + i.price * i.qty, 0);
  if (total) total.textContent = 'R' + sum.toFixed(2);
}

function removeFromCart(idx) { cart.splice(idx, 1); saveCart(); renderCart(); }

function checkout() {
  if (!cart.length) { alert('Cart is empty'); return; }
  window.location.href = 'checkout.html';
}

function openDeliveryWidget() {
  const el = document.getElementById('delivery-widget-result');
  const area = prompt('Enter your area (e.g., Soweto):');
  if (!area) return;
  if (el) el.textContent = 'Checking...';
  C6.checkDelivery(area).then(res => {
    const msg = res.available
      ? `✅ Delivery available in ${res.area} — ${res.fee_display} (~${res.eta_minutes} min)`
      : `❌ ${res.message}`;
    if (el) el.innerHTML = msg;
    else alert(msg);
  }).catch(e => {
    const msg = 'Error: ' + e.message;
    if (el) el.textContent = msg; else alert(msg);
  });
}

async function checkDeliveryAvailability() {
  const area = document.getElementById('customer-area').value.trim();
  const el = document.getElementById('delivery-result');
  if (!area) { el.textContent = 'Enter an area first.'; return; }
  el.textContent = 'Checking...';
  try {
    const res = await C6.checkDelivery(area);
    if (res.available) {
      el.dataset.available = '1';
      el.innerHTML = `✅ Delivery available in ${res.area} — ${res.fee_display} (~${res.eta_minutes} min)`;
    } else {
      el.dataset.available = '0';
      el.innerHTML = `❌ ${res.message}`;
    }
  } catch (e) {
    el.dataset.available = '0';
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

    // Only send delivery_area if we confirmed delivery is available.
    // Otherwise the order goes through as pickup — no surprise fees.
    const deliveryOk = document.getElementById('delivery-result')?.dataset.available === '1';
    const deliveryArea = deliveryOk ? area : null;

    // Step 1: create the payment — get back a redirect URL to the gateway
    const order = await C6.createPayment(cart, { name, email, deliveryArea });

    // Save what we need to remember for when the customer returns
    sessionStorage.setItem('pending_order', JSON.stringify({
      order_id: order.order_id,
      payment_id: order.payment_id,
      amount_display: order.amount_display,
    }));

    // Clear cart now — the customer is committed to paying
    cart = [];
    saveCart();

    // Step 2: redirect to the gateway (SimplyBlu, or our mock in dev)
    status.innerHTML = `<div class="p-4 bg-blue-50 border border-blue-200 rounded">
      Order <b>${order.order_id}</b> created. Redirecting to secure payment...
    </div>`;

    setTimeout(() => { window.location.href = order.payment_url; }, 400);

  } catch (e) {
    status.innerHTML = `<div class="p-4 bg-red-50 border border-red-200 rounded">Error: ${e.message}</div>`;
    btn.disabled = false;
  }
}

// Checkout page: render summary OR redirect if cart empty
if (document.getElementById('checkout-summary')) {
  if (!cart.length) {
    document.getElementById('checkout-summary').innerHTML =
      '<div class="text-gray-500">Your cart is empty. Redirecting to menu...</div>';
    // Disable the pay button so no one can proceed
    const btn = document.getElementById('pay-btn');
    if (btn) { btn.disabled = true; btn.classList.add('opacity-50', 'cursor-not-allowed'); }
    setTimeout(() => { window.location.href = 'menu.html'; }, 1500);
  } else {
    const sum = cart.reduce((s, i) => s + i.price * i.qty, 0);
    document.getElementById('checkout-summary').innerHTML =
      cart.map(i => `<div class="flex justify-between py-1"><span>${i.name} x${i.qty}</span><span>R${(i.price*i.qty).toFixed(2)}</span></div>`).join('')
      + `<div class="flex justify-between font-bold pt-3 border-t mt-3"><span>Subtotal</span><span>R${sum.toFixed(2)}</span></div>`;
  }
}

// Thank-you page: fetch order status by order_id (from URL or session)
if (document.getElementById('order-details')) {
  const params = new URLSearchParams(location.search);
  const orderId = params.get('order_id');
  const paymentId = params.get('payment_id');

  async function loadOrder() {
    const el = document.getElementById('order-details');
    const pending = JSON.parse(sessionStorage.getItem('pending_order') || 'null');
    const oid = orderId || (pending && pending.order_id);
    const pid = paymentId || (pending && pending.payment_id);

    if (!oid) {
      el.innerHTML = '<p class="text-gray-500">No recent order found.</p>';
      return;
    }

    try {
      const base = (window.C6_CONFIG?.apiBaseUrl || '').replace(/\/$/, '');
      const res = await fetch(base + '/api/orders/' + oid);
      if (!res.ok) throw new Error('Order lookup failed');
      const order = await res.json();
      const rider = order.rider;
      el.innerHTML = `
        <p class="text-sm text-gray-500 mb-1">Order ID</p>
        <p class="font-mono mb-4">${order.order_id}</p>
        <p class="text-sm text-gray-500 mb-1">Status</p>
        <p class="mb-4 capitalize">${order.status.replace(/_/g, ' ')}</p>
        ${order.total_minor ? `
          <p class="text-sm text-gray-500 mb-1">Total paid</p>
          <p class="mb-4">R${(order.total_minor / 100).toFixed(2)}</p>
        ` : ''}
        ${rider ? `
          <p class="text-sm text-gray-500 mb-1">Your rider</p>
          <p>🛵 ${rider.full_name}${rider.phone ? ` · ${rider.phone}` : ''}</p>
        ` : ''}
      `;
      sessionStorage.removeItem('pending_order');
    } catch (e) {
      el.innerHTML = `<p class="text-red-500 text-sm">Could not load order: ${e.message}</p>`;
    }
  }

  loadOrder();
}

updateCartCount();
"""
        (assets_dir / "cart.js").write_text(cart_js, encoding="utf-8")
