# Deployment notes

The standard-library server is for local demos only. For a service deployment:

1. install `.[api,llm]` and run the FastAPI factory with a process manager;
2. inject `LLM_API_KEY` from a secret store, never commit it to `.env`;
3. replace the in-memory store with a tenant-aware persistent adapter;
4. add authentication before `/v1/query` and derive `tenant_id` from the token;
5. configure an explicit CORS allowlist and request/body limits;
6. export trace spans to OpenTelemetry/Phoenix and redact prompts containing PII;
7. put high-risk tools behind an approval queue and record every tool result.

`docker-compose.yml` documents optional Postgres/pgvector and Neo4j profiles,
but intentionally does not start them for the offline demo.
