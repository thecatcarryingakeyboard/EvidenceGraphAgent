# Evaluation protocol

The included regression set is deliberately small and synthetic. It proves
that the repository can run in CI; it is not a benchmark claim. A real team
should version a tenant-safe dataset with:

- direct fact questions for retrieval recall and citation precision;
- multi-hop questions requiring entity or community expansion;
- temporal questions where stale documents must be rejected;
- permission questions where another tenant's evidence must never appear;
- unanswerable questions for abstention and calibrated confidence;
- tool questions for allowlist, argument validation and human approval.

Track at least answer-term recall, citation coverage, groundedness/faithfulness,
p95 latency, token cost and abstention rate. Run the cheap deterministic set on
every pull request and the model-graded suite nightly. Ragas, DeepEval or a
custom evaluator can consume the `QueryResponse` JSON without changing the
pipeline.
