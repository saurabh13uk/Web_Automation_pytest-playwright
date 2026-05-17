from __future__ import annotations

import base64
import platform
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Any, Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from utils.artifact_manager import ArtifactManager
from utils.config_manager import FrameworkConfig, load_config
from utils.logger import configure_logging, get_logger


SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
pytest_html: Any = None
logger = get_logger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("hybrid-framework")
    group.addoption("--target-env", action="store", default="default", help="Environment key from config.yaml")
    group.addoption("--target-browser", action="store", default=None, help="chromium, firefox, or webkit")
    group.addoption("--app-url", action="store", default=None, help="Override application URL")
    group.addoption("--run-headed", action="store_true", help="Run browser in headed mode")
    group.addoption("--action-slowmo", action="store", type=int, default=None, help="Slow motion in milliseconds")
    group.addoption("--artifact-root", action="store", default="artifacts", help="Root directory for run artifacts")
    group.addoption(
        "--capture-screenshot",
        action="store",
        default=None,
        choices=["on", "off"],
        help="Capture screenshot on failure",
    )
    group.addoption(
        "--capture-video",
        action="store",
        default=None,
        choices=["on", "off"],
        help="Capture Playwright video on failure",
    )
    group.addoption(
        "--capture-trace",
        action="store",
        default=None,
        choices=["on", "off"],
        help="Capture Playwright trace on failure",
    )


def pytest_configure(config: pytest.Config) -> None:
    global pytest_html
    artifact_manager = ArtifactManager.create(config.getoption("--artifact-root"))
    config.artifact_manager = artifact_manager
    configure_logging(artifact_manager.automation_log)
    pytest_html = config.pluginmanager.getplugin("html")

    if pytest_html and not config.option.htmlpath:
        config.option.htmlpath = str(artifact_manager.html_report)

    _set_report_metadata(config, artifact_manager)
    logger.info("Artifact directory: %s", artifact_manager.run_dir)


def pytest_html_report_title(report) -> None:
    report.title = "Hybrid Playwright Automation Report"


@pytest.fixture(scope="session")
def artifact_manager(pytestconfig: pytest.Config) -> ArtifactManager:
    return pytestconfig.artifact_manager


@pytest.fixture(scope="session")
def framework_config(pytestconfig: pytest.Config) -> FrameworkConfig:
    screenshot_flag = pytestconfig.getoption("--capture-screenshot")
    video_flag = pytestconfig.getoption("--capture-video")
    trace_flag = pytestconfig.getoption("--capture-trace")
    screenshot = None if screenshot_flag is None else screenshot_flag == "on"
    video = None if video_flag is None else video_flag == "on"
    trace = None if trace_flag is None else trace_flag == "on"
    config = load_config(
        env=pytestconfig.getoption("--target-env"),
        browser=pytestconfig.getoption("--target-browser"),
        base_url=pytestconfig.getoption("--app-url"),
        headed=pytestconfig.getoption("--run-headed"),
        slow_mo=pytestconfig.getoption("--action-slowmo"),
        screenshot=screenshot,
        video=video,
        trace=trace,
    )
    if config.browser not in SUPPORTED_BROWSERS:
        supported = ", ".join(sorted(SUPPORTED_BROWSERS))
        raise pytest.UsageError(f"Unsupported browser '{config.browser}'. Supported browsers: {supported}")
    return config


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright, framework_config: FrameworkConfig) -> Generator[Browser, None, None]:
    browser_type = getattr(playwright_instance, framework_config.browser)
    logger.info(
        "Launching %s browser. Headless=%s slow_mo=%s",
        framework_config.browser,
        framework_config.headless,
        framework_config.slow_mo,
    )
    browser = browser_type.launch(headless=framework_config.headless, slow_mo=framework_config.slow_mo)
    yield browser
    browser.close()
    logger.info("Browser closed")


@pytest.fixture()
def context(
    browser: Browser,
    framework_config: FrameworkConfig,
    artifact_manager: ArtifactManager,
    request: pytest.FixtureRequest,
) -> Generator[BrowserContext, None, None]:
    record_video_dir = artifact_manager.videos_dir if framework_config.video_on_failure else None
    context = browser.new_context(
        viewport={"width": framework_config.viewport_width, "height": framework_config.viewport_height},
        locale=framework_config.locale,
        timezone_id=framework_config.timezone_id,
        ignore_https_errors=framework_config.ignore_https_errors,
        record_video_dir=record_video_dir,
    )
    request.node.context = context
    context._pytest_item = request.node
    request.node.trace_path = artifact_manager.trace_path(request.node.nodeid)

    if framework_config.trace_on_failure:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        request.node.trace_started = True

    yield context

    if getattr(request.node, "trace_started", False) and not getattr(request.node, "trace_stopped", False):
        context.tracing.stop()
    context.close()


@pytest.fixture()
def page(
    context: BrowserContext,
    request: pytest.FixtureRequest,
    framework_config: FrameworkConfig,
    artifact_manager: ArtifactManager,
) -> Generator[Page, None, None]:
    page = context.new_page()
    request.node.page = page
    request.node.browser_events = []
    if framework_config.capture_browser_logs:
        _attach_browser_event_listeners(page, request.node)

    yield page

    _write_browser_log(request.node, artifact_manager)
    _close_page_and_log_video(page, request.node)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call":
        return

    logger.info(
        "Test finished | nodeid=%s | outcome=%s | duration=%.2fs",
        item.nodeid,
        report.outcome,
        report.duration,
    )

    if not report.failed:
        return

    config: FrameworkConfig | None = item.funcargs.get("framework_config")
    artifact_manager: ArtifactManager | None = item.funcargs.get("artifact_manager")
    page: Page | None = getattr(item, "page", None)
    context: BrowserContext | None = getattr(item, "context", None)
    extras = getattr(report, "extras", [])

    if page and not page.is_closed():
        extras.extend(_page_diagnostics(page))

    if config and artifact_manager and page and config.screenshot_on_failure:
        screenshot_extra = _capture_failure_screenshot(page, item.nodeid, artifact_manager)
        if screenshot_extra:
            extras.append(screenshot_extra)

    browser_events = getattr(item, "browser_events", [])
    if browser_events:
        extras.append(pytest_html.extras.text("\n".join(browser_events), name="Browser Console And Network"))

    if config and artifact_manager and context and config.trace_on_failure:
        trace_extra = _stop_trace(context, item, artifact_manager)
        if trace_extra:
            extras.append(trace_extra)

    report.extras = extras


def pytest_runtest_setup(item: pytest.Item) -> None:
    item.test_start = perf_counter()
    markers = ",".join(marker.name for marker in item.iter_markers()) or "none"
    logger.info("Test started | nodeid=%s | markers=%s", item.nodeid, markers)


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    elapsed = perf_counter() - getattr(item, "test_start", perf_counter())
    logger.info("Test teardown complete | nodeid=%s | elapsed=%.2fs", item.nodeid, elapsed)


def _attach_browser_event_listeners(page: Page, item: pytest.Item) -> None:
    page.on("console", lambda msg: item.browser_events.append(f"console.{msg.type}: {msg.text}"))
    page.on("pageerror", lambda exc: item.browser_events.append(f"pageerror: {exc}"))
    page.on(
        "requestfailed",
        lambda request: item.browser_events.append(
            f"requestfailed: {request.method} {request.url} | {request.failure}"
        ),
    )


def _capture_failure_screenshot(page: Page, nodeid: str, artifact_manager: ArtifactManager):
    screenshot_path = artifact_manager.screenshot_path(nodeid)
    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
        screenshot_content = base64.b64encode(screenshot_path.read_bytes()).decode("utf-8")
        logger.error("Failure screenshot captured: %s", screenshot_path)
        return pytest_html.extras.png(screenshot_content, name="Failure Screenshot")
    except Exception as exc:
        logger.exception("Unable to capture failure screenshot: %s", exc)
        return pytest_html.extras.text(str(exc), name="Screenshot Capture Error")


def _stop_trace(context: BrowserContext, item: pytest.Item, artifact_manager: ArtifactManager):
    trace_path = artifact_manager.trace_path(item.nodeid)
    try:
        context.tracing.stop(path=str(trace_path))
        item.trace_stopped = True
        logger.error("Failure trace captured: %s", trace_path)
        return pytest_html.extras.url(str(trace_path), name="Playwright Trace")
    except Exception as exc:
        logger.exception("Unable to capture trace: %s", exc)
        return pytest_html.extras.text(str(exc), name="Trace Capture Error")


def _page_diagnostics(page: Page) -> list[Any]:
    diagnostics = []
    try:
        diagnostics.append(pytest_html.extras.url(page.url, name="Current URL"))
        diagnostics.append(pytest_html.extras.text(page.title(), name="Page Title"))
    except Exception as exc:
        logger.warning("Unable to collect page diagnostics: %s", exc)
    return diagnostics


def _write_browser_log(item: pytest.Item, artifact_manager: ArtifactManager) -> None:
    events = getattr(item, "browser_events", [])
    if not events:
        return
    log_path = artifact_manager.browser_log_path(item.nodeid)
    log_path.write_text("\n".join(events), encoding="utf-8")
    logger.info("Browser event log saved: %s", log_path)


def _close_page_and_log_video(page: Page, item: pytest.Item) -> None:
    video = page.video
    page.close()
    if not video:
        return
    try:
        video_path = Path(video.path())
        if not getattr(item, "rep_call", None) or not item.rep_call.failed:
            video_path.unlink(missing_ok=True)
            logger.info("Discarded passing-test video for %s", item.nodeid)
            return
        logger.info("Failure video captured for %s: %s", item.nodeid, video_path)
    except Exception as exc:
        logger.warning("Video path was not available for %s: %s", item.nodeid, exc)


def _set_report_metadata(config: pytest.Config, artifact_manager: ArtifactManager) -> None:
    metadata = {
        "Run ID": artifact_manager.run_id,
        "Artifact Directory": str(artifact_manager.run_dir),
        "Python": platform.python_version(),
        "Platform": platform.platform(),
        "Playwright": version("playwright"),
        "Pytest": version("pytest"),
    }
    try:
        from pytest_metadata.plugin import metadata_key

        config.stash[metadata_key].update(metadata)
    except Exception:
        existing = getattr(config, "_metadata", {})
        existing.update(metadata)
        config._metadata = existing
