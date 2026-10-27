# Changelog

## 0.3.0 - 2026-10-27

- Replaced misleading offline tool aliases with an actual parameterized SQLite catalog and explicitly named graph_search backend.
- Added BM25, bounded synchronous fallback, unified citation IDs and unknown-reference rejection.
- Added LangGraph Send fan-out and injectable checkpoints, with an explicit state serialization allowlist.
- Corrected Microsoft GraphRAG 2.1.0 DRIFT/basic query arguments and tabular context conversion.
- Added real Neo4j read transactions, EXPLAIN, query timeout and structured-row evidence.
- Added an Agent API and evidence cards to the local demo page.
- Expanded regression checks and publication scanning across Git history; removed local absolute paths from document source URIs.

## 0.2.0 - 2026-10-26

- Added explicit Agent stages, optional graph tools and workflow adapters.

## 0.1.0 - 2026-10-26

- Added a synthetic offline knowledge-query pipeline, citations, traces and evaluation.
