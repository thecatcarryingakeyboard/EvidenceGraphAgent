"""Agent-tool wrapper for the optional Microsoft GraphRAG adapter."""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.graphrag import MicrosoftGraphRAGAdapter
from ..agentic import AgentTask, ToolResult
from ..models import UserContext


@dataclass
class GraphRAGTool:
    adapter: MicrosoftGraphRAGAdapter
    mode: str | None = None
    name: str = "graphrag"

    def run(self, task: AgentTask, user: UserContext) -> ToolResult:
        del user
        try:
            answer, citations = self.adapter.query(task.question, self.mode)
            return ToolResult(
                self.name,
                task.question,
                records=tuple({"answer": answer, "citation_id": item.citation_id} for item in citations),
                citations=tuple(citations),
                metadata={"mode": self.mode or self.adapter.query_type},
            )
        except Exception as exc:
            return ToolResult(self.name, task.question, errors=(type(exc).__name__,))
