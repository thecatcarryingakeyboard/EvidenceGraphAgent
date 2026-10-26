"""Adapter boundary for Microsoft GraphRAG indexes.

The upstream project changes its query API between releases, so this module
keeps imports lazy and converts its context callback into stable citations.
It is intentionally not a vendored copy of GraphRAG.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from ..models import Citation


@dataclass
class MicrosoftGraphRAGAdapter:
    """Call a locally installed GraphRAG query API and normalize its output."""

    config: Any
    entities: Any
    communities: Any
    community_reports: Any
    text_units: Any | None = None
    relationships: Any | None = None
    community_level: int = 2

    def query(self, question: str, mode: str = "local") -> tuple[str, list[Citation]]:
        try:
            from graphrag.api import query as graphrag_query  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install microsoft-graphrag separately to use this adapter") from exc
        if mode == "global":
            coroutine = graphrag_query.global_search(
                config=self.config,
                entities=self.entities,
                communities=self.communities,
                community_reports=self.community_reports,
                community_level=self.community_level,
                dynamic_community_selection=True,
                response_type="Multiple Paragraphs",
                query=question,
            )
        elif mode == "local":
            if self.text_units is None or self.relationships is None:
                raise ValueError("text_units and relationships are required for GraphRAG local search")
            coroutine = graphrag_query.local_search(
                config=self.config,
                entities=self.entities,
                communities=self.communities,
                community_reports=self.community_reports,
                text_units=self.text_units,
                relationships=self.relationships,
                covariates=None,
                community_level=self.community_level,
                response_type="Multiple Paragraphs",
                query=question,
            )
        else:
            raise ValueError("GraphRAG adapter supports local and global; use pipeline deep routing around it")
        answer, context = asyncio.run(coroutine)
        return str(answer), self._citations(context)

    @staticmethod
    def _citations(context: Any) -> list[Citation]:
        """Normalize common GraphRAG context shapes without assuming pandas."""
        rows: list[dict[str, Any]] = []
        if isinstance(context, dict):
            for value in context.values():
                if isinstance(value, list):
                    rows.extend(item for item in value if isinstance(item, dict))
        elif isinstance(context, list):
            rows = [item for item in context if isinstance(item, dict)]
        citations: list[Citation] = []
        for index, row in enumerate(rows[:20], 1):
            text = str(row.get("text") or row.get("description") or row.get("content") or "")
            if not text:
                continue
            citations.append(Citation(f"GR{index}", str(row.get("id", index)), str(row.get("document_id", "graphrag")), str(row.get("title", "GraphRAG context")), text))
        return citations
