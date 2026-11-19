from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .engine import ScrapeConfig, Scraper


def main() -> int:
    parser = argparse.ArgumentParser(description="C6 Universal Scraper — public web pages")
    parser.add_argument("urls", nargs="+", help="One or more absolute HTTP(S) URLs")
    parser.add_argument("--output", default="scrape-results.json", help="Output .json or .csv path")
    parser.add_argument("--max-pages", type=int, default=25)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()
    if not 1 <= args.max_pages <= 500 or not 0 <= args.max_depth <= 5 or args.delay < 0.5:
        parser.error("max-pages must be 1..500, max-depth 0..5, and delay at least 0.5 seconds")
    config = ScrapeConfig(max_pages=args.max_pages, max_depth=args.max_depth, delay_seconds=args.delay)
    with Scraper(config) as scraper:
        records = [item.to_dict() for item in scraper.crawl(args.urls)]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        fields = ["url", "final_url", "status_code", "fetched_at", "title", "description", "emails", "phones", "error"]
        with output.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for record in records:
                writer.writerow({**record, "emails": ";".join(record["emails"]), "phones": ";".join(record["phones"])})
    else:
        output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    succeeded = sum(1 for record in records if record["status_code"] and record["status_code"] < 400 and not record["error"])
    print(f"Fetched {succeeded}/{len(records)} pages. Results: {output}")
    return 0 if succeeded else 2


if __name__ == "__main__":
    raise SystemExit(main())
