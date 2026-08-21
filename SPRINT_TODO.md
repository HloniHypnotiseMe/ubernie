# C6 Economic Sprint — 3-System TODO

**Scope:** C6 Group website + RemotePay + Ubernie only.
**Date:** 2026-08-21
**Destination:** Business discovery → evidence → offer/package → checkout/payment → measurable revenue event.

## Status

- [x] Locate and scope the three systems.
- [x] Confirm Ubernie local codebase and create GitHub baseline.
- [x] Normalize Ubernie remote to `https://github.com/HloniHypnotiseMe/ubernie.git`.
- [x] Confirm RemotePay GitHub repository: `HloniHypnotiseMe/RemotePay-`.
- [x] Confirm C6 Group website GitHub repository: `HloniHypnotiseMe/C6-Group-Final-Website`.
- [x] Complete scoped three-system audit package: `C6_3SYSTEM_AUDIT_20260821_161644`.
- [x] Establish production-integrity PR #1 on the C6 Group website.
- [x] Remove synthetic/local fallback audit results from the C6 audit flow in PR #1.

## Current blockers / gates

- [ ] C6 website PR #1 must have verified build/tests before merge. GitHub currently reports no combined status for head `6603aa61d031a928701523aff2ee1691600e8f19`.
- [ ] Do not claim the C6 audit is production-ready until the AI audit API path is verified end-to-end.
- [ ] Do not wire payment until the offer/package returned by the audit is authoritative and evidence-backed.

## Build order

### 1. Discovery
- [ ] Define the real-business research contract: business identity, website signals, market/competitor signals, decision-maker signals, source URLs, timestamps, confidence.
- [ ] Reuse/harden existing Ubernie agent orchestration rather than creating a parallel agent framework.
- [ ] Connect real research input to a normalized business profile.

### 2. Evidence / provenance
- [ ] Persist every material finding with source URL, observed signal, timestamp, confidence and originating agent.
- [ ] Make evidence inspectable from the audit result.
- [ ] Reject recommendations that have no supporting evidence where evidence is required.

### 3. Offer / package engine
- [ ] Map evidence + opportunity signals to C6 service/package recommendations.
- [ ] Replace guessed pricing with the approved commercial package catalogue and explicit pricing rules.
- [ ] Return a machine-readable offer: package, price, inclusions, rationale, evidence IDs and next action.

### 4. Checkout / payment bridge
- [ ] Pass only the validated offer to the C6 checkout surface.
- [ ] Use RemotePay as the transaction boundary; no client-supplied amount becomes authoritative.
- [ ] Record payment intent/status against the business/customer and offer IDs.

### 5. Outcome loop
- [ ] Record audit → offer → checkout → payment → activation/conversion events.
- [ ] Feed outcomes back into scoring/recommendation quality.
- [ ] Add self-correction only after the end-to-end revenue event is observable.

## Repository responsibilities

| System | Responsibility |
|---|---|
| C6 Group website | Commercial surface, AI audit UX, package presentation, checkout initiation |
| Ubernie | Business discovery, business intelligence, orchestration, evidence and offer intelligence |
| RemotePay | Payment execution, transaction state and payment webhooks |

## Decision rule

Build the smallest missing component that closes the next measurable revenue transition. Do not expand scope into unrelated repositories or infrastructure until this path works for one real business.
