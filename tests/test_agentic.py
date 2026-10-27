import unittest

from enterprise_graphrag.adapters.neo4j import CypherRejected, ReadOnlyNeo4jAdapter, Text2CypherExecutor
from enterprise_graphrag.agentic import demo_agent
from enterprise_graphrag.demo_data import demo_graph
from enterprise_graphrag.models import QueryRequest


class FakeGraph:
    def __init__(self):
        self.queries = []
        self.structured_schema = {"nodes": ["Product"]}

    def query(self, query, params=None):
        self.queries.append((query, params))
        return [{"name": "demo", "count": 1}]


class AgenticTests(unittest.TestCase):
    def test_agent_keeps_planning_and_tool_steps(self):
        state = demo_agent(demo_graph()).run(QueryRequest("比较商品库存并总结售后规则"))
        self.assertEqual(state.steps[:3], ["guardrails", "planner", "tool_selection"])
        self.assertEqual(state.selected_tools, ["catalog_query", "graph_search"])
        self.assertIn("validate_answer", state.steps)
        self.assertTrue(state.answer)

    def test_cypher_policy_rejects_write_and_limits_reads(self):
        graph = FakeGraph()
        adapter = ReadOnlyNeo4jAdapter(graph, default_limit=10)
        with self.assertRaises(CypherRejected):
            adapter.validate("MATCH (n) DELETE n")
        rows = adapter.run("MATCH (n:Product) RETURN n.name")
        self.assertEqual(rows[0]["count"], 1)
        self.assertIn("LIMIT 10", graph.queries[-1][0])

    def test_text2cypher_retries_after_invalid_generation(self):
        graph = FakeGraph()
        adapter = ReadOnlyNeo4jAdapter(graph)
        attempts = iter(["CREATE (n)", "MATCH (n) RETURN n"])
        executor = Text2CypherExecutor(adapter, lambda q, s, e: next(attempts), max_attempts=2)
        result = executor.run("列出节点")
        self.assertEqual(result["attempts"], 2)
        self.assertTrue(result["records"])
        self.assertEqual(len(result["retry_history"]), 1)


if __name__ == "__main__":
    unittest.main()
