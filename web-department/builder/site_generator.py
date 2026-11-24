#!/usr/bin/env python3
"""
C6 Website Department — AI Site Generator
Generates a complete online store for any shop in under 60 seconds.
"""
from datetime import datetime
from pathlib import Path
import json


class SiteGenerator:
    """
    Takes a shop's basic info and generates a full online store:
    - Landing page (hero, about, contact)
    - Product/menu catalog
    - Cart + checkout (RemotePay embedded)
    - Delivery widget (Ubernie)
    - Admin panel (orders, products, settings)
    """

    TEMPLATES = {
        "restaurant": {
            "pages": ["home", "menu", "about", "contact", "checkout"],
            "features": ["menu_grid", "cart", "delivery_widget", "hours"],
            "primary_color": "#E63946",
        },
        "retail": {
            "pages": ["home", "shop", "about", "contact", "checkout"],
            "features": ["product_grid", "cart", "delivery_widget", "inventory"],
            "primary_color": "#2A9D8F",
        },
        "pharmacy": {
            "pages": ["home", "products", "prescription", "contact"],
            "features": ["product_grid", "prescription_upload", "delivery_widget"],
            "primary_color": "#1D3557",
        },
        "salon": {
            "pages": ["home", "services", "booking", "contact"],
            "features": ["service_list", "booking_calendar", "reminders"],
            "primary_color": "#9B5DE5",
        },
        "services": {
            "pages": ["home", "services", "quote", "contact"],
            "features": ["service_list", "quote_form", "contact"],
            "primary_color": "#F77F00",
        },
        "daycare": {
            "pages": ["home", "programs", "fees", "tour", "contact", "checkout"],
            "features": ["programs_grid", "fees_table", "tour_booking", "whatsapp_widget", "enrollment_form", "meals_info"],
            "primary_color": "#FF6B35",
        },
    }

    # Uber Smart Capabilities - Adapted for Ubernie Directory (Not Ride-Hailing)
    SMART_CAPABILITIES = {
        "geo_matching": "Find nearest by ETA + rating, not just distance",
        "upfront_pricing": "Price from server catalogue, never client price",
        "live_share": "Share listing / tour / voucher link via WhatsApp",
        "two_way_ratings": "Customer rates business, business rates customer",
        "verified_badge": "OTP + ID + CIPC / RMI verified",
        "thursday_surge_reverse": "Demand spike Thursday = prices drop via Deals Corner",
        "batch_matching": "Lead sent to 3 nearest best-rated, first to reply in 5 min wins",
        "lead_state_machine": "inquiry -> replied -> tour_booked -> showed -> paid -> reviewed",
        "featured_membership": "Ubernie Featured = Uber One for businesses",
        "multi_location": "Mall / Agency / Dealer Group = 1 bill, many locations",
    }

    def __init__(self, shop_data):
        self.shop = shop_data
        self.industry = shop_data.get("industry", "retail").lower()
        self.template = self.TEMPLATES.get(self.industry, self.TEMPLATES["retail"])

    def generate(self):
        """Generate the full site."""
        site = {
            "shop": self.shop,
            "template": self.industry,
            "config": self._generate_config(),
            "pages": self._generate_pages(),
            "integrations": self._generate_integrations(),
            "generated_at": datetime.now().isoformat(),
        }
        return site

    def _generate_config(self):
        """Generate site config (colors, fonts, logo)."""
        return {
            "site_name": self.shop["name"],
            "tagline": self.shop.get("tagline", f"Welcome to {self.shop['name']}"),
            "primary_color": self.template["primary_color"],
            "font": "Inter",
            "logo_url": self.shop.get("logo_url"),
            "contact": {
                "phone": self.shop.get("phone"),
                "email": self.shop.get("email"),
                "address": self.shop.get("address"),
            },
            "social": {
                "facebook": self.shop.get("facebook"),
                "instagram": self.shop.get("instagram"),
                "whatsapp": self.shop.get("whatsapp"),
            },
        }

    def _generate_pages(self):
        """Generate each page's content structure."""
        pages = {}
        for page in self.template["pages"]:
            pages[page] = self._generate_page(page)
        return pages

    def _generate_page(self, page_name):
        """Generate a single page."""
        generators = {
            "home": self._home_page,
            "menu": self._menu_page,
            "shop": self._shop_page,
            "products": self._shop_page,
            "services": self._services_page,
            "about": self._about_page,
            "contact": self._contact_page,
            "checkout": self._checkout_page,
            "booking": self._booking_page,
            "prescription": self._prescription_page,
            "quote": self._quote_page,
        }
        return generators.get(page_name, self._generic_page)()

    def _home_page(self):
        return {
            "hero": {
                "headline": self.shop["name"],
                "subheadline": self.shop.get("tagline", "Quality products, delivered to your door"),
                "cta": "Book FREE Tour" if self.industry == "daycare" else ("Order Now" if self.industry == "restaurant" else "Shop Now"),
            },
            "sections": ["featured_products", "about_preview", "delivery_banner", "contact_cta"],
        }

    def _menu_page(self):
        return {
            "title": "Our Menu",
            "layout": "grid",
            "items": self.shop.get("menu_items", []),
            "categories": self.shop.get("menu_categories", []),
        }

    def _shop_page(self):
        return {
            "title": "Shop",
            "layout": "grid",
            "products": self.shop.get("products", []),
            "categories": self.shop.get("categories", []),
            "filters": ["price", "category", "availability"],
        }

    def _services_page(self):
        return {
            "title": "Our Services",
            "layout": "list",
            "services": self.shop.get("services", []),
        }

    def _about_page(self):
        return {
            "title": "About Us",
            "story": self.shop.get("story", f"{self.shop['name']} has been serving the community."),
            "values": self.shop.get("values", []),
        }

    def _contact_page(self):
        return {
            "title": "Contact",
            "form": True,
            "map": True,
            "hours": self.shop.get("hours", {}),
        }

    def _checkout_page(self):
        return {
            "title": "Checkout",
            "payment_methods": ["RemotePay", "Card", "EFT", "Cash on Delivery"],
            "delivery_options": ["Ubernie Delivery", "Pickup"],
        }

    def _booking_page(self):
        return {
            "title": "Book Appointment",
            "calendar": True,
            "services": self.shop.get("services", []),
        }

    def _prescription_page(self):
        return {
            "title": "Upload Prescription",
            "upload": True,
            "pharmacist_review": True,
        }

    def _quote_page(self):
        return {
            "title": "Request a Quote",
            "form": True,
            "fields": ["name", "phone", "service", "details"],
        }

    def _generic_page(self):
        return {"title": "Page", "content": []}

    def _generate_integrations(self):
        """Generate integration configs."""
        return {
            "remotepay": {
                "enabled": True,
                "merchant_id": self.shop.get("remotepay_merchant_id"),
                "button_text": "Pay with RemotePay",
            },
            "ubernie_delivery": {
                "enabled": True,
                "shop_id": self.shop.get("ubernie_shop_id"),
                "widget_position": "floating",
                "delivery_fee": "R15-R45",
            },
            "taxai": {
                "enabled": True,
                "auto_vat": True,
                "auto_receipts": True,
            },
            "whatsapp": {
                "enabled": True,
                "order_via_whatsapp": True,
            },
        }


if __name__ == "__main__":
    print("Site Generator ready")
