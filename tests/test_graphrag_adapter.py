import asyncio
import sys
import types
import unittest
from unittest.mock import patch

from enterprise_graphrag.adapters.graphrag import MicrosoftGraphRAGAdapter


class GraphRAGContractTests(unittest.TestCase):
    def test_four_query_signatures_and_dataframe_context(self):
        calls = []

        class Table:
            def to_dict(self, orient):
                return [{"id": "source", "text": "warranty evidence"}]

        async def local_search(
            *,
            config,
            query,
            response_type,
            entities,
            communities,
            community_reports,
            text_units,
            relationships,
            covariates,
            community_level,
        ):
            calls.append("local")
            return "answer", {"sources": Table()}

        async def drift_search(
            *,
            config,
            query,
            response_type,
            entities,
            communities,
            community_reports,
            text_units,
            relationships,
            community_level,
        ):
            calls.append("drift")
            return "answer", {"sources": Table()}

        async def global_search(
            *,
            config,
            query,
            response_type,
            entities,
            communities,
            community_reports,
            community_level,
            dynamic_community_selection,
        ):
            calls.append("global")
            return "answer", {"sources": Table()}

        async def basic_search(*, config, query, text_units):
            calls.append("basic")
            return "answer", {"sources": Table()}

        fake = types.ModuleType("graphrag")
        fake.api = types.SimpleNamespace(
            local_search=local_search, drift_search=drift_search, global_search=global_search, basic_search=basic_search
        )
        adapter = MicrosoftGraphRAGAdapter(None, [], [], [], text_units=[], relationships=[])
        with patch.dict(sys.modules, {"graphrag": fake}):
            for mode in ("local", "drift", "global", "basic"):
                answer, citations = asyncio.run(adapter.query_async("question", mode))
                self.assertEqual(answer, "answer")
                self.assertEqual(citations[0].quote, "warranty evidence")
        self.assertEqual(calls, ["local", "drift", "global", "basic"])
