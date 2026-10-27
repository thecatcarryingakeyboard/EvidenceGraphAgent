"""Small, read-only Neo4j boundary used by the reference example.

The original learning project generated Cypher with an LLM and then executed
it through ``langchain_neo4j``.  This adapter keeps that idea explicit without
vendoring LangChain or requiring Neo4j for the offline demo.  Any object with
``query`` and optional ``get_schema``/``structured_schema`` methods can be
used in tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol


class GraphQueryClient(Protocol):
    def query(self, query: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]: ...


class CypherRejected(ValueError):
    """Raised when generated Cypher is not safe for a read-only tool."""


_WRITE_OPERATIONS = re.compile(
    r"\b(?:CREATE|INSERT|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD|FOREACH|GRANT|REVOKE|ALTER|CALL)\b",
    re.IGNORECASE,
)
_ADMIN_OPERATIONS = re.compile(r"\bCALL\s+(?:DBMS|DB|APOC)\b", re.IGNORECASE)
_ALLOWED_START = re.compile(r"^\s*(?:MATCH|OPTIONAL\s+MATCH|WITH|UNWIND|RETURN|EXPLAIN)\b", re.IGNORECASE)


def validate_read_only_cypher(statement: str) -> str:
    """Validate one read-only Cypher statement and return normalized text.

    This is deliberately a *policy gate*, not a complete Cypher parser.  A
    database read-only account, query timeout and server-side limits remain
    necessary in a real deployment.
    """

    query = " ".join(statement.strip().split())
    if not query:
        raise CypherRejected("Cypher statement is empty")
    if ";" in query:
        raise CypherRejected("multiple Cypher statements are not allowed")
    if _WRITE_OPERATIONS.search(query) or _ADMIN_OPERATIONS.search(query):
        raise CypherRejected("write or administrative Cypher operation is not allowed")
    if not _ALLOWED_START.match(query):
        raise CypherRejected("statement must start with MATCH, WITH, UNWIND, RETURN or EXPLAIN")
    return query


@dataclass
class ReadOnlyNeo4jAdapter:
    """Execute validated read-only queries against a graph-like client."""

    client: GraphQueryClient
    default_limit: int = 50
    explain: Callable[[str], Any] | None = None

    def schema(self) -> str:
        value = getattr(self.client, "get_schema", "")
        if callable(value):
            value = value()
        if value:
            return str(value)
        return str(getattr(self.client, "structured_schema", ""))

    def run(self, statement: str, parameters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        query = self.validate(statement, parameters)
        if not re.search(r"\bLIMIT\s+\d+\b", query, re.IGNORECASE):
            query = f"{query} LIMIT {max(1, int(self.default_limit))}"
        return list(self.client.query(query, params=parameters or {}))

    def validate(self, statement: str, parameters: Mapping[str, Any] | None = None) -> str:
        query = validate_read_only_cypher(statement)
        if self.explain is not None:
            self.explain(query)
        else:
            self.client.query(f"EXPLAIN {query}", params=parameters or {})
        return query


@dataclass
class Text2CypherExecutor:
    """Generate, validate and execute Cypher with bounded retries.

    ``generator`` receives ``(question, schema, previous_errors)`` and returns
    a statement.  Keeping the generator as a callable makes the class usable
    with an LLM chain, a deterministic fixture, or a human-written example.
    """

    adapter: ReadOnlyNeo4jAdapter
    generator: Callable[[str, str, list[str]], str]
    max_attempts: int = 3

    def run(self, question: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]:
        errors: list[str] = []
        for attempt in range(1, max(1, self.max_attempts) + 1):
            try:
                statement = self.generator(question, self.adapter.schema(), errors)
                records = self.adapter.run(statement, parameters)
                return {"statement": statement, "records": records, "errors": [],
                        "retry_history": errors, "attempts": attempt}
            except Exception as exc:  # retry with the error as model feedback
                errors.append(f"attempt {attempt}: {type(exc).__name__}")
        return {"statement": "", "records": [], "errors": errors, "attempts": max(1, self.max_attempts)}


class Neo4jReadClient:
    """Native driver client: read transaction, explicit schema and query timeout."""

    def __init__(self, driver: Any, schema: str, database: str = 'neo4j', timeout: float = 10) -> None:
        self.driver, self.get_schema = driver, schema
        self.database, self.timeout = database, timeout

    def query(self, query: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        from neo4j import Query

        with self.driver.session(database=self.database, default_access_mode='READ') as session:
            return session.execute_read(
                lambda tx: [dict(row) for row in tx.run(Query(query, timeout=self.timeout), dict(params or {}))]
            )
