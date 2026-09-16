"""公共基础设施模块：engines/common/io/report_io.py。"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def research_report_dir(role: str) -> Path:
    return PROJECT_ROOT / "data" / "report" / role


def latest_research_results() -> dict[str, dict[str, str]]:
    results = {}
    for role in ("insight", "media"):
        # 兼容旧版 output_dir 为空时保存在项目根目录的报告。
        candidates = [
            path
            for directory in (research_report_dir(role), PROJECT_ROOT)
            for path in directory.glob(f"{role}_*.md")
            if path.is_file()
        ]
        if not candidates:
            continue
        latest = max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name))
        results[role] = {
            "final_report": latest.read_text(encoding="utf-8"),
            "report_file": str(latest.relative_to(PROJECT_ROOT)),
        }
    return results






def save_md_report(output_dir: str , prefix: str, query: str, content: str, suffix: str = ".md") -> Path:
    """直接完成从命名到落盘的全流程"""
    stem = f"{prefix}_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    path = Path(output_dir) / f"{stem}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
