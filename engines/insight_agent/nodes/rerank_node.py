from collections import defaultdict
from engines.insight_agent.evidence.models import EvidenceRecord
from engines.insight_agent.evidence.models import RetrievalMeta
from typing import Any
from engines.insight_agent.state import InsightState
from engines.common.nodes.base_node import ResearchNodeContext
from engines.common.nodes.base_node import BaseNode


_CHANNEL_WEIGHTS = {
    "semantic_recall": 0.5,
    "keyword_recall": 0.4,
    "hot_recall": 0.1,
    "comment_recall": 0.4
}

SOURCE_QUOTAS = {
    "keyword_recall": 10,
    "semantic_recall": 10,
    "comment_recall": 10,
    "hot_recall": 10,
}

MAX_EVIDENCE_RECORDS = 50


class RerankNode(BaseNode):
    def __init__(self, ctx: ResearchNodeContext) -> None:
        super().__init__(ctx)
    async def __call__(self, state: InsightState) -> dict[str, Any]:
        # 获取证据池,获取records
        evidence_pool = state["evidence_pool"]
        records = evidence_pool.records

        # 1. 去重，合并
        merged_records = _dedupe_and_merge(records)
        # 2. 打分，排序
        sorted_records = _sort_records(merged_records)
        # 3. 根据通道选择指定的证据记录对象列表
        filtered_records = __apply_channel_filter(sorted_records)

        evidence_pool = state["evidence_pool"]
        evidence_pool.records = filtered_records

        return {
            "evidence_pool": evidence_pool
        }

def _dedupe_and_merge(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    去重，合并
    """
    # 1. 判断是否有证据记录
    if not records:
        return []
    # 2. 遍历
    # 2.1 基于ID即可
    record_by_id: dict[str, dict[str, Any]] = {}

    for record in records:
        # 获取记录id
        record_id = record["id"]
        # 判断当前记录id是否存在
        if record_id not in record_by_id:
            continue

        # 3. 当前记录已经存在（不剔除重复的记录）
        
        # 3.1 更新当前记录的热度值（找同一条记录中最大热度值的那一个）

        # 3.2 更新当前记录的检索元数据（更新检索元数据查询，更新检索元数据通道，更新检索元数据检索分数）

        base_record = record_by_id[record_id]
        base_record.retrieval = _merge_retrieval_meta(base_record.retrieval, record.retrieval)
        # 两套规则计算热度值（多源数据：milvus 和 mysql中数据一致）
        base_record.score = max(base_record.score, record.score) 

    # 3. 利用重复记录
    records = list(record_by_id.values())
    return records


def _merge_retrieval_meta(base_record: EvidenceRecord, new_record: EvidenceRecord) -> RetrievalMeta:
    """
    合并检索元数据
    """
    # 合并 retrieval_scores
    base_record.retrieval.retrieval_scores.update(new_record.retrieval.retrieval_scores)

    # set去重 双通道检索
    return RetrievalMeta(
        matched_queries=sorted(set(base_record.retrieval.matched_queries + new_record.retrieval.matched_queries)),
        retrieval_channels=sorted(set(base_record.retrieval.retrieval_channels + new_record.retrieval.retrieval_channels)),
        retrieval_scores=base_record.retrieval.retrieval_scores
    )

def _retrival_score(merged_record: EvidenceRecord):
    # merged_record: retrieval_channels: ["semantic_recall", "hot_recall"] retrieval_scores: {"semantic_recall": 0.8, "hot_recall": 0.2}
    meta = merged_record.retrieval
    return min(sum([meta.retrieval_scores[channel] * _CHANNEL_WEIGHTS[channel] for channel in meta.retrieval_channels]), 1.0)


def _sort_records(merged_records: list[EvidenceRecord]) -> list[EvidenceRecord]:
    """
    EvidenceRecord对象的检索元数据的通道就有可能是多个[keyord_recall,semantic_recall]
    """
    # 计算最大热度值，max可能取空列表 or 1.0 ，确保分母不为0
    max_hot_score = max([merged_record.hotness_score for merged_record in merged_records]) or 1.0

    for merged_record in merged_records:
        # 总得分（二因子）检索相关得分*0.6 + 热度值 * 0.4
        final_score = (_retrival_score(merged_record) * 0.6) + ((merged_record.hotness_score/max_hot_score) * 0.4)
        merged_record.score = final_score
    return sorted(merged_records, key=lambda x: final_score, reverse=True)


def __apply_channel_filter(sorted_records: list[EvidenceRecord]) -> list[EvidenceRecord]:
    """
    根据通道筛选证据记录对象列表
    """
    selected_record = []
    channel_count:dict[str,int] = defaultdict(int)
    for record in sorted_records:
        channel = _SOURCE_QUOTAS(record)
        if channel_count[channel] < SOURCE_QUOTAS[channel]:
            selected_record.append(record)
            channel_count[channel] += 1

    if len(selected_record) < MAX_EVIDENCE_RECORDS:
        selected_id = [r for r in selected_record]
        remainders = [r for r in sorted_records if r.id not in selected_id]
        selected_record.extend(remainders[:MAX_EVIDENCE_RECORDS - len(selected_record)])

    return sorted(selected_record, key=lambda x: record.score, reverse=True)

def _SOURCE_QUOTAS(record: EvidenceRecord)->str:
    # record: retrieval_channels ["a", "b"]
    retrieval_channels = record.retrieval.retrieval_channels
    for channel in SOURCE_QUOTAS:
        if channel in retrieval_channels:
            return channel

    return "other"