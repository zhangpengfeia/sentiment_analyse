import unittest
from unittest.mock import AsyncMock, patch

from engines.insight_agent.evidence.models import EvidencePool, EvidenceRecord, RetrievalMeta
from engines.insight_agent.graph import build_graph
from engines.insight_agent.nodes.retrieval_node import RetrievalNode
from engines.insight_agent.nodes.rerank_node import RerankNode


class InsightRetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_rerank_handles_missing_hotness(self):
        cases = [
            ([None, None], 0.0, 0.12),
            ([None, 20.0], 20.0, 0.52),
            ([20.0, None], 20.0, 0.52),
            ([None], 0.0, 0.12),
            ([0.0, None], 0.0, 0.12),
        ]
        for hotness_values, expected_hotness, expected_score in cases:
            with self.subTest(hotness_values=hotness_values):
                records = [
                    EvidenceRecord(
                        id="doc_1", platform="test", source_table="posts",
                        source_keyword=None, content="高考", published_at="2026-09-11",
                        hotness_score=hotness,
                        retrieval=RetrievalMeta(
                            ["高考"], ["keyword_recall"], {"keyword_recall": 0.5}
                        ),
                    )
                    for hotness in hotness_values
                ]
                result = await RerankNode(None)({
                    "query": "高考", "role": "insight",
                    "evidence_pool": EvidencePool(query="高考", records=records),
                })
                ranked = result["evidence_pool"].records
                self.assertEqual(len(ranked), 1)
                self.assertEqual(ranked[0].hotness_score, expected_hotness)
                self.assertAlmostEqual(ranked[0].final_score, expected_score)

    async def test_graph_initializes_pool_and_reranks_real_records(self):
        records = [
            EvidenceRecord(
                id="doc_1", platform="test", source_table="posts",
                source_keyword=None, content="高考", published_at="2026-09-11",
                hotness_score=hotness,
                retrieval=RetrievalMeta(["高考"], [channel], {channel: 0.5}),
            )
            for channel, hotness in [("keyword_recall", 10), ("semantic_recall", 20)]
        ]
        with patch(
            "engines.insight_agent.nodes.retrieval_node.InsightRetrivalService"
        ) as service:
            retrieve = AsyncMock(return_value=records)
            service.return_value.retrival_evidence = retrieve
            result = await build_graph(None).ainvoke({"query": "高考", "role": "insight"})

        retrieve.assert_awaited_once_with("高考")
        pool = result["evidence_pool"]
        self.assertEqual(pool.query, "高考")
        self.assertEqual(len(pool.records), 1)
        self.assertEqual(pool.records[0].hotness_score, 20)
        self.assertEqual(set(pool.records[0].retrieval.retrieval_channels),
                         {"keyword_recall", "semantic_recall"})
        self.assertGreater(pool.records[0].final_score, 0)

    async def test_graph_handles_empty_retrieval(self):
        with patch(
            "engines.insight_agent.nodes.retrieval_node.InsightRetrivalService"
        ) as service:
            service.return_value.retrival_evidence = AsyncMock(return_value=[])
            result = await build_graph(None).ainvoke({"query": "高考", "role": "insight"})
        self.assertEqual(result["evidence_pool"].records, [])

    async def test_retrieval_reuses_existing_pool(self):
        pool = EvidencePool(query="高考")
        with patch(
            "engines.insight_agent.nodes.retrieval_node.InsightRetrivalService"
        ) as service:
            service.return_value.retrival_evidence = AsyncMock(return_value=[])
            result = await RetrievalNode(None)({
                "query": "高考", "role": "insight", "evidence_pool": pool,
            })
        self.assertIs(result["evidence_pool"], pool)


if __name__ == "__main__":
    unittest.main()
