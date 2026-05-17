import re

from playwright.sync_api import expect

from core.base_page import BasePage


class PracticePage(BasePage):
    RADIO_BUTTONS = "input[type='radio']"
    SUGGESTION_BOX = "#autocomplete"
    SUGGESTION_OPTIONS = ".ui-menu-item div"
    DROPDOWN = "#dropdown-class-example"
    CHECKBOX = "#checkBoxOption1"
    OPEN_WINDOW = "#openwindow"
    NAME_INPUT = "#name"
    ALERT_BUTTON = "#alertbtn"
    HIDE_BUTTON = "#hide-textbox"
    SHOW_BUTTON = "#show-textbox"
    DISPLAYED_TEXTBOX = "#displayed-text"

    def choose_radio(self, value: str) -> None:
        option = self.page.locator(f"input[value='{value}']")
        option.check()
        expect(option).to_be_checked()

    def choose_country_suggestion(self, search_text: str, country_name: str) -> None:
        self.fill(self.SUGGESTION_BOX, search_text)
        option = self.page.locator(self.SUGGESTION_OPTIONS).filter(
            has_text=re.compile(f"^{re.escape(country_name)}$")
        )
        expect(option).to_be_visible(timeout=self.timeout)
        option.click()
        expect(self.locator(self.SUGGESTION_BOX)).to_have_value(country_name)

    def select_dropdown_by_value(self, value: str) -> None:
        self.select_option(self.DROPDOWN, value)
        expect(self.locator(self.DROPDOWN)).to_have_value(value)

    def enable_first_checkbox(self) -> None:
        checkbox = self.locator(self.CHECKBOX)
        checkbox.check()
        expect(checkbox).to_be_checked()

    def trigger_alert_for_name(self, name: str) -> str:
        alert_message = ""

        def handle_dialog(dialog) -> None:
            nonlocal alert_message
            alert_message = dialog.message
            dialog.accept()

        self.page.once("dialog", handle_dialog)
        self.fill(self.NAME_INPUT, name)
        self.click(self.ALERT_BUTTON)
        expect(self.locator(self.NAME_INPUT)).to_be_visible()
        return alert_message

    def hide_and_show_textbox(self) -> None:
        textbox = self.locator(self.DISPLAYED_TEXTBOX)
        expect(textbox).to_be_visible()
        self.click(self.HIDE_BUTTON)
        expect(textbox).to_be_hidden()
        self.click(self.SHOW_BUTTON)
        expect(textbox).to_be_visible()
