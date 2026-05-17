from pathlib import Path

from playwright.sync_api import Locator, Page, expect

from utils.logger import get_logger


class BasePage:
    def __init__(self, page: Page, timeout: int = 10000):
        self.page = page
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)
        self.page.set_default_timeout(timeout)

    def open(self, url: str) -> None:
        self.logger.info("Opening URL: %s", url)
        self.page.goto(url, wait_until="domcontentloaded")

    def locator(self, selector: str) -> Locator:
        return self.page.locator(selector)

    def click(self, selector: str) -> None:
        target = self.locator(selector)
        expect(target).to_be_visible(timeout=self.timeout)
        target.click()

    def fill(self, selector: str, value: str) -> None:
        target = self.locator(selector)
        expect(target).to_be_editable(timeout=self.timeout)
        target.fill(value)

    def select_option(self, selector: str, value: str) -> None:
        target = self.locator(selector)
        expect(target).to_be_visible(timeout=self.timeout)
        target.select_option(value)

    def expect_visible(self, selector: str) -> None:
        expect(self.locator(selector).first).to_be_visible(timeout=self.timeout)

    def expect_text_contains(self, selector: str, text: str) -> None:
        expect(self.locator(selector)).to_contain_text(text, timeout=self.timeout)

    def screenshot(self, path: str | Path, full_page: bool = True) -> Path:
        screenshot_path = Path(path)
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(screenshot_path), full_page=full_page)
        self.logger.info("Screenshot saved: %s", screenshot_path)
        return screenshot_path
