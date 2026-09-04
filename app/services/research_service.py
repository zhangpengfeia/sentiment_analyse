from engines.orchestration.research import run_research
from typing import Any


class ResearchService:

    def start_research(self, query: str) -> dict[str, Any]:
        # TODO 
        # 执行编排层启动两个研究agent执行的任务
        try:
            run_research(query)
            return {"started": True}
        except Exception as exc:
            return {"error": exc}


    def get_research_result(self) -> dict[str, Any]:
        pass
