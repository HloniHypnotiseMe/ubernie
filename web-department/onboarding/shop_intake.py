#!/usr/bin/env python3
"""
C6 Website Department — Shop Intake
Collects everything needed to build a shop's website.
"""
from datetime import datetime


class ShopIntake:
    """
    Intake flow:
    1. Shop owner fills form (or we scrape what we can)
    2. AI fills gaps (descriptions, categories)
    3. Shop uploads logo + product photos
    4. Site generated in 60 seconds
    5. Shop reviews and approves
    6. Deployed to subdomain
    """

    REQUIRED_FIELDS = [
        "business_name",
        "owner_name",
        "email",
        "phone",
        "address",
        "industry",
    ]

    OPTIONAL_FIELDS = [
        "tagline",
        "story",
        "logo_url",
        "product_photos",
        "hours",
        "social_links",
        "menu_items",
        "products",
        "services",
    ]

    def __init__(self, db_pool):
        self.db = db_pool

    async def start_intake(self, business_id):
        """Start intake for a business (from Ubernie scrape)."""
        # Pull what we already have from Ubernie directory
        business = await self._get_business(business_id)

        return {
            "business_id": business_id,
            "prefilled": {
                "business_name": business["name"],
                "address": business["address"],
                "phone": business.get("phone"),
                "email": business.get("email"),
                "industry": business.get("industry"),
            },
            "missing": self._get_missing_fields(business),
            "intake_url": f"https://c6.remotepay.co.za/intake/{business_id}",
        }

    async def submit_intake(self, business_id, data):
        """Shop submits intake form."""
        # Validate
        missing = [f for f in self.REQUIRED_FIELDS if not data.get(f)]
        if missing:
            return {"error": "Missing required fields", "missing": missing}

        # Save
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO shop_intakes (business_id, data, submitted_at, status)
                VALUES ($1, $2, NOW(), 'SUBMITTED')
                ON CONFLICT (business_id) DO UPDATE
                SET data = $2, submitted_at = NOW(), status = 'SUBMITTED'
            """, business_id, data)

        # Trigger AI enrichment
        enriched = await self._enrich_with_ai(data)

        # Trigger site generation
        return await self._generate_site(business_id, enriched)

    async def _enrich_with_ai(self, data):
        """Use AI to fill gaps (descriptions, categories)."""
        enriched = dict(data)

        if not enriched.get("tagline"):
            enriched["tagline"] = await self._ai_tagline(data)

        if not enriched.get("story"):
            enriched["story"] = await self._ai_story(data)

        if not enriched.get("categories"):
            enriched["categories"] = await self._ai_categories(data)

        return enriched

    async def _ai_tagline(self, data):
        """Generate a tagline."""
        industry = data.get("industry", "business")
        taglines = {
            "restaurant": f"Authentic flavors, delivered fresh",
            "retail": f"Quality products, unbeatable prices",
            "pharmacy": f"Your health, our priority",
            "salon": f"Look good, feel great",
        }
        return taglines.get(industry, f"Welcome to {data['business_name']}")

    async def _ai_story(self, data):
        return f"{data['business_name']} has been proudly serving the community."

    async def _ai_categories(self, data):
        return ["Featured", "Popular", "New"]

    async def _generate_site(self, business_id, enriched_data):
        """Trigger site generation."""
        from builder.site_generator import SiteGenerator
        from builder.site_renderer import SiteRenderer

        shop_data = {
            "id": business_id,
            "name": enriched_data["business_name"],
            "industry": enriched_data.get("industry", "retail"),
            "address": enriched_data["address"],
            "phone": enriched_data.get("phone"),
            "email": enriched_data.get("email"),
            "tagline": enriched_data.get("tagline"),
            "story": enriched_data.get("story"),
            "menu_items": enriched_data.get("menu_items", []),
            "products": enriched_data.get("products", []),
            "services": enriched_data.get("services", []),
            "remotepay_merchant_id": f"rp_{business_id}",
            "ubernie_shop_id": business_id,
        }

        generator = SiteGenerator(shop_data)
        config = generator.generate()

        output_dir = f"/var/www/c6-sites/{business_id}"
        renderer = SiteRenderer(config, output_dir)
        result = renderer.render()

        # Save config
        async with self.db.acquire() as conn:
            await conn.execute("""
                UPDATE shop_intakes
                SET status = 'SITE_GENERATED',
                    site_config = $2,
                    site_url = $3,
                    generated_at = NOW()
                WHERE business_id = $1
            """, business_id, config, f"https://{business_id}.c6.remotepay.co.za")

        return {
            "business_id": business_id,
            "status": "SITE_GENERATED",
            "preview_url": f"https://preview.c6.remotepay.co.za/{business_id}",
            "rendered_to": result["rendered_to"],
            "next_step": "Shop reviews and approves",
        }

    async def _get_business(self, business_id):
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM businesses WHERE id = $1", business_id
            )
        return dict(row) if row else {}

    def _get_missing_fields(self, business):
        return [f for f in self.REQUIRED_FIELDS if not business.get(f)]


if __name__ == "__main__":
    print("Shop Intake ready")
