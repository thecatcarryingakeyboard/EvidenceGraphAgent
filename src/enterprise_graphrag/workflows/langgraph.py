"""LangGraph version of the interview-friendly multi-tool workflow.

LangGraph is deliberately imported inside :func:`build_graph`.  The offline
CLI and unit tests therefore stay dependency-free, while a reader who wants
to connect a real checkpoint store or interrupt for human approval can inspect
the exact state graph used by the project.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict

from ..agentic import AgentRunner, AgentTask, AgentTool, Guardrail, RuleToolRouter, SimplePlanner, ToolResult
from ..models import UserContext
from ..providers import AnswerProvider


class WorkflowState(TypedDict, total=False):
    question: str
    user: UserContext
    tasks: list[AgentTask]
    selected_tools: list[str]
    results: list[ToolResult]
    answer: str
    validation_errors: list[str]
    blocked: bool
    steps: Annotated[list[str], add]


def build_graph(
    tools: list[AgentTool],
    *,
    provider: AnswerProvider | None = None,
    guardrail: Guardrail | None = None,
    planner: SimplePlanner | None = None,
    router: RuleToolRouter | None = None,
) -> Any:
    """Build and compile a LangGraph state graph.

    The returned graph is compatible with ``invoke``/``ainvoke``.  For a
    production application, pass a checkpointer to LangGraph's ``compile``
    method and insert an ``interrupt`` before high-risk tools.
    """

    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install the 'langgraph' extra to use this workflow") from exc

    runner = AgentRunner(tools, provider=provider, guardrail=guardrail, planner=planner, router=router)

    def guardrails(state: WorkflowState) -> dict[str, Any]:
        allowed, reason = runner.guardrail.check(state["question"], state.get("user", UserContext()))
        if not allowed:
            return {"blocked": True, "answer": reason, "steps": ["guardrails", "final_answer"]}
        return {"blocked": False, "steps": ["guardrails"]}

    def plan(state: WorkflowState) -> dict[str, Any]:
        return {"tasks": runner.planner.plan(state["question"]), "steps": ["planner"]}

    def select_tools(state: WorkflowState) -> dict[str, Any]:
        names = [runner.router.choose(task, runner.tools) for task in state.get("tasks", [])]
        return {"selected_tools": names, "steps": ["tool_selection"]}

    def execute_tools(state: WorkflowState) -> dict[str, Any]:
        user = state.get("user", UserContext())
        results: list[ToolResult] = []
        steps = []
        for task, name in zip(state.get("tasks", []), state.get("selected_tools", [])):
            steps.append(name or "no_tool")
            if name not in runner.tools:
                results.append(ToolResult("none", task.question, errors=("no tool available",)))
            else:
                results.append(runner.tools[name].run(task, user))
        return {"results": results, "steps": steps}

    def summarize(state: WorkflowState) -> dict[str, Any]:
        citations = runner._deduplicate_citations(state.get("results", []))
        if not citations:
            return {"answer": "当前知识库没有足够的可引用证据，暂不回答。", "steps": ["summarize"]}
        if runner.provider is None:
            from ..config import Settings
            from ..providers import provider_from_settings

            runner.provider = provider_from_settings(Settings.from_env())
        return {"answer": runner.provider.answer(state["question"], citations), "steps": ["summarize"]}  # type: ignore[union-attr]

    def final_answer(state: WorkflowState) -> dict[str, Any]:
        return {"steps": ["final_answer"]}

    def validate_answer(state: WorkflowState) -> dict[str, Any]:
        citations = runner._deduplicate_citations(state.get("results", []))
        if citations and not any(item.citation_id in state.get("answer", "") for item in citations):
            return {
                "answer": "生成结果没有包含可验证引用，暂不回答。",
                "validation_errors": ["answer did not contain a citation id"],
                "steps": ["validate_answer"],
            }
        return {"validation_errors": [], "steps": ["validate_answer"]}

    def route(state: WorkflowState) -> str:
        return "final_answer" if state.get("blocked") else "planner"

    builder = StateGraph(WorkflowState)
    builder.add_node("guardrails", guardrails)
    builder.add_node("planner", plan)
    builder.add_node("tool_selection", select_tools)
    builder.add_node("execute_tools", execute_tools)
    builder.add_node("summarize", summarize)
    builder.add_node("validate_answer", validate_answer)
    builder.add_node("final_answer", final_answer)
    builder.add_edge(START, "guardrails")
    builder.add_conditional_edges("guardrails", route, {"planner": "planner", "final_answer": "final_answer"})
    builder.add_edge("planner", "tool_selection")
    builder.add_edge("tool_selection", "execute_tools")
    builder.add_edge("execute_tools", "summarize")
    builder.add_edge("summarize", "validate_answer")
    builder.add_edge("validate_answer", "final_answer")
    builder.add_edge("final_answer", END)
    return builder.compile()
