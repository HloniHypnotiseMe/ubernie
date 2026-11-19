# C6 Universal Scraper — MVP

A bounded crawler for publicly accessible web pages, initially powering Ubernie's South African business discovery workflow.

## Install

From `web-department/`:

```bash
python -m pip install -r requirements.txt
python -m pip install beautifulsoup4
```

## Run

```bash
python -m scraper.cli https://example.org --max-pages 10 --max-depth 1 --output data/results.json
python -m scraper.cli https://example.org --max-pages 10 --max-depth 1 --output data/results.csv
```

The crawler records page title, description, canonical URL, visible text, public email/phone patterns, JSON-LD, discovered links, HTTP status and timestamp. It follows same-domain links by default, enforces page/depth/response-size limits, uses a per-host delay, checks robots.txt, revalidates redirect destinations and blocks non-public IP destinations.

## Operating boundaries

- Public pages only. No login automation, CAPTCHA solving, paywall circumvention or access-control bypass.
- Respect site terms, robots.txt, privacy requirements and applicable law. Do not use this to harvest sensitive personal data or send unsolicited bulk messages.
- Robots denial and robots retrieval failure fail closed.
- Validate extracted business records before publishing them in Ubernie. Extraction is not verification of ownership, consent, accuracy or current trading status.
- This MVP uses a synchronous HTTP fetcher. JavaScript-rendered pages, adaptive selectors, durable job queues, proxy rotation and dashboard integration are explicitly later phases—not claimed as complete.


## Google Places discovery (South Africa)

Ubernie can query the official Google Places API (New) for immediate in-app discovery of businesses in South Africa. This is an API integration, not HTML scraping of Google Maps.

1. In a Google Cloud project, enable **Places API (New)** and billing.
2. Create a server-side API key restricted to the Places API and the deployment environment.
3. Set the secret as `GOOGLE_MAPS_API_KEY` (never commit it).
4. Use `GooglePlacesClient.search_businesses("plumbers in Johannesburg")` from the application. The adapter sets `regionCode=ZA`, uses an explicit field mask, includes service-area businesses, and limits Text Search pagination to at most three pages.

Example:

```python
from scraper.google_places import GooglePlacesClient

with GooglePlacesClient() as places:
    transient_results = places.search_businesses("electricians in Soweto")
    # Render these results immediately in a Google Places-powered UI.
    # You may retain a Google place ID. Do not copy other Google Maps
    # Content into Ubernie's independent business/lead database.
```

**Google data boundary:** Google Maps Content is subject to Google Maps Platform terms and attribution/display requirements. Do not export, index, bulk-download, or persist Google business names, addresses, phone numbers, websites, ratings, reviews, or other Places content in an independent lead database. Place IDs are exempt from the general caching restriction. Use a returned website URL transiently to visit the business's own public website with the independent C6 crawler; only independently collected website content should enter the C6 lead database, with its own source URL and fetch timestamp. Re-check Google's current policies before release.

Official references:
- https://developers.google.com/maps/documentation/places/web-service/text-search
- https://developers.google.com/maps/documentation/places/web-service/policies
- https://developers.google.com/maps/documentation/places/web-service/usage-and-billing
