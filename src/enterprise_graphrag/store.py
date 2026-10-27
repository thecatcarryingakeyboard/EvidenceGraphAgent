"""In-memory knowledge graph used by the offline demo and unit tests.

The store deliberately exposes narrow methods.  A PostgreSQL/pgvector,
Neo4j, or Microsoft GraphRAG adapter can implement the same retrieval-facing
contract without changing the agent state machine.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import replace
from hashlib import sha1
from typing import Iterable

from .models import Chunk, Document, Edge, Entity, UserContext

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{1,}|[\u4e00-\u9fff]{2,}")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN_RE.findall(text):
        token = token.lower()
        tokens.append(token)
        # Chinese text often has no whitespace.  Add overlapping bigrams so a
        # question can match a sentence without shipping a heavyweight segmenter.
        if all("\u4e00" <= char <= "\u9fff" for char in token):
            tokens.extend(token[index : index + 2] for index in range(len(token) - 1))
    return tokens


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{sha1(value.encode('utf-8')).hexdigest()[:12]}"


class KnowledgeGraph:
    """Tenant-aware graph + chunk index with deterministic ingestion."""

    def __init__(self) -> None:
        self.documents: dict[str, Document] = {}
        self.chunks: dict[str, Chunk] = {}
        self.entities: dict[str, Entity] = {}
        self.edges: list[Edge] = []
        self.chunk_entities: dict[str, set[str]] = defaultdict(set)
        self.entity_chunks: dict[str, set[str]] = defaultdict(set)

    def ingest(self, document: Document, chunk_size: int = 900, overlap: int = 120) -> list[Chunk]:
        if overlap < 0 or chunk_size <= overlap:
            raise ValueError("chunk_size must be greater than overlap")
        existing = self.documents.get(document.id)
        if existing and existing.tenant_id != document.tenant_id:
            raise ValueError("document id belongs to another tenant")
        self.documents[document.id] = document
        chunks: list[Chunk] = []
        start = 0
        ordinal = 0
        text = document.text.strip()
        while start < len(text):
            end = min(len(text), start + chunk_size)
            if end < len(text):
                boundary = text.rfind("\n", start, end)
                if boundary > start + chunk_size // 2:
                    end = boundary
            content = text[start:end].strip()
            if content:
                chunk = Chunk(
                    id=stable_id("chunk", f"{document.id}:{ordinal}:{content}"),
                    document_id=document.id,
                    text=content,
                    ordinal=ordinal,
                    tenant_id=document.tenant_id,
                    source_uri=document.source_uri,
                    metadata={**document.metadata, "char_start": start, "char_end": end},
                )
                self.chunks[chunk.id] = chunk
                chunks.append(chunk)
                self._index_entities(chunk)
                ordinal += 1
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
        return chunks

    def _index_entities(self, chunk: Chunk) -> None:
        tokens = list(dict.fromkeys(tokenize(chunk.text)))
        # Short function words create noisy edges; keep meaningful terms.
        terms = [token for token in tokens if len(token) >= 3 or any("\u4e00" <= c <= "\u9fff" for c in token)]
        for term in terms[:40]:
            entity_id = stable_id("entity", f"{chunk.tenant_id}:{term}")
            self.entities.setdefault(entity_id, Entity(entity_id, term, tenant_id=chunk.tenant_id))
            self.chunk_entities[chunk.id].add(entity_id)
            self.entity_chunks[entity_id].add(chunk.id)
        entity_ids = sorted(self.chunk_entities[chunk.id])
        for left, right in zip(entity_ids, entity_ids[1:]):
            self.edges.append(Edge(left, right, tenant_id=chunk.tenant_id))
            self.edges.append(Edge(right, left, tenant_id=chunk.tenant_id))

    def visible_chunks(self, user: UserContext) -> Iterable[Chunk]:
        for chunk in self.chunks.values():
            if chunk.tenant_id == user.tenant_id:
                yield chunk

    def expand(self, seed_chunk_ids: set[str], user: UserContext, hops: int = 1) -> set[str]:
        visible = {chunk.id for chunk in self.visible_chunks(user)}
        current = set(seed_chunk_ids) & visible
        expanded = set(current)
        for _ in range(max(0, hops)):
            entities = {entity for chunk_id in current for entity in self.chunk_entities.get(chunk_id, set())}
            current = {
                chunk_id
                for entity in entities
                for chunk_id in self.entity_chunks.get(entity, set())
                if chunk_id in visible
            }
            expanded.update(current)
        return expanded

    def replace_document(self, document: Document, chunk_size: int = 900, overlap: int = 120) -> list[Chunk]:
        old = [chunk_id for chunk_id, chunk in self.chunks.items() if chunk.document_id == document.id]
        for chunk_id in old:
            self.chunks.pop(chunk_id, None)
            for entity_id in self.chunk_entities.pop(chunk_id, set()):
                self.entity_chunks[entity_id].discard(chunk_id)
        self.documents.pop(document.id, None)
        return self.ingest(replace(document), chunk_size=chunk_size, overlap=overlap)
