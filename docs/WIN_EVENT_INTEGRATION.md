# C6 Win Event Integration

This product emits evidence-first Win Events using the C6 contract:

`OBJECTIVE → MINIMUM WINNABLE ACTION → EVIDENCE → WIN CONFIRMED → NEXT WIN`.

Configure:
- `C6_WIN_ENGINE_URL`: Command Centre `/api/wins` endpoint.
- `C6_WIN_ENGINE_TOKEN`: optional shared ingestion token.
- Product operations remain fail-open if the Command Centre is unavailable; events are retained locally where supported.

A confirmed event must include non-empty evidence. No evidence means no confirmed win.
