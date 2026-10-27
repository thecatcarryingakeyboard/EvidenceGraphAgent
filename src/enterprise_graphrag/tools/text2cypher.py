"""Agent-tool wrapper around the schema-aware Text2Cypher executor."""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters.neo4j import Text2CypherExecutor
from ..agentic import AgentTask, ToolResult
from ..models import UserContext


@dataclass
class Text2CypherTool:
    executor: Text2CypherExecutor
    name: str = "text2cypher"

    def run(self, task: AgentTask, user: UserContext) -> ToolResult:
        del user
        result = self.executor.run(task.question)
        errors = tuple(result["errors"])
        return ToolResult(
            tool=self.name,
            task=task.question,
            records=tuple(result["records"]),
            errors=errors,
            metadata={"statement": result["statement"], "attempts": result["attempts"]},
        )
