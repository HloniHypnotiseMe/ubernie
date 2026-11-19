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
