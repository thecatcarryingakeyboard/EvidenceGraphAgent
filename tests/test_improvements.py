import importlib.util
import tempfile
import unittest
from pathlib import Path

from enterprise_graphrag.agentic import AgentRunner, AgentTask, CallableTool, DocumentSearchTool, ToolResult, demo_agent
from enterprise_graphrag.catalog import CatalogQueryTool
from enterprise_graphrag.demo_data import demo_graph
from enterprise_graphrag.ingest import ingest_path
from enterprise_graphrag.models import Citation, QueryRequest, UserContext
from enterprise_graphrag.providers import DemoProvider
from enterprise_graphrag.store import KnowledgeGraph


class ImprovementsTests(unittest.TestCase):
    def test_common_word_does_not_answer_unrelated_question(self):
        state = demo_agent(demo_graph(), provider=DemoProvider()).run(QueryRequest('火星飞船发射时间'))
        self.assertTrue(state.abstained)
        self.assertEqual(state.citations, [])

    def test_catalog_runs_real_filtered_query_and_tenant_check(self):
        tool = CatalogQueryTool()
        result = tool.run(AgentTask("哪些商品库存不足需要补货"), UserContext())
        self.assertEqual([row["name"] for row in result.records], ["智能音箱 Pro"])
        self.assertEqual(result.records[0]["stock"], 8)
        self.assertEqual(tool.run(AgentTask("价格"), UserContext(tenant_id="other")).records, ())

    def test_fallback_is_bounded_and_traced(self):
        runner = AgentRunner(
            [
                CallableTool("graphrag", lambda q, u: ToolResult("graphrag", q, errors=("offline",))),
                DocumentSearchTool(demo_graph()),
            ],
            provider=DemoProvider(),
            max_tool_calls=2,
        )
        state = runner.run(QueryRequest("总结售后规则"))
        self.assertEqual(len(state.results), 2)
        self.assertTrue(any(row["stage"] == "fallback" for row in state.trace))
        self.assertFalse(state.abstained)

    def test_citation_ids_do_not_collide_across_tools(self):
        results = [
            ToolResult("a", "q", citations=(Citation("X1", "one", "a", "a", "one"),)),
            ToolResult("b", "q", citations=(Citation("X1", "two", "b", "b", "two"),)),
        ]
        self.assertEqual([c.citation_id for c in AgentRunner._deduplicate_citations(results)], ["C1", "C2"])

    def test_unknown_generated_citation_abstains(self):
        class BadProvider:
            def answer(self, query, context):
                return "fabricated [C999]"

        state = demo_agent(demo_graph(), provider=BadProvider()).run(QueryRequest("商品库存"))
        self.assertTrue(state.abstained)
        self.assertTrue(state.validation_errors)

    def test_ingest_does_not_expose_local_home_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "guide.md").write_text("售后规则需要订单。")
            graph = KnowledgeGraph()
            ingest_path(graph, tmp)
            self.assertEqual(next(iter(graph.documents.values())).source_uri, "documents://guide.md")

    @unittest.skipUnless(importlib.util.find_spec("langgraph"), "optional LangGraph dependency")
    def test_langgraph_fanout_and_checkpoint(self):

        from enterprise_graphrag.workflows.langgraph import build_graph, memory_checkpointer

        runner = demo_agent(demo_graph(), provider=DemoProvider())
        graph = build_graph(list(runner.tools.values()), provider=runner.provider, checkpointer=memory_checkpointer())
        config = {"configurable": {"thread_id": "regression-test"}, "max_concurrency": 2}
        result = graph.invoke({"question": "比较商品库存并总结售后规则", "user": UserContext()}, config)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["steps"].count("summarize"), 1)
        self.assertFalse(result["abstained"])
        self.assertTrue(graph.get_state(config).values["answer"])

    @unittest.skipUnless(importlib.util.find_spec("fastapi"), "optional FastAPI dependency")
    def test_api_agent_and_tenant_evidence(self):
        from fastapi.testclient import TestClient

        from enterprise_graphrag.api import create_app

        client = TestClient(create_app())
        result = client.post("/v1/agent", json={"query": "比较商品库存并总结售后规则"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["selected_tools"], ["catalog_query", "graph_search"])
        hit = client.post("/v1/query", json={"query": "售后规则"}).json()["citations"][0]["chunk_id"]
        self.assertEqual(client.get(f"/v1/evidence/{hit}?tenant_id=other").status_code, 404)
