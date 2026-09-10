
from engines.insight_agent.tools.retrival_service import InsightRetrivalService
from typing import Any
from engines.insight_agent.state import InsightState
from engines.common.nodes.base_node import ResearchNodeContext
from engines.common.nodes.base_node import BaseNode

class RetrievalNode(BaseNode):
    def __init__(self, ctx: ResearchNodeContext) -> None:
        super().__init__(ctx)
    
    async def __call__(self, state: InsightState) -> dict[str, Any]:
        # 调用检索服务
        # 1. 接受用户查询问题
        user_query = state["query"]
        # 2. 调用检索服务
        retrival_service = InsightRetrivalService()
        evidence_records = retrival_service.retrival_evidence(user_query)

        # 3. 获取state中的证据池
        evidence_pool = state["evidence_pool"]
        # 4. 更新证据池中的证据记录
        evidence_pool.records = evidence_records

        # 5. 返回状态
        return {
            "evidence_pool": evidence_pool
        }