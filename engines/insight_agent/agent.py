from engines.orchestration.research import ProgressCallback
from engines.common.llm_client import LLMClient
async def invoke_insight_agent(
    query: str,
    llm_client: LLMClient,
    progress_callback: ProgressCallback,
) -> None:
    """
    职责：调用私域检索智能体专家的Agent
    """