# Evaluation

`python -m enterprise_graphrag.cli eval --json` runs three synthetic document cases and reports answer-term recall, citation rate and abstention rate. These are inexpensive regressions, not semantic answer accuracy or a comparison with other RAG systems. Cases honor tenant_id when constructing the query.

The unit suite also covers actual catalog filtering, failed-tool fallback, citation collisions and fabricated IDs, tenant evidence access, source path redaction, Cypher rejection/retry and GraphRAG's four API signatures. With optional FastAPI and LangGraph dependencies, the same suite exercises HTTP requests and parallel tool fan-in/checkpoint reads.

Real Neo4j, GraphRAG index building and hosted model calls are not tested end to end. Future evaluation needs authorized documents, expected source IDs, unanswerable cases, temporal validity, answer faithfulness, latency and token cost. A model judge should be reported separately from deterministic checks.
