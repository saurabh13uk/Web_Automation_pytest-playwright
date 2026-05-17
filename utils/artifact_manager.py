import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ArtifactManager:
    run_id: str
    run_dir: Path
    logs_dir: Path
    reports_dir: Path
    screenshots_dir: Path
    traces_dir: Path
    videos_dir: Path
    browser_logs_dir: Path

    @classmethod
    def create(cls, root: str | Path = "artifacts") -> "ArtifactManager":
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(root) / run_id
        manager = cls(
            run_id=run_id,
            run_dir=run_dir,
            logs_dir=run_dir / "logs",
            reports_dir=run_dir / "reports",
            screenshots_dir=run_dir / "screenshots",
            traces_dir=run_dir / "traces",
            videos_dir=run_dir / "videos",
            browser_logs_dir=run_dir / "browser_logs",
        )
        manager.ensure_dirs()
        return manager

    def ensure_dirs(self) -> None:
        for directory in (
            self.logs_dir,
            self.reports_dir,
            self.screenshots_dir,
            self.traces_dir,
            self.videos_dir,
            self.browser_logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def safe_name(nodeid: str) -> str:
        name = re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid)
        return name.strip("_")[:180]

    @property
    def html_report(self) -> Path:
        return self.reports_dir / "extent_report.html"

    @property
    def automation_log(self) -> Path:
        return self.logs_dir / "automation.log"

    def screenshot_path(self, nodeid: str) -> Path:
        return self.screenshots_dir / f"{self.safe_name(nodeid)}.png"

    def trace_path(self, nodeid: str) -> Path:
        return self.traces_dir / f"{self.safe_name(nodeid)}.zip"

    def browser_log_path(self, nodeid: str) -> Path:
        return self.browser_logs_dir / f"{self.safe_name(nodeid)}.log"
