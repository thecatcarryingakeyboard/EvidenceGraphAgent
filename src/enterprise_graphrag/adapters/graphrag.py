"""Optional adapter for a separately installed Microsoft GraphRAG index.

The upstream query API changes between releases, so this module keeps imports
lazy and normalizes local/global/DRIFT/basic context into our citation contract.
It intentionally does not vendor GraphRAG source or data.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any

from ..models import Citation


@dataclass
class MicrosoftGraphRAGAdapter:
    config: Any
    entities: Any
    communities: Any
    community_reports: Any
    text_units: Any | None = None
    relationships: Any | None = None
    covariates: Any | None = None
    query_type: str = "local"
    community_level: int = 2
    dynamic_community_selection: bool = False

    async def query_async(self, question: str, mode: str | None = None) -> tuple[str, list[Citation]]:
        """Run one GraphRAG query without blocking an existing event loop."""

        try:
            from graphrag import api as graphrag_api  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install the optional 'graphrag' extra separately") from exc

        selected = (mode or self.query_type).lower()
        if selected not in {"local", "global", "drift", "basic"}:
            raise ValueError("GraphRAG mode must be local, global, drift or basic")
        kwargs: dict[str, Any] = {
            "config": self.config,
            "query": question,
            "response_type": "Multiple Paragraphs",
        }
        if selected in {"local", "drift"}:
            if self.text_units is None or self.relationships is None:
                raise ValueError("text_units and relationships are required for local/DRIFT search")
            kwargs.update(
                entities=self.entities,
                communities=self.communities,
                community_reports=self.community_reports,
                text_units=self.text_units,
                relationships=self.relationships,
                covariates=self.covariates,
                community_level=self.community_level,
            )
        elif selected == "global":
            kwargs.update(
                entities=self.entities,
                communities=self.communities,
                community_reports=self.community_reports,
                community_level=self.community_level,
                dynamic_community_selection=self.dynamic_community_selection,
            )
        elif self.text_units is None:
            raise ValueError("text_units is required for basic search")
        else:
            kwargs["text_units"] = self.text_units

        function = getattr(graphrag_api, f"{selected}_search", None)
        if function is None:
            raise RuntimeError(f"installed GraphRAG version does not expose {selected}_search")
        result = function(**kwargs)
        answer, context = await result if inspect.isawaitable(result) else result
        return str(answer), self._citations(context)

    def query(self, question: str, mode: str | None = None) -> tuple[str, list[Citation]]:
        """Synchronous convenience wrapper for scripts and the CLI."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.query_async(question, mode))
        raise RuntimeError("query() cannot run inside an active event loop; use await query_async()")

    @staticmethod
    def _citations(context: Any) -> list[Citation]:
        if hasattr(context, "to_dict"):
            try:
                context = context.to_dict("records")
            except TypeError:
                context = context.to_dict()
        rows: list[dict[str, Any]] = []
        if isinstance(context, dict):
            for value in context.values():
                if isinstance(value, list):
                    rows.extend(item for item in value if isinstance(item, dict))
                elif isinstance(value, dict):
                    rows.append(value)
        elif isinstance(context, list):
            rows = [item for item in context if isinstance(item, dict)]
        citations: list[Citation] = []
        for index, row in enumerate(rows[:20], 1):
            text = str(row.get("text") or row.get("description") or row.get("content") or "")
            if not text:
                continue
            citations.append(
                Citation(
                    f"GR{index}",
                    str(row.get("id", index)),
                    str(row.get("document_id", "graphrag")),
                    str(row.get("title", "GraphRAG context")),
                    text[:1000],
                    str(row.get("source_uri", "")),
                )
            )
        return citations
