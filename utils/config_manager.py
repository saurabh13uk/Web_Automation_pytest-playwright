from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


CONFIG_FILE = Path(__file__).resolve().parents[1] / "config" / "config.yaml"


@dataclass(frozen=True)
class FrameworkConfig:
    env: str
    base_url: str
    browser: str
    headless: bool
    timeout: int
    slow_mo: int
    screenshot_on_failure: bool
    video_on_failure: bool


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config(
    env: str = "default",
    browser: str | None = None,
    base_url: str | None = None,
    headed: bool = False,
    slow_mo: int | None = None,
    screenshot: bool | None = None,
) -> FrameworkConfig:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

    with CONFIG_FILE.open(encoding="utf-8") as file:
        raw_config = yaml.safe_load(file) or {}

    if env not in raw_config:
        available = ", ".join(sorted(raw_config))
        raise ValueError(f"Unknown environment '{env}'. Available: {available}")

    values = {**raw_config["default"], **raw_config[env]}
    return FrameworkConfig(
        env=env,
        base_url=base_url or values["base_url"],
        browser=browser or values["browser"],
        headless=False if headed else _as_bool(values["headless"]),
        timeout=int(values["timeout"]),
        slow_mo=int(values["slow_mo"] if slow_mo is None else slow_mo),
        screenshot_on_failure=_as_bool(
            values["screenshot_on_failure"] if screenshot is None else screenshot
        ),
        video_on_failure=_as_bool(values["video_on_failure"]),
    )
