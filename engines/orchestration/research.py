from engines.common.eventing.publishers import pub_role_result, pub_role_error
from engines.common.eventing.event import RoleResultEvent, RoleErrorEvent
from engines.common.eventing.event import RoleProgressEvent
from engines.common.eventing.publishers import pub_role_progress
from loguru import logger
from engines.common.runtime.role_log import route_logs_by_role
import asyncio
from engines.media_agent.agent import invoke_media_agent
from engines.insight_agent.agent import invoke_insight_agent
from engines.common.progress import ProgressUpdate
from engines.common.llm.llm_client import LLMClient
from engines.common.io.report_io import research_report_dir
from typing import Callable, Awaitable

ProgressCallback = Callable[[ProgressUpdate], None]
AgentInvoker = Callable[[str, str, LLMClient, str, ProgressCallback], Awaitable[None]]

_RESEARCH_INVOKER: dict[str, AgentInvoker] = {
    "insight": invoke_insight_agent,
    "media": invoke_media_agent,
}

def run_research(query: str)  -> None:
    """
    职责：运行两个维度查询的Agent(面向私域数据检索的insight_agent 面向公域数据检索的media_agent)
    执行两个Agent【invoke_insight_agent、invoke_media_agent】的时候都需要以下几个参数
    """

    # 后台启动两个异步任务（并没有创建新线程，一个事件循环线程，切换协程对象，多个协程并发执行）
    for role in _RESEARCH_INVOKER:
        asyncio.create_task(_run_research_task(query,role))
    pass


async def _run_research_task(query: str, role: str) -> None:
    """
    职责：运行一个维度查询的Agent
    """
    with route_logs_by_role(role):
        # 初始化单独调用一次
        _publish_role_progress(role, update=ProgressUpdate("starting","准备开始分析舆情话题",0))
        # 执行指定角色的研究agent
        try:
            await _execute_research_flow(role=role, query=query)
            # 发布
            pub_role_result(RoleResultEvent(role=role))
        except Exception as exc:
            # 发布失败
            logger.error(f"运行{role}失败: {exc}")
            pub_role_error(RoleErrorEvent(role=role, error=str(exc)))


async def _execute_research_flow(role: str, query: str):
    # 1. 获取指定角色Agent的LLM配置信息的客户端对象
    llm_client = LLMClient.from_role(role)

    # 2. 获取指定角色Agent的报告落盘目录
    output_dir = str(research_report_dir(role))

    # 3. 运行指定角色的Agent[INSIGHT]
    await _RESEARCH_INVOKER[role](
        query,
        role,
        llm_client,
        output_dir,
        lambda update: _publish_role_progress(role, update)
    )

# 发布指定角色的进度更新回调事件
def _publish_role_progress(role: str, update: ProgressUpdate):
    pub_role_progress(RoleProgressEvent(role=role,
                                        status= update.status,
                                        message= update.message,
                                        progress_pct=update.progress_pct
                                        ))
