"""Enterprise GraphRAG Agent reference implementation.

The package intentionally keeps the core pipeline dependency-light.  External
LLM, vector, graph and observability providers are adapters, so the demo can be
run offline while the same contracts can be wired to production services.
"""

from .config import Settings
from .models import QueryRequest, QueryResponse
from .pipeline import QueryEngine

__all__ = ["QueryEngine", "QueryRequest", "QueryResponse", "Settings"]
