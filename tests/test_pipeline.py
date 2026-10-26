import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from enterprise_graphrag.demo_data import demo_graph
from enterprise_graphrag.eval import EvalCase, run_eval
from enterprise_graphrag.governance import ToolRegistry, ToolSpec
from enterprise_graphrag.models import Document, QueryRequest, UserContext
from enterprise_graphrag.pipeline import QueryEngine
from enterprise_graphrag.store import KnowledgeGraph


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = QueryEngine(demo_graph())

    def test_answer_contains_citations_and_trace(self) -> None:
        response = self.engine.answer(QueryRequest("上线前需要完成哪些工作？"))
        self.assertTrue(response.citations)
        self.assertIn("C1", response.answer)
        self.assertTrue(response.trace_id)
        self.assertGreaterEqual(len(response.trace), 4)

    def test_global_mode_expands_related_context(self) -> None:
        response = self.engine.answer(QueryRequest("MCP 工具如何治理？", mode="deep"))
        self.assertEqual(response.mode, "deep")
        self.assertTrue(response.citations)

    def test_tenant_isolation_and_abstention(self) -> None:
        response = self.engine.answer(
            QueryRequest("上线前需要完成哪些工作？", user=UserContext(tenant_id="other"))
        )
        self.assertTrue(response.abstained)
        self.assertEqual(response.citations, [])

    def test_eval_report_is_json_serializable(self) -> None:
        report = run_eval(self.engine, [EvalCase("没有足够证据时应该怎么办？", ("拒答",))])
        payload = json.dumps(report.to_dict(), ensure_ascii=False)
        self.assertIn("citation_rate", payload)

    def test_ingestion_chunks_and_graph_expansion(self) -> None:
        graph = KnowledgeGraph()
        graph.ingest(Document("d1", "内部手册", "权限审批需要人工确认。\n工具调用需要审计。", tenant_id="t1"), chunk_size=30, overlap=5)
        self.assertTrue(graph.chunks)
        self.assertTrue(graph.entities)
        self.assertTrue(graph.expand(set(graph.chunks), UserContext(tenant_id="t1")))

    def test_tool_registry_requires_approval_for_high_risk_action(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolSpec("delete_record", "Delete a record", risk="high", requires_approval=True),
            lambda **kwargs: {"ok": True, "tenant": kwargs["user"].tenant_id},
        )
        with self.assertRaises(PermissionError):
            registry.invoke("delete_record", UserContext(tenant_id="t1"), {}, approved=False)
        self.assertEqual(
            registry.invoke("delete_record", UserContext(tenant_id="t1"), {}, approved=True),
            {"ok": True, "tenant": "t1"},
        )


if __name__ == "__main__":
    unittest.main()
