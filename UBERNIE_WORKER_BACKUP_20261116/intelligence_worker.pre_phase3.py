"""Controlled public-web fetch worker for UBERNIE intelligence jobs."""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from sqlalchemy.orm import Session

from db.models import IntelligenceJob, IntelligenceSource
from intelligence import _host, ingest_candidate
from intelligence_extractor import extract_business_entities


USER_AGENT = "UBERNIEBusinessIntelligenceBot/1.0"
MAX_HTML_BYTES = 2 * 1024 * 1024
MAX_ROBOTS_BYTES = 256 * 1024
TIMEOUT_SECONDS = 20
MAX_ATTEMPTS = 3


class CollectionBlocked(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _assert_public_host(host: str) -> None:
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise CollectionBlocked("private_host_blocked")
    try:
        literal = ipaddress.ip_address(host)
        if not literal.is_global:
            raise CollectionBlocked("non_public_ip_blocked")
        return
    except ValueError:
        pass

    try:
        results = await asyncio.to_thread(
            socket.getaddrinfo, host, 443, type=socket.SOCK_STREAM
        )
    except OSError as exc:
        raise CollectionBlocked("dns_resolution_failed") from exc

    addresses = {item[4][0] for item in results}
    if not addresses:
        raise CollectionBlocked("dns_resolution_failed")
    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise CollectionBlocked("non_public_ip_blocked")


async def _read_bounded(response: httpx.Response, maximum: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > maximum:
            raise CollectionBlocked("response_size_limit")
        chunks.append(chunk)
    return b"".join(chunks)


async def fetch_permitted_html(url: str, requests_per_minute: int) -> bytes:
    host = _host(url)
    await _assert_public_host(host)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9",
    }
    timeout = httpx.Timeout(TIMEOUT_SECONDS, connect=8.0)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
        headers=headers,
    ) as client:
        robots_url = f"https://{host}/robots.txt"
        try:
            robots_response = await client.get(robots_url)
        except httpx.HTTPError as exc:
            raise CollectionBlocked("robots_unavailable") from exc

        parser = RobotFileParser()
        if robots_response.status_code == 200:
            robots_bytes = await _read_bounded(robots_response, MAX_ROBOTS_BYTES)
            parser.parse(robots_bytes.decode("utf-8", errors="replace").splitlines())
        elif robots_response.status_code in (404, 410):
            parser.parse([])
        else:
            raise CollectionBlocked("robots_policy_unavailable")

        if not parser.can_fetch(USER_AGENT, url):
            raise CollectionBlocked("robots_disallowed")

        # Sequential per-source pacing. Distributed rate limiting belongs in the
        # production scheduler before horizontal worker scaling.
        await asyncio.sleep(60.0 / max(1, min(requests_per_minute, 30)))

        try:
            async with client.stream("GET", url) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    raise CollectionBlocked("redirect_blocked")
                if response.status_code != 200:
                    raise CollectionBlocked(f"http_status_{response.status_code}")
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    raise CollectionBlocked("non_html_content_type")
                return await _read_bounded(response, MAX_HTML_BYTES)
        except httpx.HTTPError as exc:
            raise CollectionBlocked("http_fetch_failed") from exc


async def execute_job(db: Session, job_id: str) -> dict:
    job = db.get(IntelligenceJob, job_id)
    if job is None:
        raise ValueError("job_not_found")
    if job.status not in ("queued", "failed"):
        raise ValueError("job_not_runnable")
    if job.attempts >= MAX_ATTEMPTS:
        raise ValueError("job_attempt_limit")

    source = db.get(IntelligenceSource, job.source_id)
    if source is None or not source.enabled:
        raise ValueError("source_disabled")
    if _host(job.requested_url) != urlparse(source.base_url).hostname:
        raise ValueError("source_host_mismatch")

    job.status = "running"
    job.attempts += 1
    job.started_at = _now()
    job.error_code = None
    db.commit()

    try:
        html = await fetch_permitted_html(job.requested_url, source.requests_per_minute)
        records = extract_business_entities(html, job.requested_url)
        created = 0
        duplicates = 0
        for record in records:
            candidate, duplicate = ingest_candidate(
                db,
                source_id=source.id,
                source_url=job.requested_url,
                business_name=record.pop("business_name") or "",
                created_fields=record,
            )
            duplicates += int(duplicate)
            created += int(not duplicate)

        job.status = "completed" if records else "completed_no_candidates"
        job.finished_at = _now()
        db.commit()
        return {
            "job_id": job.id,
            "status": job.status,
            "pages_fetched": 1,
            "candidates_created": created,
            "duplicates_detected": duplicates,
        }
    except CollectionBlocked as exc:
        job.status = "failed"
        job.error_code = str(exc)
        job.finished_at = _now()
        db.commit()
        return {"job_id": job.id, "status": job.status, "error_code": job.error_code}
    except Exception:
        job.status = "failed"
        job.error_code = "worker_error"
        job.finished_at = _now()
        db.commit()
        raise
