from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from utils.config_manager import FrameworkConfig, load_config
from utils.logger import get_logger


logger = get_logger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("hybrid-framework")
    group.addoption("--target-env", action="store", default="default", help="Environment key from config.yaml")
    group.addoption("--target-browser", action="store", default=None, help="chromium, firefox, or webkit")
    group.addoption("--app-url", action="store", default=None, help="Override application URL")
    group.addoption("--run-headed", action="store_true", help="Run browser in headed mode")
    group.addoption("--action-slowmo", action="store", type=int, default=None, help="Slow motion in milliseconds")
    group.addoption(
        "--capture-screenshot",
        action="store",
        default=None,
        choices=["on", "off"],
        help="Capture screenshot on failure",
    )


@pytest.fixture(scope="session")
def framework_config(pytestconfig: pytest.Config) -> FrameworkConfig:
    screenshot_flag = pytestconfig.getoption("--capture-screenshot")
    screenshot = None if screenshot_flag is None else screenshot_flag == "on"
    return load_config(
        env=pytestconfig.getoption("--target-env"),
        browser=pytestconfig.getoption("--target-browser"),
        base_url=pytestconfig.getoption("--app-url"),
        headed=pytestconfig.getoption("--run-headed"),
        slow_mo=pytestconfig.getoption("--action-slowmo"),
        screenshot=screenshot,
    )


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright, framework_config: FrameworkConfig) -> Generator[Browser, None, None]:
    browser_type = getattr(playwright_instance, framework_config.browser)
    logger.info("Launching %s browser. Headless=%s", framework_config.browser, framework_config.headless)
    browser = browser_type.launch(headless=framework_config.headless, slow_mo=framework_config.slow_mo)
    yield browser
    browser.close()


@pytest.fixture()
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    context = browser.new_context(viewport={"width": 1366, "height": 768}, record_video_dir=None)
    yield context
    context.close()


@pytest.fixture()
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Generator[Page, None, None]:
    page = context.new_page()
    request.node.page = page
    yield page


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or not report.failed:
        return

    config: FrameworkConfig | None = item.funcargs.get("framework_config")
    page: Page | None = getattr(item, "page", None)
    if not config or not page or not config.screenshot_on_failure:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = Path("screenshots") / f"{item.name}_{timestamp}.png"
    screenshot_path.parent.mkdir(exist_ok=True)
    page.screenshot(path=str(screenshot_path), full_page=True)
    screenshot_content = base64.b64encode(screenshot_path.read_bytes()).decode("utf-8")
    extras = getattr(report, "extras", [])
    extras.append(pytest_html.extras.png(screenshot_content, name="Failure Screenshot"))
    report.extras = extras
    logger.error("Failure screenshot captured: %s", screenshot_path)


def pytest_configure(config: pytest.Config) -> None:
    global pytest_html
    pytest_html = config.pluginmanager.getplugin("html")
