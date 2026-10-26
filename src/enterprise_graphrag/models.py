"""Stable contracts shared by ingestion, retrieval, generation and API layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SearchMode = Literal["local", "global", "deep"]


@dataclass(frozen=True)
class UserContext:
    tenant_id: str = "demo"
    user_id: str = "anonymous"
    roles: tuple[str, ...] = ("reader",)


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    tenant_id: str = "demo"
    source_uri: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    text: str
    ordinal: int
    tenant_id: str = "demo"
    source_uri: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    kind: str = "concept"
    tenant_id: str = "demo"


@dataclass(frozen=True)
class Edge:
    source_id: str
    target_id: str
    relation: str = "co_occurs"
    weight: float = 1.0
    tenant_id: str = "demo"


@dataclass(frozen=True)
class Citation:
    citation_id: str
    chunk_id: str
    document_id: str
    title: str
    quote: str
    source_uri: str = ""
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalHit:
    chunk: Chunk
    score: float
    matched_terms: tuple[str, ...] = ()
    graph_hops: int = 0
    reason: str = "lexical"


@dataclass(frozen=True)
class QueryRequest:
    query: str
    user: UserContext = field(default_factory=UserContext)
    mode: SearchMode = "local"
    top_k: int = 6
    conversation_id: str | None = None
    stream: bool = False


@dataclass
class TraceEvent:
    name: str
    duration_ms: float
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResponse:
    answer: str
    citations: list[Citation]
    mode: SearchMode
    trace_id: str
    confidence: float
    abstained: bool = False
    trace: list[TraceEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [item.to_dict() for item in self.citations],
            "mode": self.mode,
            "trace_id": self.trace_id,
            "confidence": round(self.confidence, 4),
            "abstained": self.abstained,
            "trace": [asdict(item) for item in self.trace],
        }
