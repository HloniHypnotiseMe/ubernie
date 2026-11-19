import json
import sys
from pathlib import Path

import httpx
import pytest

WEB_DEPARTMENT = Path(__file__).resolve().parents[2]
if str(WEB_DEPARTMENT) not in sys.path:
    sys.path.insert(0, str(WEB_DEPARTMENT))

from scraper.osm_discovery import (
    CATEGORY_TAGS,
    OSM_ATTRIBUTION,
    OSMDiscoveryConfig,
    OSMBusinessDiscovery,
    OSMDiscoveryError,
)


def make_discovery(handler, **kwargs):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = OSMDiscoveryConfig(minimum_request_interval_seconds=5, **kwargs)
    return OSMBusinessDiscovery(config, client=client)


def test_builds_bounded_south_african_area_query():
    query = OSMBusinessDiscovery.build_query("plumber", "Gauteng", 25)
    assert 'area["name"="Gauteng"]["boundary"="administrative"]' in query
    assert 'node["craft"="plumber"]' in query
    assert 'way["craft"="plumber"]' in query
    assert 'relation["craft"="plumber"]' in query
    assert query.endswith("out center tags 25;")


def test_rejects_unknown_category_and_query_injection():
    with pytest.raises(ValueError, match="Unsupported category"):
        OSMBusinessDiscovery.build_query("anything", "Gauteng")
    with pytest.raises(ValueError, match="Area name"):
        OSMBusinessDiscovery.build_query("plumber", 'Gauteng"];node;out;')
    with pytest.raises(ValueError):
        OSMBusinessDiscovery.build_query("plumber", "Gauteng", 101)


def test_search_maps_nodes_and_ways_with_provenance():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"elements": [
            {"type": "node", "id": 101, "lat": -26.2, "lon": 28.0,
             "tags": {"name": "Example Plumbing", "craft": "plumber",
                      "contact:phone": "+27 11 555 0100", "website": "https://example.org",
                      "addr:city": "Johannesburg"}},
            {"type": "way", "id": 202, "center": {"lat": -26.3, "lon": 28.1},
             "tags": {"name": "Second Plumbing", "craft": "plumber"}},
        ]})

    discovery = make_discovery(handler)
    try:
        records = discovery.search_businesses("plumber", "Gauteng")
    finally:
        discovery.close()

    assert len(records) == 2
    first = records[0]
    assert first["source_id"] == "node/101"
    assert first["name"] == "Example Plumbing"
    assert first["phone"] == "+27 11 555 0100"
    assert first["address"]["city"] == "Johannesburg"
    assert first["latitude"] == -26.2
    assert first["attribution"] == OSM_ATTRIBUTION
    assert first["license"] == "ODbL-1.0"
    assert calls[0].headers["User-Agent"].startswith("UbernieRSA-BusinessDiscovery/")
    assert "Gauteng" in calls[0].content.decode()


def test_deduplicates_repeated_osm_ids_and_respects_limit():
    def handler(request):
        return httpx.Response(200, json={"elements": [
            {"type": "node", "id": 1, "lat": 0, "lon": 0, "tags": {"name": "A"}},
            {"type": "node", "id": 1, "lat": 0, "lon": 0, "tags": {"name": "A"}},
            {"type": "node", "id": 2, "lat": 1, "lon": 1, "tags": {"name": "B"}},
        ]})

    discovery = make_discovery(handler, max_results=2)
    try:
        records = discovery.search_businesses("cafe", "Johannesburg", limit=1)
    finally:
        discovery.close()
    assert len(records) == 1
    assert records[0]["source_id"] == "node/1"


def test_overpass_busy_response_is_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429, text="rate limited")

    discovery = make_discovery(handler)
    try:
        with pytest.raises(OSMDiscoveryError, match="Pause before retrying"):
            discovery.search_businesses("restaurant", "Cape Town")
    finally:
        discovery.close()
    assert len(calls) == 1


def test_rejects_non_https_endpoint_and_unbounded_config():
    with pytest.raises(ValueError, match="HTTPS"):
        OSMBusinessDiscovery(OSMDiscoveryConfig(endpoint="http://example.org/api"))
    with pytest.raises(ValueError, match="max_results"):
        OSMBusinessDiscovery(OSMDiscoveryConfig(max_results=500))


def test_supported_categories_are_fixed_and_nonempty():
    assert "plumber" in CATEGORY_TAGS
    assert "restaurant" in CATEGORY_TAGS
    assert len(CATEGORY_TAGS) >= 15
