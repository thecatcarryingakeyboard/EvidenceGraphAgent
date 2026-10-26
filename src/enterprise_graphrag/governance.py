"""Allowlist and approval primitives for enterprise tools/MCP servers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .models import UserContext


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    risk: str = "low"  # low, medium, high
    requires_approval: bool = False


class ToolRegistry:
    """A deliberately small policy boundary around callable tools."""

    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolSpec, Callable[..., Any]]] = {}

    def register(self, spec: ToolSpec, handler: Callable[..., Any]) -> None:
        if spec.name in self._tools:
            raise ValueError(f"tool already registered: {spec.name}")
        if spec.risk not in {"low", "medium", "high"}:
            raise ValueError("risk must be low, medium or high")
        self._tools[spec.name] = (spec, handler)

    def invoke(
        self,
        name: str,
        user: UserContext,
        arguments: dict[str, Any],
        *,
        approved: bool = False,
    ) -> Any:
        if name not in self._tools:
            raise PermissionError(f"tool is not allowlisted: {name}")
        spec, handler = self._tools[name]
        if spec.requires_approval and not approved:
            raise PermissionError(f"human approval required for tool: {name}")
        # The tenant context is explicit and can be logged by the handler.
        return handler(user=user, arguments=arguments)

    def manifest(self) -> list[dict[str, Any]]:
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "risk": spec.risk,
                "requires_approval": spec.requires_approval,
            }
            for spec, _ in self._tools.values()
        ]
