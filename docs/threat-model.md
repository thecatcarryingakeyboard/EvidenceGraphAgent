# Threat model

The reference implementation treats the following as boundaries that must be
kept when replacing the demo components:

| Threat | Required control |
| --- | --- |
| Cross-tenant retrieval | derive tenant identity from auth; filter before ranking; test with adversarial IDs |
| Prompt injection in documents | keep retrieved text as evidence; separate instructions from data; validate tool arguments |
| Unsafe side effects | allowlist tools, set timeouts/budgets, require approval for high-risk actions |
| Data leakage in traces | redact secrets/PII; restrict trace access by tenant; configure retention |
| Unsupported answer | return `abstained=true`; show evidence IDs; avoid confidence as a security decision |
| Stale or revoked content | version documents, enforce effective dates and deletion propagation |

The demo has no authentication and uses synthetic data. It is a development
fixture, not a production security boundary.
