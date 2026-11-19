"""Free-first South African business discovery using OpenStreetMap + Overpass.

OSM records are ODbL-licensed data. Keep their provenance and attribution when
displaying or distributing them; do not silently merge them into an unrelated
proprietary dataset.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_ATTRIBUTION = "© OpenStreetMap contributors"
OSM_LICENSE_URL = "https://www.openstreetmap.org/copyright"

# Deliberately controlled categories prevent arbitrary Overpass QL injection.
CATEGORY_TAGS: dict[str, tuple[str, str]] = {
    "accountant": ("office", "accountant"),
    "builder": ("craft", "builder"),
    "cafe": ("amenity", "cafe"),
    "dentist": ("healthcare", "dentist"),
    "doctor": ("healthcare", "doctor"),
    "electrician": ("craft", "electrician"),
    "hairdresser": ("shop", "hairdresser"),
    "hotel": ("tourism", "hotel"),
    "lawyer": ("office", "lawyer"),
    "mechanic": ("craft", "car_repair"),
    "pharmacy": ("amenity", "pharmacy"),
    "plumber": ("craft", "plumber"),
    "painter": ("craft", "painter"),
    "restaurant": ("amenity", "restaurant"),
    "school": ("amenity", "school"),
    "supermarket": ("shop", "supermarket"),
}

AREA_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .'-]{0,79}$")


@dataclass(frozen=True)
class OSMDiscoveryConfig:
    endpoint: str = DEFAULT_OVERPASS_URL
    timeout_seconds: float = 30.0
    max_results: int = 50
    user_agent: str = "UbernieRSA-BusinessDiscovery/1.0 (https://www.ubernie.co.za)"
    minimum_request_interval_seconds: float = 5.0


class OSMDiscoveryError(RuntimeError):
    """Raised when Overpass cannot complete a bounded discovery request."""


class OSMBusinessDiscovery:
    """Search OSM-mapped businesses in a named South African area."""

    def __init__(
        self,
        config: OSMDiscoveryConfig | None = None,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        if config is None:
            config = OSMDiscoveryConfig(
                endpoint=os.getenv("OVERPASS_URL", DEFAULT_OVERPASS_URL).strip()
                or DEFAULT_OVERPASS_URL
            )
        if not config.endpoint.startswith("https://"):
            raise ValueError("Overpass endpoint must use HTTPS")
        if not 1 <= config.max_results <= 100:
            raise ValueError("max_results must be between 1 and 100")
        if not 5 <= config.minimum_request_interval_seconds <= 3600:
            raise ValueError("minimum request interval must be between 5 and 3600 seconds")
        self.config = config
        self._external_client = client is not None
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(config.timeout_seconds),
            headers={"User-Agent": config.user_agent, "Accept": "application/json"},
        )

    def close(self) -> None:
        if not self._external_client:
            self.client.close()

    def __enter__(self) -> "OSMBusinessDiscovery":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def build_query(category: str, area_name: str, limit: int = 50) -> str:
        category = category.strip().lower()
        if category not in CATEGORY_TAGS:
            raise ValueError(
                f"Unsupported category '{category}'. Choose from: {', '.join(sorted(CATEGORY_TAGS))}"
            )
        area_name = area_name.strip()
        if not AREA_PATTERN.fullmatch(area_name):
            raise ValueError("Area name must be 1-80 plain letters, numbers, spaces, apostrophes, dots or hyphens")
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        key, value = CATEGORY_TAGS[category]
        # Area input is restricted above; tag keys/values come only from the fixed map.
        return (
            f'[out:json][timeout:25];\n'
            f'area["name"="{area_name}"]["boundary"="administrative"]->.searchArea;\n'
            f'(\n'
            f'  node["{key}"="{value}"](area.searchArea);\n'
            f'  way["{key}"="{value}"](area.searchArea);\n'
            f'  relation["{key}"="{value}"](area.searchArea);\n'
            f');\n'
            f'out center tags {limit};'
        )

    @staticmethod
    def _record(element: dict[str, Any], fetched_at: str) -> dict[str, Any]:
        tags = element.get("tags") or {}
        center = element.get("center") or {}
        lat = element.get("lat", center.get("lat"))
        lon = element.get("lon", center.get("lon"))
        osm_type = str(element.get("type", ""))
        osm_id = element.get("id")
        if osm_type not in {"node", "way", "relation"} or not isinstance(osm_id, int):
            raise ValueError("Overpass returned an invalid OSM element identity")
        website = tags.get("contact:website") or tags.get("website")
        phone = tags.get("contact:phone") or tags.get("phone")
        email = tags.get("contact:email") or tags.get("email")
        return {
            "source": "openstreetmap",
            "source_id": f"{osm_type}/{osm_id}",
            "source_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
            "fetched_at": fetched_at,
            "name": tags.get("name", ""),
            "category": tags.get("craft") or tags.get("office") or tags.get("healthcare")
            or tags.get("amenity") or tags.get("shop") or tags.get("tourism", ""),
            "website": website or "",
            "phone": phone or "",
            "email": email or "",
            "address": {
                "house_number": tags.get("addr:housenumber", ""),
                "street": tags.get("addr:street", ""),
                "suburb": tags.get("addr:suburb", ""),
                "city": tags.get("addr:city", ""),
                "province": tags.get("addr:province", ""),
                "postcode": tags.get("addr:postcode", ""),
                "country": tags.get("addr:country", ""),
            },
            "latitude": lat,
            "longitude": lon,
            "tags": dict(tags),
            "attribution": OSM_ATTRIBUTION,
            "license": "ODbL-1.0",
            "license_url": OSM_LICENSE_URL,
        }

    def search_businesses(
        self,
        category: str,
        area_name: str,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        result_limit = limit if limit is not None else self.config.max_results
        if not 1 <= result_limit <= self.config.max_results:
            raise ValueError(f"limit must be between 1 and {self.config.max_results}")
        query = self.build_query(category, area_name, result_limit)
        try:
            response = self.client.post(
                self.config.endpoint,
                data={"data": query},
                headers={"User-Agent": self.config.user_agent},
                timeout=self.config.timeout_seconds,
            )
            if response.status_code in {429, 503, 504}:
                raise OSMDiscoveryError(
                    f"Overpass is busy (HTTP {response.status_code}). Pause before retrying; do not parallelise requests."
                )
            response.raise_for_status()
            payload = response.json()
        except OSMDiscoveryError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise OSMDiscoveryError(f"OpenStreetMap discovery failed: {exc}") from exc

        elements = payload.get("elements", [])
        if not isinstance(elements, list):
            raise OSMDiscoveryError("Overpass returned an unexpected response shape")
        fetched_at = datetime.now(timezone.utc).isoformat()
        records: list[dict[str, Any]] = []
        seen: set[str] = set()
        for element in elements:
            if not isinstance(element, dict):
                continue
            try:
                record = self._record(element, fetched_at)
            except (TypeError, ValueError):
                continue
            if record["source_id"] in seen:
                continue
            seen.add(record["source_id"])
            records.append(record)
            if len(records) >= result_limit:
                break
        return records


def main() -> int:
    """CLI entry point; run with python -m scraper.osm_discovery."""
    import argparse
    import csv
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Ubernie RSA business discovery via OpenStreetMap")
    parser.add_argument("--category", required=True, choices=sorted(CATEGORY_TAGS))
    parser.add_argument("--area", required=True, help="South African province, city or mapped administrative area")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", default="osm-businesses.json", help="Output .json or .csv file")
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("limit must be between 1 and 100")

    with OSMBusinessDiscovery(OSMDiscoveryConfig(max_results=args.limit)) as discovery:
        records = discovery.search_businesses(args.category, args.area, limit=args.limit)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        fields = ["source", "source_id", "source_url", "fetched_at", "name", "category",
                  "website", "phone", "email", "latitude", "longitude", "attribution", "license"]
        with output.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for record in records:
                writer.writerow({key: record.get(key, "") for key in fields})
    else:
        output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Discovered {len(records)} OSM-mapped businesses. Results: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
