# Roadmap

## Implemented

- Parameterized synthetic catalog queries and tenant-local BM25/co-occurrence retrieval.
- Synchronous tool budget/fallback and globally unique evidence IDs.
- Optional LangGraph Send fan-out and injectable checkpoint saver.
- GraphRAG 2.1.0 query adapter and Neo4j read-transaction boundary.
- Local Agent API, evidence cards, regression tests and Git-history publication scan.

## Next experiments

1. Add vector retrieval and reranking; compare recall and cost against BM25 on an authorized corpus.
2. Introduce incremental indexing with update/delete propagation.
3. Implement authentication-derived authorization and document ACLs before retrieval.
4. Add persistent checkpoints and human approval before any future write tool.
5. Evaluate semantic faithfulness and source precision, including no-answer and stale-document cases.
6. Compare upstream local/global/DRIFT query cost on the same versioned index.

Design sources are listed in design-evolution.md. Features in this section are planned work, not current capabilities.
