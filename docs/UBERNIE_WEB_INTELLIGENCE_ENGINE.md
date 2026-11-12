# UBERNIE Web Intelligence & Business Discovery Engine

**Product owner:** RemotePay Fintech Services  
**Product:** UBERNIE  
**Public identity:** UBERNIE only. UBERNIE is not a C6 Group-branded product and must not depend on C6 Group branding or public navigation.

## Objective

Turn UBERNIE into a South African-first business discovery and intelligence platform that can discover public business information, extract and normalize it, identify duplicates, enrich and score records, verify evidence, and publish approved records into UBERNIE's directory and merchant acquisition workflows.

The objective is capability reuse: inspect repositories already present in the controlled technology estate, extract the smallest useful components, adapt them into UBERNIE-owned modules, and maintain the resulting implementation in this repository. Do not make UBERNIE depend on a separate C6 product at runtime.

## Ownership and boundaries

- RemotePay Fintech Services owns UBERNIE.
- UBERNIE owns its domain, brand, customers, directory data, merchant relationships, product roadmap and commercial operations.
- C6-Os and the wider repository estate may be used as an internal technology and capability source. They are not UBERNIE's public parent identity.
- RemotePay may provide payment processing under a documented merchant/payment contract. Payment truth remains with the verified payment provider webhook and reconciliation evidence.
- Shared infrastructure may be consumed through explicit, replaceable interfaces. UBERNIE must retain its own product data model and tenant/brand configuration.
- BBLA and LBF are intended to be separate directory brands/tenants on the UBERNIE engine, with explicit brand-level data, domain, admin and publication isolation. This is a target architecture, not a claim that isolation is already implemented.

## Capability pipeline

```text
Source Registry
    -> Policy & Permission Gate
    -> Scheduler / Crawl Queue
    -> Fetch & Browser Extraction
    -> Parse / Normalize
    -> Business Entity Resolution
    -> Evidence & Confidence Scoring
    -> Human Review / Automated Approval Rules
    -> UBERNIE Directory
    -> Search / Maps / Insights / Merchant Outreach
```

### Required owned modules

1. **Source Registry** — source URL/domain, source type, permitted collection method, terms/policy review, crawl frequency, rate limit, last checked, owner and status.
2. **Collection Scheduler** — queues, retries, concurrency limits, per-domain throttling and pause/kill switch.
3. **Fetch Adapters** — HTTP extraction first; browser rendering only where required and permitted.
4. **Extraction Profiles** — source-specific selectors/schema, structured-data extraction, contact and location extraction.
5. **Normalization** — consistent names, addresses, phone numbers, URLs, categories and geographic coordinates.
6. **Entity Resolution** — deduplication using normalized identifiers and confidence; never merge uncertain entities silently.
7. **Evidence Ledger** — source URL, retrieval timestamp, captured fields, transformation history, confidence, review status and deletion/refresh history.
8. **Verification Workflow** — distinguish discovered, source-supported, business-confirmed and independently verified records.
9. **Intelligence Scoring** — completeness, freshness, source reliability, business activity signals and opportunity indicators.
10. **Publication Gateway** — only approved records enter public directory/search indexes.
11. **Tenant/Brand Boundary** — brand-specific domain, category configuration, moderation, admin roles, analytics and publication rules.
12. **Operations Dashboard** — crawl health, queue depth, errors, spend, coverage, freshness, duplicate rate, review backlog and conversion outcomes.

## Existing UBERNIE components to reuse

The current repository documents:
- Laravel directory/application layer with business profiles, categories, listings and search-related services.
- Meilisearch for directory search.
- Leaflet/OpenStreetMap for geographic presentation.
- Python FastAPI Web Department for merchant sites, orders, rider and tracking surfaces.
- Existing n8n workflow assets.
- RemotePay payment-link integration with webhook-gated payment confirmation.

These are existing code/documentation surfaces, not proof that every feature is deployed or live. The intelligence pipeline must integrate through explicit contracts and must not bypass the Web Department's production payment invariants.

## Arsenal candidates — not yet extracted into UBERNIE

| Capability | Registered provider/source | Intended UBERNIE use | Decision |
|---|---|---|---|
| Web scraping / extraction | Scrapling (C6-Os provider registry) | HTTP/browser-aware collection and extraction | Inspect exact repository identity, fork status, source commit, licence and dependency closure before extraction |
| Browser automation | HeadlessX | Dynamic pages, browser-rendered extraction and controlled browser jobs | Candidate only; AGPL-3.0 creates network-copyleft obligations that require an explicit legal/product decision before incorporation |
| Page understanding / browser agent | Alibaba Page-Agent | Optional interactive page understanding for permitted workflows | MIT; not a crawler replacement; extract only if a real page-agent use case justifies it |
| Workflow automation | C6-controlled n8n fork | Scheduling, retries, notifications and business workflow triggers | Reuse workflow patterns or a narrow adapter; do not couple core ingestion correctness to a visual workflow |
| Search | Existing UBERNIE Meilisearch integration | Search published business records | Retain as search index, not the system of record |
| Maps/geography | Existing Leaflet + OpenStreetMap | Map discovery and geographic enrichment | Retain; verify OSM attribution and tile/service policy |

A provider being registered or locally present in C6-Os does not establish that it is installed in UBERNIE, pinned, healthy or production-ready. No candidate above is represented as already extracted or live.

## Extraction rules

For every capability adopted:
- Record exact source repository, source component, immutable commit/tag and fork/upstream status.
- Review licence and preserve copyright, notices and attribution.
- Record dependency closure, security posture, data flows and required permissions.
- Import only the smallest sufficient component.
- Adapt it behind an UBERNIE-owned interface.
- Keep credentials outside source control.
- Add deterministic tests, fixtures and operational telemetry.
- Record files imported, files deliberately excluded, tests and proof.
- Do not use CAPTCHA bypass, credential theft, access-control circumvention or collection that violates applicable terms or law.

## Data governance and POPIA

- Collect only business information needed for a stated directory or intelligence purpose.
- Record source and collection time for every material field.
- Distinguish public business contact details from personal information; public availability does not remove POPIA obligations.
- Provide correction, objection, suppression and deletion workflows where applicable.
- Apply retention limits and source refresh/expiry rules.
- Respect robots directives, published terms, rate limits and technical access controls; escalate unclear cases for review.
- Never present an unverified scraped record as a verified business.
- Keep personal contact data, enrichment and outreach eligibility behind role-based permissions and audit logs.

## Delivery sequence

### Phase 0 — Evidence audit
Inspect UBERNIE's current default branch, source tree, database migrations, auth/tenant model, search implementation, tests, deployment contract and existing workflows. Reconcile C6 Arsenal candidates against actual controlled forks and exact source commits.

### Phase 1 — Owned ingestion foundation
Implement UBERNIE-owned source registry, collection job model, queue contract, permission/rate-limit policy, extraction result schema and evidence ledger. No external crawler is embedded until source and licence review is complete.

### Phase 2 — Narrow capability extraction
Select the best-fit extraction component after the Phase 0 review. Import only required modules, preserve licence obligations, wrap with UBERNIE interfaces and add fixture-based tests.

### Phase 3 — Business intelligence
Add normalization, entity resolution, confidence scoring, verification/review and controlled publication to Meilisearch.

### Phase 4 — Commercial workflows
Connect approved records to merchant claim/onboarding, website generation, lead routing and RemotePay payment initiation. Payment status must continue to be confirmed only by verified provider evidence.

### Phase 5 — Multi-brand directory operation
Prove independent brand/domain/admin/data isolation for UBERNIE, BBLA and LBF before enabling multiple brands in production.

## Acceptance gates

- A crawl job can be created, paused, resumed, retried and audited.
- Every extracted field has source provenance and retrieval timestamp.
- Duplicate candidates are detected without destructive automatic merging.
- Unreviewed records cannot silently become verified/public.
- Per-domain rate limits and global kill switch work.
- Tenant/brand boundaries are enforced in API and database queries.
- Search index can be rebuilt from approved source-of-truth records.
- Tests cover malformed pages, timeouts, retries, duplicate entities, stale records, opt-outs and permission denials.
- Production deployment, monitoring, backup/restore and data-retention behaviour are demonstrated.
- No production-ready or live claim without recorded evidence.

## Current status

**Architecture decision recorded.**  
**Git branch created:** `feature/ubernie-intelligence-acquisition`  
**Implementation status:** Not yet extracted or deployed.  
**Immediate next gate:** complete Phase 0 source-tree and runtime audit, then select and legally clear the smallest viable extraction.
