"""Google Places discovery adapter.

Google Maps content is returned for immediate in-app display only. Do not persist
business names, addresses, phone numbers, websites, ratings, or other Places
content in Ubernie's independent lead database. Place IDs may be retained.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join(
    (
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.primaryType",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.googleMapsUri",
        "places.businessStatus",
        "nextPageToken",
    )
)


@dataclass(frozen=True)
class GooglePlacesConfig:
    api_key: str
    timeout_seconds: float = 15.0
    page_size: int = 20
    max_pages: int = 3
    region_code: str = "ZA"
    language_code: str = "en"


class GooglePlacesError(RuntimeError):
    """Raised when Google Places cannot complete a discovery request."""


class GooglePlacesClient:
    """Search Google Places for RSA businesses; never writes Places content to disk."""

    def __init__(
        self,
        config: GooglePlacesConfig | None = None,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        if config is None:
            api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
            if not api_key:
                raise GooglePlacesError("Set GOOGLE_MAPS_API_KEY before using Google Places")
            config = GooglePlacesConfig(api_key=api_key)
        if not config.api_key.strip():
            raise GooglePlacesError("Google Maps API key cannot be empty")
        if not 1 <= config.page_size <= 20:
            raise ValueError("page_size must be between 1 and 20")
        if not 1 <= config.max_pages <= 3:
            raise ValueError("max_pages must be between 1 and 3 (Google Text Search limit)")
        if config.region_code != "ZA":
            raise ValueError("This adapter is configured for South Africa (region_code='ZA')")
        self.config = config
        self._external_client = client is not None
        self.client = client or httpx.Client(timeout=config.timeout_seconds)

    def close(self) -> None:
        if not self._external_client:
            self.client.close()

    def __enter__(self) -> "GooglePlacesClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def search_businesses(
        self,
        query: str,
        *,
        page_limit: int | None = None,
        include_service_area_businesses: bool = True,
    ) -> list[dict[str, Any]]:
        """Return transient Google Places records for immediate in-app display.

        The caller may retain the Google place ID. All other returned fields are
        Google Maps Content and must remain subject to Places display/storage rules.
        """
        query = query.strip()
        if not query:
            raise ValueError("A business category or search query is required")
        pages = page_limit if page_limit is not None else self.config.max_pages
        if not 1 <= pages <= self.config.max_pages:
            raise ValueError(f"page_limit must be between 1 and {self.config.max_pages}")

        results: list[dict[str, Any]] = []
        page_token: str | None = None
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.config.api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        }
        for _ in range(pages):
            body: dict[str, Any] = {
                "textQuery": query,
                "pageSize": self.config.page_size,
                "regionCode": self.config.region_code,
                "languageCode": self.config.language_code,
                "includePureServiceAreaBusinesses": include_service_area_businesses,
            }
            if page_token:
                body["pageToken"] = page_token
            try:
                response = self.client.post(SEARCH_URL, headers=headers, json=body)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise GooglePlacesError(f"Google Places search failed: {exc}") from exc

            for place in payload.get("places", []):
                # Keep the exact Google response fields transient. The app must not
                # copy these values into its independent business/lead database.
                results.append(dict(place))
            page_token = payload.get("nextPageToken")
            if not page_token:
                break
        return results
