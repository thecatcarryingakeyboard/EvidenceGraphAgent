"""Optional FastAPI application for production-shaped deployments."""

from __future__ import annotations

from typing import Any

from .demo_data import demo_graph
from .models import QueryRequest, UserContext
from .pipeline import QueryEngine


def create_app(engine: QueryEngine | None = None) -> Any:
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install enterprise-graphrag-agent[api] to run the FastAPI server") from exc

    app = FastAPI(title="AssistGen Graph Agent", version="0.2.0")
    query_engine = engine or QueryEngine(demo_graph())

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/query")
    def query(payload: dict[str, Any]) -> dict[str, Any]:
        question = str(payload.get("query", "")).strip()
        if not question:
            raise HTTPException(status_code=422, detail="query is required")
        user = UserContext(
            tenant_id=str(payload.get("tenant_id", "demo")),
            user_id=str(payload.get("user_id", "anonymous")),
            roles=tuple(payload.get("roles", ["reader"])),
        )
        request = QueryRequest(
            query=question,
            user=user,
            mode=payload.get("mode", "local"),
            top_k=int(payload.get("top_k", 6)),
        )
        return query_engine.answer(request).to_dict()

    @app.get("/v1/evidence/{chunk_id}")
    def evidence(chunk_id: str) -> dict[str, Any]:
        chunk = query_engine.graph.chunks.get(chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="evidence not found")
        return {"chunk_id": chunk.id, "document_id": chunk.document_id, "text": chunk.text, "metadata": chunk.metadata}

    return app
