"""Stateful query pipeline: route -> retrieve -> cite -> answer -> audit."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import Settings
from .models import Citation, QueryRequest, QueryResponse
from .providers import AnswerProvider, provider_from_settings
from .retrieval import HybridRetriever
from .store import KnowledgeGraph
from .trace import Trace

COMPLEX_MARKERS = re.compile(r"(为什么|原因|影响|比较|风险|趋势|how|why|compare|impact|risk)", re.I)


@dataclass
class QueryEngine:
    graph: KnowledgeGraph
    settings: Settings = field(default_factory=Settings.from_env)
    provider: AnswerProvider | None = None

    def __post_init__(self) -> None:
        self.retriever = HybridRetriever(self.graph)
        if self.provider is None:
            self.provider = provider_from_settings(self.settings)

    def answer(self, request: QueryRequest) -> QueryResponse:
        if not request.query.strip():
            raise ValueError("query must not be empty")
        trace = Trace(enabled=self.settings.enable_trace)
        mode = request.mode
        if mode == "local" and (len(request.query) > 80 or COMPLEX_MARKERS.search(request.query)):
            mode = "deep"
        with trace.span("route", selected_mode=mode):
            pass
        with trace.span("retrieve", mode=mode, top_k=request.top_k):
            hits = self.retriever.search(
                request.query,
                request.user,
                mode,
                min(request.top_k, self.settings.max_retrieval_k),
            )
        citations = [
            Citation(
                citation_id=f"C{i}",
                chunk_id=hit.chunk.id,
                document_id=hit.chunk.document_id,
                title=self.graph.documents[hit.chunk.document_id].title,
                quote=hit.chunk.text[:500],
                source_uri=hit.chunk.source_uri,
                score=hit.score,
            )
            for i, hit in enumerate(hits, 1)
        ]
        context = citations[: self.settings.max_retrieval_k]
        with trace.span("generate", provider=getattr(self.provider, "name", "unknown"), citations=len(context)):
            answer = (
                self.provider.answer(request.query, context)
                if context else "当前知识库没有足够证据，暂不回答。"
            )
        confidence = min(0.99, max(0.0, (context[0].score / 4.0) if context else 0.0))
        abstained = not context
        with trace.span("audit", abstained=abstained, tenant_id=request.user.tenant_id):
            pass
        return QueryResponse(
            answer=answer,
            citations=context,
            mode=mode,  # type: ignore[arg-type]
            trace_id=trace.trace_id,
            confidence=confidence,
            abstained=abstained,
            trace=trace.events,
        )
