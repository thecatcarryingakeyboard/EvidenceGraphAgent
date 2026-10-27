# Architecture

The design follows the original structured-query / document-retrieval split. The local implementation and optional external integrations have separate, explicit backends.

## Synchronous Agent

`AgentRunner` performs scope checking, bounded task splitting, deterministic routing, tool execution, evidence collection, generation and citation-ID validation. The default planner splits a compound question into at most four tasks. The runner accepts at most six tool calls, including fallback calls. A primary tool that fails or returns no citations may trigger one document-search fallback. The trace records each decision. This budget limits calls, not wall-clock time.

`CatalogQueryTool` executes real, parameterized SQLite queries against a synthetic catalog. It filters by tenant and optionally product name or low stock. Each invocation owns and closes its database connection.

`graph_search` uses BM25 seeds and two rounds of shared-term expansion. These terms are derived by tokenization; they are not entities extracted by an LLM. The local `global` option is one expansion round, not Microsoft GraphRAG's community map-reduce query.

## Parallel LangGraph runtime

`build_graph` uses `Send` to run the planned tools in parallel. Results use an additive reducer, retain task indices and are sorted before evidence normalization. The summary node runs after fan-in. The caller may inject a checkpointer and use a distinct thread_id for an independent run. The supplied saver is in-memory; it does not survive process termination. State serialization explicitly allows only the four application dataclasses.

The parallel runtime does not yet implement the synchronous runner's fallback policy, and repeated turns on one thread are not implemented as a conversation product. Use a fresh thread_id per query in the current example.

## Evidence

Tool outputs normalize to `ToolResult`; structured rows are serialized as evidence, document hits retain their source text. The aggregation key is `(document_id, chunk_id)`. Final citations are assigned C1, C2, … globally so two tools cannot accidentally reuse an identifier. The answer must contain known citation IDs. This validates identifiers, not the semantic truth of a claim.

The offline provider extracts the first three evidence items. The OpenAI-compatible provider performs model generation only when explicitly configured. No benchmark claim is made from the synthetic regression set.

## External boundaries

`ReadOnlyNeo4jAdapter` rejects conservative write/procedure keywords and performs EXPLAIN before execution. `Neo4jReadClient` uses a read transaction and timeout; the account must also have read-only permissions. The supplied schema is prompt context rather than complete AST validation.

`MicrosoftGraphRAGAdapter` loads a separately built 2.1.0 index and calls its four public query methods with their respective signatures. The adapter converts tabular context into citations. Community-report context does not automatically establish original page-level provenance.

Neither external adapter automatically enforces tenant authorization. Authentication, document ACLs, persistent storage, human approval queues and semantic faithfulness evaluation remain deployment work.
