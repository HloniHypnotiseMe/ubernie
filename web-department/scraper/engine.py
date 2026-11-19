from __future__ import annotations

import ipaddress
import json
import socket
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup


@dataclass
class ScrapeConfig:
    max_pages: int = 25
    max_depth: int = 2
    timeout_seconds: float = 15.0
    max_bytes_per_page: int = 2_000_000
    delay_seconds: float = 1.0
    user_agent: str = "C6UniversalScraper/0.1 (+https://www.ubernie.co.za; public-data research)"
    respect_robots_txt: bool = True
    same_domain_only: bool = True


@dataclass
class ScrapeResult:
    url: str
    final_url: str
    status_code: int | None
    fetched_at: str
    title: str = ""
    description: str = ""
    canonical_url: str = ""
    text: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    json_ld: list[dict] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only absolute HTTP(S) URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed")
    host = parsed.hostname.lower().rstrip(".")
    port = parsed.port
    netloc = host if port is None or (parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443) else f"{host}:{port}"
    path = parsed.path or "/"
    clean = urlunparse((parsed.scheme.lower(), netloc, path, "", parsed.query, ""))
    return urldefrag(clean)[0]


def _assert_public_host(host: str) -> None:
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)]
        except OSError as exc:
            raise ValueError(f"Could not resolve host: {host}") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Private, loopback, link-local and non-public destinations are blocked")


class Scraper:
    """Small production-oriented crawler for public pages; no login or CAPTCHA bypass."""

    def __init__(self, config: ScrapeConfig | None = None, *, client: httpx.Client | None = None):
        self.config = config or ScrapeConfig()
        self._external_client = client is not None
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(self.config.timeout_seconds),
            headers={"User-Agent": self.config.user_agent, "Accept": "text/html,application/xhtml+xml"},
            follow_redirects=False,
        )
        self._robots: dict[str, RobotFileParser] = {}
        self._last_request: dict[str, float] = {}

    def close(self) -> None:
        if not self._external_client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _allowed_by_robots(self, url: str) -> bool:
        if not self.config.respect_robots_txt:
            return True
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            parser = RobotFileParser()
            robots_url = f"{origin}/robots.txt"
            try:
                response = self.client.get(robots_url, timeout=self.config.timeout_seconds)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                elif response.status_code == 404:
                    # A missing robots.txt means the origin publishes no crawl rules.
                    parser.parse([])
                else:
                    # Do not crawl when a policy endpoint redirects, rate-limits or fails.
                    parser.parse(["User-agent: *", "Disallow: /"])
            except httpx.HTTPError:
                # Fail closed when the site's crawl policy cannot be read.
                parser.parse(["User-agent: *", "Disallow: /"])
            self._robots[origin] = parser
        return self._robots[origin].can_fetch(self.config.user_agent, url)

    def _get(self, url: str) -> tuple[httpx.Response, str]:
        current = url
        for _ in range(6):
            parsed = urlparse(current)
            _assert_public_host(parsed.hostname or "")
            if not self._allowed_by_robots(current):
                raise PermissionError("Blocked by robots.txt")
            host = parsed.netloc.lower()
            wait = self.config.delay_seconds - (time.monotonic() - self._last_request.get(host, 0.0))
            if wait > 0:
                time.sleep(wait)
            response = self.client.get(current, timeout=self.config.timeout_seconds)
            self._last_request[host] = time.monotonic()
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    return response, current
                current = normalize_url(urljoin(current, location))
                continue
            return response, current
        raise RuntimeError("Too many redirects")

    def _extract(self, requested_url: str, response: httpx.Response, final_url: str) -> ScrapeResult:
        now = datetime.now(timezone.utc).isoformat()
        result = ScrapeResult(requested_url, final_url, response.status_code, now)
        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type and "xhtml" not in content_type:
            result.error = f"Unsupported content type: {content_type or 'missing'}"
            return result
        if len(response.content) > self.config.max_bytes_per_page:
            result.error = "Response exceeded max_bytes_per_page"
            return result
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            if tag.get("type") != "application/ld+json":
                tag.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        result.title = title[:500]
        description = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        result.description = (description.get("content", "") if description else "")[:2000]
        canonical = soup.find("link", rel="canonical")
        result.canonical_url = urljoin(final_url, canonical.get("href")) if canonical and canonical.get("href") else final_url
        result.text = " ".join(soup.stripped_strings)[:100_000]
        import re
        result.emails = sorted(set(re.findall(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", result.text)))[:100]
        result.phones = sorted(set(re.findall(r"(?<!\w)(?:\+27|0)[\s().-]*(?:\d[\s().-]*){8,10}", result.text)))[:100]
        for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                value = json.loads(node.string or node.get_text())
                result.json_ld.extend(value if isinstance(value, list) else [value])
            except (ValueError, TypeError):
                continue
        links = set()
        for anchor in soup.find_all("a", href=True):
            candidate = urljoin(final_url, anchor["href"])
            try:
                candidate = normalize_url(candidate)
                target = urlparse(candidate)
                if target.hostname and target.scheme in {"http", "https"}:
                    links.add(candidate)
            except ValueError:
                continue
        result.links = sorted(links)
        return result

    def crawl(self, start_urls: list[str]) -> list[ScrapeResult]:
        if not start_urls:
            raise ValueError("At least one start URL is required")
        queue = deque((normalize_url(url), 0) for url in start_urls)
        seen: set[str] = set()
        seen_canonicals: set[str] = set()
        start_hosts = {urlparse(url).hostname for url, _ in queue}
        results: list[ScrapeResult] = []
        while queue and len(results) < self.config.max_pages:
            url, depth = queue.popleft()
            if url in seen or depth > self.config.max_depth:
                continue
            seen.add(url)
            try:
                response, final_url = self._get(url)
                result = self._extract(url, response, final_url)
                if response.status_code < 400 and not result.error:
                    canonical = normalize_url(result.canonical_url or final_url)
                    if canonical in seen_canonicals:
                        continue
                    seen_canonicals.add(canonical)
                if response.status_code >= 400:
                    result.error = f"HTTP {response.status_code}"
                results.append(result)
                if response.status_code < 400 and depth < self.config.max_depth and not result.error:
                    for link in result.links:
                        if link not in seen and (not self.config.same_domain_only or urlparse(link).hostname in start_hosts):
                            queue.append((link, depth + 1))
            except (httpx.HTTPError, ValueError, PermissionError, RuntimeError) as exc:
                results.append(ScrapeResult(url, url, None, datetime.now(timezone.utc).isoformat(), error=str(exc)))
        return results
