"""Simple local ingestion; production adapters can use MarkItDown/Docling/MinerU."""

from __future__ import annotations

from pathlib import Path

from .models import Document
from .store import KnowledgeGraph, stable_id


SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt"}


def ingest_path(graph: KnowledgeGraph, path: str | Path, tenant_id: str = "demo") -> list[str]:
    root = Path(path)
    files = [root] if root.is_file() else sorted(item for item in root.rglob("*") if item.suffix.lower() in SUPPORTED_SUFFIXES)
    ids: list[str] = []
    for file in files:
        text = file.read_text(encoding="utf-8")
        document_id = stable_id("doc", f"{tenant_id}:{file.resolve()}")
        graph.ingest(Document(document_id, file.stem, text, tenant_id, str(file)))
        ids.append(document_id)
    return ids
