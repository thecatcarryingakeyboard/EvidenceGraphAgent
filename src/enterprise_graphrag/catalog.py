"""Synthetic catalog with actual parameterized SQL queries for offline runs.

The local backend is SQLite; it does not pretend to execute Neo4j Cypher.
The domain and query split follow the original structured-data/document tools.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .agentic import AgentTask, ToolResult
from .models import Citation, UserContext

PRODUCTS = (
    ("demo", "speaker-mini", "智能音箱 Mini", 299, 42, "星河供应商"),
    ("demo", "speaker-pro", "智能音箱 Pro", 599, 8, "星河供应商"),
)


@dataclass
class CatalogQueryTool:
    name: str = "catalog_query"

    def run(self, task: AgentTask, user: UserContext) -> ToolResult:
        # A connection per invocation also supports concurrent HTTP requests.
        with closing(sqlite3.connect(":memory:")) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(
                "CREATE TABLE products (tenant TEXT, id TEXT, name TEXT, price INTEGER, stock INTEGER, supplier TEXT)"
            )
            conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)", PRODUCTS)
            query = "SELECT id, name, price, stock, supplier FROM products WHERE tenant = ?"
            parameters: list[object] = [user.tenant_id]
            lowered = task.question.lower()
            if "mini" in lowered or "pro" in lowered:
                query += " AND lower(name) LIKE ?"
                parameters.append("%mini%" if "mini" in lowered else "%pro%")
            low_stock = any(term in lowered for term in ("补货", "低库存", "库存不足"))
            if low_stock:
                query += " AND stock < ?"
                parameters.append(10)
            query += " ORDER BY id LIMIT 20"
            rows = tuple(dict(row) for row in conn.execute(query, parameters))
        citations = tuple(
            Citation(
                f"CAT{i}",
                f"catalog:{row['id']}",
                "synthetic-catalog",
                "商品目录（合成数据）",
                json.dumps(row, ensure_ascii=False),
                f"demo://catalog/{row['id']}",
            )
            for i, row in enumerate(rows, 1)
        )
        return ToolResult(
            self.name,
            task.question,
            rows,
            citations,
            metadata={
                "backend": "sqlite",
                "query": query,
                "parameterized": True,
                "low_stock_threshold": 10 if low_stock else None,
            },
        )
