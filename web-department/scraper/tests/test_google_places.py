import httpx
import pytest

from scraper.google_places import (
    FIELD_MASK,
    SEARCH_URL,
    GooglePlacesClient,
    GooglePlacesConfig,
    GooglePlacesError,
)


def test_search_uses_south_africa_region_and_explicit_field_mask():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"places": [
            {"id": "za-place-1", "displayName": {"text": "Example Plumber"},
             "formattedAddress": "Johannesburg, South Africa",
             "websiteUri": "https://example.org"}
        ]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    places = GooglePlacesClient(GooglePlacesConfig(api_key="test-key"), client=client)
    try:
        results = places.search_businesses("plumbers in Johannesburg")
    finally:
        places.close()

    assert len(results) == 1
    assert results[0]["id"] == "za-place-1"
    request = calls[0]
    assert request.url == SEARCH_URL
    assert request.headers["X-Goog-Api-Key"] == "test-key"
    assert request.headers["X-Goog-FieldMask"] == FIELD_MASK
    body = request.read()
    assert b'"regionCode":"ZA"' in body
    assert b'"includePureServiceAreaBusinesses":true' in body


def test_follows_next_page_token_without_changing_query():
    bodies = []

    def handler(request):
        import json
        body = json.loads(request.content)
        bodies.append(body)
        if len(bodies) == 1:
            return httpx.Response(200, json={"places": [{"id": "one"}], "nextPageToken": "next"})
        return httpx.Response(200, json={"places": [{"id": "two"}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    places = GooglePlacesClient(
        GooglePlacesConfig(api_key="test-key", max_pages=2), client=client
    )
    try:
        results = places.search_businesses("accountants in Cape Town")
    finally:
        places.close()

    assert [item["id"] for item in results] == ["one", "two"]
    assert bodies[0]["textQuery"] == bodies[1]["textQuery"]
    assert bodies[1]["pageToken"] == "next"


def test_rejects_empty_query_and_invalid_page_limits():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})))
    places = GooglePlacesClient(GooglePlacesConfig(api_key="test-key"), client=client)
    try:
        with pytest.raises(ValueError):
            places.search_businesses("  ")
        with pytest.raises(ValueError):
            places.search_businesses("builders in Durban", page_limit=4)
    finally:
        places.close()


def test_missing_api_key_is_clear(monkeypatch):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    with pytest.raises(GooglePlacesError, match="GOOGLE_MAPS_API_KEY"):
        GooglePlacesClient()
