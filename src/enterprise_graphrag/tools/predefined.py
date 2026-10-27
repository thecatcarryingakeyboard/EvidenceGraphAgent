"""Parameterised, auditable Cypher queries for common questions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..adapters.neo4j import ReadOnlyNeo4jAdapter
from ..agentic import AgentTask, ToolResult
from ..models import UserContext


@dataclass
class PredefinedCypherTool:
    adapter: ReadOnlyNeo4jAdapter
    queries: Mapping[str, str]
    name: str = "predefined_cypher"

    def run_named(self, query_name: str, parameters: Mapping[str, Any] | None = None) -> ToolResult:
        statement = self.queries.get(query_name)
        if not statement:
            return ToolResult(self.name, query_name, errors=(f"unknown query: {query_name}",))
        try:
            checked = self.adapter.validate(statement)
            rows = self.adapter.run(checked, parameters)
            return ToolResult(self.name, query_name, records=tuple(rows), metadata={"query_name": query_name})
        except Exception as exc:
            return ToolResult(self.name, query_name, errors=(f"{type(exc).__name__}: {exc}",))

    def run(self, task: AgentTask, user: UserContext) -> ToolResult:
        del user
        # The deterministic demo treats the task as the registered query name.
        # An LLM tool selector can call run_named with structured arguments.
        return self.run_named(task.question)
