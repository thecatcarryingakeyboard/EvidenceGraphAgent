"""Optional LangGraph runtime with parallel Send fan-out and caller-owned checkpoints."""

from __future__ import annotations

from dataclasses import replace
from operator import add
from typing import Annotated, Any

from typing_extensions import TypedDict

from ..agentic import AgentRunner, AgentTask, AgentTool, Guardrail, RuleToolRouter, SimplePlanner, ToolResult
from ..config import Settings
from ..models import UserContext
from ..providers import AnswerProvider, provider_from_settings


class WorkflowState(TypedDict, total=False):
    question: str
    user: UserContext
    tasks: list[AgentTask]
    selected_tools: list[str]
    results: Annotated[list[ToolResult], add]
    answer: str
    citations: list[Any]
    abstained: bool
    validation_errors: list[str]
    blocked: bool
    steps: Annotated[list[str], add]
    task: AgentTask
    tool_name: str
    task_index: int


def build_graph(
    tools: list[AgentTool],
    *,
    provider: AnswerProvider | None = None,
    guardrail: Guardrail | None = None,
    planner: SimplePlanner | None = None,
    router: RuleToolRouter | None = None,
    checkpointer: Any = None,
) -> Any:
    """Compile bounded task fan-out; provide a distinct thread_id for each independent run.

    A checkpointer belongs to the caller. InMemorySaver supports local inspection;
    durable execution requires a separately configured persistent saver.
    """
    try:
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Send
    except ImportError as exc:
        raise RuntimeError("Install the 'langgraph' extra to use this workflow") from exc
    runner = AgentRunner(tools, provider=provider, guardrail=guardrail, planner=planner, router=router)

    def guardrails(state: WorkflowState) -> dict[str, Any]:
        allowed, reason = runner.guardrail.check(state["question"], state.get("user", UserContext()))
        return {"blocked": not allowed, "answer": reason, "abstained": not allowed, "steps": ["guardrails"]}

    def plan(state: WorkflowState) -> dict[str, Any]:
        return {"tasks": runner.planner.plan(state["question"]), "steps": ["planner"]}

    def select_tools(state: WorkflowState) -> dict[str, Any]:
        return {
            "selected_tools": [runner.router.choose(task, runner.tools) for task in state["tasks"]],
            "steps": ["tool_selection"],
        }

    def fan_out(state: WorkflowState) -> list[Any]:
        return [
            Send(
                "execute_tool",
                {"task": task, "tool_name": name, "task_index": index, "user": state.get("user", UserContext())},
            )
            for index, (task, name) in enumerate(zip(state["tasks"], state["selected_tools"]))
        ]

    def execute_tool(state: WorkflowState) -> dict[str, Any]:
        name, task = state["tool_name"], state["task"]
        try:
            result = runner.tools[name].run(task, state["user"])
        except Exception as exc:
            result = ToolResult(name, task.question, errors=(type(exc).__name__,))
        result = replace(result, metadata={**result.metadata, "task_index": state["task_index"]})
        return {"results": [result], "steps": [name]}

    def summarize(state: WorkflowState) -> dict[str, Any]:
        results = sorted(state.get("results", []), key=lambda item: item.metadata["task_index"])
        citations = runner._deduplicate_citations(results)
        selected_provider = runner.provider or provider_from_settings(Settings.from_env())
        answer = (
            selected_provider.answer(state["question"], citations)
            if citations
            else "当前知识库没有足够证据，暂不回答。"
        )
        return {"answer": answer, "citations": citations, "abstained": not citations, "steps": ["summarize"]}

    def validate_answer(state: WorkflowState) -> dict[str, Any]:
        import re

        ids = set(re.findall(r"\[(C\d+)\]", state.get("answer", "")))
        allowed = {item.citation_id for item in state.get("citations", [])}
        if allowed and (not ids or not ids <= allowed):
            return {
                "answer": "生成结果缺少有效引用，暂不回答。",
                "abstained": True,
                "validation_errors": ["answer has missing or unknown citation ids"],
                "steps": ["validate_answer"],
            }
        return {"validation_errors": [], "steps": ["validate_answer"]}

    builder = StateGraph(WorkflowState)
    for name, node in [
        ("guardrails", guardrails),
        ("planner", plan),
        ("tool_selection", select_tools),
        ("execute_tool", execute_tool),
        ("summarize", summarize),
        ("validate_answer", validate_answer),
    ]:
        builder.add_node(name, node)
    builder.add_node("final_answer", lambda state: {"steps": ["final_answer"]})
    builder.add_edge(START, "guardrails")
    builder.add_conditional_edges("guardrails", lambda state: "final_answer" if state["blocked"] else "planner")
    builder.add_edge("planner", "tool_selection")
    builder.add_conditional_edges("tool_selection", fan_out, ["execute_tool"])
    builder.add_edge("execute_tool", "summarize")
    builder.add_edge("summarize", "validate_answer")
    builder.add_edge("validate_answer", "final_answer")
    builder.add_edge("final_answer", END)
    return builder.compile(checkpointer=checkpointer)


def memory_checkpointer() -> Any:
    """Local saver with an explicit allowlist for this application's state types."""
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    allowed = [
        ("enterprise_graphrag.models", "UserContext"),
        ("enterprise_graphrag.models", "Citation"),
        ("enterprise_graphrag.agentic", "AgentTask"),
        ("enterprise_graphrag.agentic", "ToolResult"),
    ]
    return InMemorySaver(serde=JsonPlusSerializer(allowed_msgpack_modules=allowed))
