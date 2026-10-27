"""A small, dependency-free agent workflow that mirrors the reference project.

The original learning project has a useful shape: guardrails -> planner ->
tool selection -> graph/document tools -> summarize -> final answer.  This
module keeps that shape as plain Python so that it can be read and tested
without installing LangGraph, Neo4j, or a hosted model.  The optional
``workflows.langgraph`` module exposes the same stages as a LangGraph graph.

The classes here are intentionally boring boundaries.  A production project
can replace :class:`SimplePlanner`, :class:`RuleToolRouter`, or an individual
tool with an LLM-backed implementation without changing the response format.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Callable, Iterable, Protocol

from .models import Citation, QueryRequest, UserContext
from .providers import AnswerProvider, provider_from_settings
from .retrieval import HybridRetriever
from .store import KnowledgeGraph


@dataclass(frozen=True)
class AgentTask:
    """One independently executable sub-question."""

    question: str
    parent: str = ""


@dataclass(frozen=True)
class ToolResult:
    """Normalized output from every agent tool.

    ``records`` is deliberately JSON-shaped.  It can contain Neo4j rows,
    GraphRAG context, or a small diagnostic object.  ``citations`` is the
    only field consumed by the answer provider, which prevents a tool from
    silently adding uncited prose to the final response.
    """

    tool: str
    task: str
    records: tuple[dict[str, Any], ...] = ()
    citations: tuple[Citation, ...] = ()
    errors: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class AgentState:
    """Serializable state useful for traces, replay, and LangGraph adapters."""

    question: str
    user: UserContext
    tasks: list[AgentTask] = field(default_factory=list)
    selected_tools: list[str] = field(default_factory=list)
    results: list[ToolResult] = field(default_factory=list)
    answer: str = ""
    validation_errors: list[str] = field(default_factory=list)
    abstained: bool = False
    citations: list[Citation] = field(default_factory=list)
    blocked: bool = False
    steps: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["user"]["roles"] = list(self.user.roles)
        return payload


class AgentTool(Protocol):
    name: str

    def run(self, task: AgentTask, user: UserContext) -> ToolResult: ...


class Guardrail(Protocol):
    def check(self, question: str, user: UserContext) -> tuple[bool, str]: ...


@dataclass(frozen=True)
class ScopeGuardrail:
    """Deterministic scope check used by the offline example.

    Set ``terms`` to a small domain vocabulary to reject clearly out-of-scope
    questions.  An empty vocabulary leaves scope decisions to the model-backed
    guardrail used by an application.
    """

    terms: tuple[str, ...] = ()
    message: str = "问题不在当前知识库的服务范围内。"

    def check(self, question: str, user: UserContext) -> tuple[bool, str]:
        del user
        question = question.strip()
        if not question:
            return False, "问题不能为空。"
        if self.terms and not any(term.lower() in question.lower() for term in self.terms):
            return False, self.message
        return True, ""


class SimplePlanner:
    """Small planner for demos; replace it with structured LLM output later."""

    _SEPARATORS = re.compile(r"(?:并且|并|以及|同时|另外|然后|\band\b|\balso\b)", re.I)

    def plan(self, question: str) -> list[AgentTask]:
        parts = [part.strip(" ，,。；;") for part in self._SEPARATORS.split(question)]
        parts = [part for part in parts if part]
        # Avoid turning a long natural-language question into an unbounded
        # fan-out.  The LLM planner in a real deployment should enforce a
        # similar budget.
        return [AgentTask(part, question) for part in parts[:4]] or [AgentTask(question, question)]


class RuleToolRouter:
    """Conservative tool routing that is deterministic and easy to inspect."""

    def choose(self, task: AgentTask, available: Iterable[str]) -> str:
        names = set(available)
        text = task.question.lower()
        structured_terms = (
            "统计",
            "数量",
            "列出",
            "排行",
            "库存",
            "补货",
            "价格",
            "供应商",
            "订单",
            "商品",
            "stock",
            "price",
        )
        if any(word in text for word in structured_terms):
            for name in ("catalog_query", "predefined_cypher"):
                if name in names:
                    return name
        if "text2cypher" in names and any(word in text for word in ("节点", "关系", "图谱", "neo4j", "cypher")):
            return "text2cypher"
        semantic_terms = ("趋势", "概括", "总结", "比较", "售后", "故障", "保修", "规则", "全局", "影响")
        if any(word in text for word in semantic_terms):
            for name in ("graphrag", "graph_search"):
                if name in names:
                    return name
        if "document_search" in names:
            return "document_search"
        return sorted(names)[0] if names else ""


@dataclass
class DocumentSearchTool:
    """Adapter from the existing hybrid retriever to the agent tool contract."""

    graph: KnowledgeGraph
    top_k: int = 6
    mode: str = "local"
    name: str = "document_search"

    def run(self, task: AgentTask, user: UserContext) -> ToolResult:
        hits = HybridRetriever(self.graph).search(task.question, user, self.mode, self.top_k)
        citations = tuple(
            Citation(
                citation_id=f"{self.name[:2].upper()}{index}",
                chunk_id=hit.chunk.id,
                document_id=hit.chunk.document_id,
                title=self.graph.documents[hit.chunk.document_id].title,
                quote=hit.chunk.text[:500],
                source_uri=hit.chunk.source_uri,
                score=hit.score,
            )
            for index, hit in enumerate(hits, 1)
        )
        return ToolResult(
            tool=self.name,
            task=task.question,
            records=tuple({"chunk_id": citation.chunk_id, "score": citation.score} for citation in citations),
            citations=citations,
            metadata={"mode": self.mode, "hits": len(citations)},
        )


@dataclass
class CallableTool:
    """Wrap a user-supplied callable without coupling the core to a framework."""

    name: str
    handler: Callable[[str, UserContext], ToolResult]

    def run(self, task: AgentTask, user: UserContext) -> ToolResult:
        try:
            result = self.handler(task.question, user)
            if not isinstance(result, ToolResult):
                raise TypeError("tool handler must return ToolResult")
            return result
        except Exception as exc:  # tools should fail closed and remain traceable
            return ToolResult(self.name, task.question, errors=(type(exc).__name__,))


class AgentRunner:
    """Run guardrails, planning, routing, tools, and grounded generation."""

    def __init__(
        self,
        tools: Iterable[AgentTool],
        provider: AnswerProvider | None = None,
        guardrail: Guardrail | None = None,
        planner: SimplePlanner | None = None,
        router: RuleToolRouter | None = None,
        max_tool_calls: int = 6,
    ) -> None:
        if max_tool_calls < 1:
            raise ValueError("max_tool_calls must be positive")
        self.max_tool_calls = max_tool_calls
        self.tools = {tool.name: tool for tool in tools}
        self.provider = provider
        self.guardrail = guardrail or ScopeGuardrail()
        self.planner = planner or SimplePlanner()
        self.router = router or RuleToolRouter()

    def run(self, request: QueryRequest) -> AgentState:
        if self.provider is None:
            # The import is intentionally delayed so constructing an agent does
            # not require optional model dependencies.
            from .config import Settings

            self.provider = provider_from_settings(Settings.from_env())
        state = AgentState(request.query, request.user)
        state.steps.append("guardrails")
        allowed, reason = self.guardrail.check(request.query, request.user)
        state.trace.append({"stage": "guardrails", "allowed": allowed})
        if not allowed:
            state.blocked = True
            state.abstained = True
            state.answer = reason
            state.steps.append("final_answer")
            state.trace.append({"stage": "final_answer", "blocked": True})
            return state

        state.steps.append("planner")
        state.tasks = self.planner.plan(request.query)
        state.trace.append({"stage": "planner", "task_count": len(state.tasks)})
        state.steps.append("tool_selection")
        for task in state.tasks:
            if len(state.results) >= self.max_tool_calls:
                state.trace.append({"stage": "budget_exhausted", "max_tool_calls": self.max_tool_calls})
                break
            tool_name = self.router.choose(task, self.tools)
            state.selected_tools.append(tool_name)
            state.trace.append({"stage": "tool_selection", "task": task.question, "tool": tool_name})
            if not tool_name:
                state.results.append(ToolResult("none", task.question, errors=("no tool available",)))
                continue
            state.steps.append(tool_name)
            try:
                result = self.tools[tool_name].run(task, request.user)
            except Exception as exc:  # fail closed and keep the run inspectable
                result = ToolResult(
                    tool_name,
                    task.question,
                    errors=(type(exc).__name__,),
                )
            state.results.append(result)
            state.trace.append(
                {
                    "stage": "tool_result",
                    "tool": tool_name,
                    "ok": result.ok,
                    "citations": len(result.citations),
                    "records": len(result.records),
                    "errors": list(result.errors),
                }
            )
            if (result.errors or not result.citations) and tool_name != "document_search":
                if "document_search" in self.tools and len(state.results) < self.max_tool_calls:
                    try:
                        fallback = self.tools["document_search"].run(task, request.user)
                    except Exception as exc:
                        fallback = ToolResult("document_search", task.question, errors=(type(exc).__name__,))
                    state.results.append(fallback)
                    state.steps.append("document_search")
                    state.trace.append(
                        {
                            "stage": "fallback",
                            "from": tool_name,
                            "to": "document_search",
                            "citations": len(fallback.citations),
                        }
                    )

        state.steps.append("summarize")
        citations = self._deduplicate_citations(state.results)
        state.citations = citations
        state.abstained = not citations
        if citations:
            state.answer = self.provider.answer(request.query, citations)
        else:
            state.answer = "当前知识库没有足够的可引用证据，暂不回答。"
        state.trace.append({"stage": "summarize", "citations": len(citations)})
        state.steps.append("validate_answer")
        cited_ids = set(re.findall(r"\[(C\d+)\]", state.answer))
        allowed_ids = {citation.citation_id for citation in citations}
        if citations and (not cited_ids or not cited_ids <= allowed_ids):
            state.validation_errors.append("answer has missing or unknown citation ids")
            state.answer = "生成结果没有包含可验证引用，暂不回答。"
            state.abstained = True
        state.trace.append(
            {
                "stage": "validate_answer",
                "valid": not state.validation_errors,
                "errors": list(state.validation_errors),
            }
        )
        state.steps.append("final_answer")
        state.trace.append({"stage": "final_answer", "blocked": state.blocked})
        return state

    @staticmethod
    def _deduplicate_citations(results: Iterable[ToolResult]) -> list[Citation]:
        seen: set[tuple[str, str]] = set()
        output: list[Citation] = []
        for result in results:
            for citation in result.citations:
                key = (citation.document_id, citation.chunk_id)
                if key in seen:
                    continue
                seen.add(key)
                output.append(replace(citation, citation_id=f"C{len(output) + 1}"))
        return output


def demo_agent(graph: KnowledgeGraph, provider: AnswerProvider | None = None) -> AgentRunner:
    """Build the offline workflow used by examples and smoke tests."""

    from .catalog import CatalogQueryTool

    return AgentRunner(
        [
            CatalogQueryTool(),
            DocumentSearchTool(graph, mode="deep", name="graph_search"),
            DocumentSearchTool(graph),
        ],
        provider=provider,
    )
