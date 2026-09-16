from typing import Any
from engines.orchestration.research import run_research
from engines.common.io.report_io import latest_research_results


class ResearchService:

    def start_research(self, query: str) -> dict[str, Any]:
        # 1. 引擎编排层启动两个研究Agent执行的任务
        try:
            run_research(query)
            return {"started": True}
        except Exception as e:
            return {"started": False,"error":str(e)}


    def get_research_result(self) -> dict[str, Any]:
        return latest_research_results()
