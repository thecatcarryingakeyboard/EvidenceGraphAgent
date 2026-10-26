# Roadmap

The first release is a compact reference implementation, not a claim that a
small in-memory graph is production-ready. Planned increments are ordered by
enterprise value and research visibility:

1. **Persistence and permissions:** PostgreSQL/pgvector adapter, Neo4j adapter,
   JWT-derived tenant context, document ACLs and a redaction test suite.
2. **Cost-aware GraphRAG:** dynamic community selection, LazyGraphRAG-style
   early exits, reranking and a query budget in the trace.
3. **Document intelligence:** MarkItDown/Docling/MinerU ingestion, page/table/
   image provenance and multimodal chunk types.
4. **Agent runtime:** LangGraph durable checkpoints, MCP registry, tool timeout,
   approval queue and replayable trajectories.
5. **Evaluation:** Ragas/DeepEval integration, claim-level faithfulness,
   temporal and permission benchmarks, nightly model comparison.
6. **Context and memory:** hierarchy-aware summaries inspired by PageIndex and
   OpenViking, with explicit retention and deletion policies.

The roadmap reflects public projects such as Microsoft GraphRAG, LightRAG,
KAG, RAGFlow, PageIndex, LangGraph, OpenViking, MCP servers, Ragas, DeepEval,
Phoenix and Langfuse. It is a design reference, not an endorsement of any
third-party license or hosted service.

For the GraphRAG-specific research track, the next experiments should compare
DRIFT-style global/local routing, dynamic community selection and
LazyGraphRAG-style early exits on the same evidence and cost budget. Claim-level
provenance (Claimify/VeriTrail-inspired) and automated benchmark generation are
the following step after the basic citation contract is stable. See the public
Microsoft Research notes on [DRIFT Search](https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/),
[LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/),
[Claimify](https://www.microsoft.com/en-us/research/blog/claimify-extracting-high-quality-claims-from-language-model-outputs/)
and [VeriTrail](https://www.microsoft.com/en-us/research/blog/veritrail-detecting-hallucination-and-tracing-provenance-in-multi-step-ai-workflows/).
