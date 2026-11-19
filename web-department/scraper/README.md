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


## Free-first South African business discovery (OpenStreetMap)

Ubernie also includes a free-data discovery adapter using OpenStreetMap (OSM) via the read-only Overpass API. It is separate from Google Places: OSM data can be retained and used under the Open Database License (ODbL), provided the licence and attribution obligations are followed.

### Run a discovery search

From `web-department/`:

```bash
python -m scraper.osm_discovery --category plumber --area Gauteng --limit 50 --output data/gauteng-plumbers.json
python -m scraper.osm_discovery --category restaurant --area Johannesburg --limit 50 --output data/johannesburg-restaurants.csv
```

Supported initial categories: accountant, builder, cafe, dentist, doctor, electrician, hairdresser, hotel, lawyer, mechanic, painter, pharmacy, plumber, restaurant, school and supermarket. Search is bounded to 100 results per request and supports named administrative areas such as provinces and cities when they are mapped in OSM. Coverage and tagging quality vary; an empty result does not prove that no such businesses exist.

Each record carries its OSM element identity, source URL, retrieval timestamp, raw OSM tags, and ODbL attribution metadata. Keep OSM-derived data clearly labelled and separate from independently collected website evidence. Display **© OpenStreetMap contributors** and link to https://www.openstreetmap.org/copyright where users access OSM-derived records. If distributing an adapted or derivative database, review and comply with ODbL share-alike requirements.

### Free-service limits and commercial deployment

- OSM map data itself is free to use commercially under ODbL, with attribution and share-alike obligations.
- Public Overpass servers are shared community infrastructure, not a production SLA. This adapter makes one bounded request at a time, identifies Ubernie with a User-Agent, does not retry overloaded responses, and caps each search at 100 records.
- The public FOSSGIS Overpass service guidance recommends self-hosting or a paid service for commercial use, and calls for caching, rate limiting and no parallel scripts. Use this public endpoint for development and controlled low-volume evaluation only; do not make it the guaranteed backend for paying customers.
- For production at scale, use South Africa regional OSM extracts on Ubernie's own infrastructure or a provider whose commercial terms and capacity support the workload. The OSM data remains free; compute, storage and bandwidth may not be.
- No Google API key, Google Cloud billing account, or paid business-data subscription is needed for this OSM discovery path.

Official references:
- https://www.openstreetmap.org/copyright
- https://osmfoundation.org/wiki/Licence_and_Legal_FAQ
- https://wiki.openstreetmap.org/wiki/Overpass_API
