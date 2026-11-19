import json

import httpx
import pytest

from scraper.engine import ScrapeConfig, Scraper, normalize_url, _assert_public_host

HTML = b'''<!doctype html><html><head><title>Example Business</title><meta name="description" content="A local service"><link rel="canonical" href="/about"><script type="application/ld+json">{"@type":"LocalBusiness","name":"Example Business","telephone":"+27 11 555 0100"}</script></head><body><h1>Example Business</h1><p>Email hello@example.org or call 011 555 0100.</p><a href="/contact">Contact</a><a href="https://outside.example/path">Outside</a></body></html>'''


def make_scraper(handler, **kwargs):
    client = httpx.Client(transport=httpx.MockTransport(handler), headers={"User-Agent": "test-agent"})
    config = ScrapeConfig(respect_robots_txt=False, delay_seconds=0, **kwargs)
    return Scraper(config, client=client)


def test_normalize_url_removes_fragment_and_default_port():
    assert normalize_url("HTTPS://Example.org:443/a#section") == "https://example.org/a"


def test_rejects_non_http_and_credentials():
    with pytest.raises(ValueError):
        normalize_url("file:///etc/passwd")
    with pytest.raises(ValueError):
        normalize_url("https://user:pass@example.org/")


def test_blocks_loopback_and_private_ip():
    for host in ("127.0.0.1", "10.0.0.5", "::1"):
        with pytest.raises(ValueError):
            _assert_public_host(host)


def test_extracts_business_fields_and_jsonld(monkeypatch):
    monkeypatch.setattr("scraper.engine._assert_public_host", lambda host: None)
    scraper = make_scraper(lambda request: httpx.Response(200, headers={"content-type": "text/html"}, content=HTML))
    try:
        results = scraper.crawl(["https://example.org/"])
    finally:
        scraper.close()
    assert len(results) == 1
    item = results[0]
    assert item.title == "Example Business"
    assert item.description == "A local service"
    assert item.canonical_url == "https://example.org/about"
    assert item.emails == ["hello@example.org"]
    assert item.json_ld[0]["@type"] == "LocalBusiness"
    assert "https://example.org/contact" in item.links
    assert item.status_code == 200


def test_crawl_is_same_domain_and_page_bounded(monkeypatch):
    monkeypatch.setattr("scraper.engine._assert_public_host", lambda host: None)
    calls = []
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, headers={"content-type": "text/html"}, content=HTML)
    scraper = make_scraper(handler, max_pages=2, max_depth=3)
    try:
        results = scraper.crawl(["https://example.org/"])
    finally:
        scraper.close()
    assert len(results) == 2
    assert len(calls) == 2
    assert all("outside.example" not in url for url in calls)


def test_http_errors_are_reported(monkeypatch):
    monkeypatch.setattr("scraper.engine._assert_public_host", lambda host: None)
    scraper = make_scraper(lambda request: httpx.Response(503, headers={"content-type": "text/html"}, content=b"down"))
    try:
        result = scraper.crawl(["https://example.org/"])[0]
    finally:
        scraper.close()
    assert result.status_code == 503
    assert result.error == "HTTP 503"


def test_robots_denial_is_reported(monkeypatch):
    monkeypatch.setattr("scraper.engine._assert_public_host", lambda host: None)
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\\nDisallow: /")
        return httpx.Response(200, headers={"content-type": "text/html"}, content=HTML)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    scraper = Scraper(ScrapeConfig(delay_seconds=0), client=client)
    try:
        result = scraper.crawl(["https://example.org/"])[0]
    finally:
        scraper.close()
    assert result.status_code is None
    assert "robots.txt" in result.error
