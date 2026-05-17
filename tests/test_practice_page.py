import pytest

from pages.practice_page import PracticePage
from utils.api_client import ApiClient


@pytest.mark.ui
@pytest.mark.smoke
def test_practice_page_loads(page, framework_config):
    practice = PracticePage(page, framework_config.timeout)
    practice.open(framework_config.base_url)
    practice.expect_visible(PracticePage.RADIO_BUTTONS)
    practice.expect_visible(PracticePage.SUGGESTION_BOX)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("radio_value", ["radio1", "radio2", "radio3"])
def test_user_can_select_radio_buttons(page, framework_config, radio_value):
    practice = PracticePage(page, framework_config.timeout)
    practice.open(framework_config.base_url)
    practice.choose_radio(radio_value)


@pytest.mark.ui
@pytest.mark.smoke
def test_user_can_select_suggestion_dropdown_and_checkbox(page, framework_config):
    practice = PracticePage(page, framework_config.timeout)
    practice.open(framework_config.base_url)
    practice.choose_country_suggestion("ind", "India")
    practice.select_dropdown_by_value("option2")
    practice.enable_first_checkbox()


@pytest.mark.ui
@pytest.mark.regression
def test_user_can_handle_alert_and_visibility(page, framework_config):
    practice = PracticePage(page, framework_config.timeout)
    practice.open(framework_config.base_url)
    alert_message = practice.trigger_alert_for_name("Automation Tester")
    assert "Automation Tester" in alert_message
    practice.hide_and_show_textbox()


@pytest.mark.smoke
def test_home_page_is_reachable_with_requests(framework_config):
    client = ApiClient(framework_config.base_url, timeout=framework_config.timeout // 1000)
    result = client.get()
    assert result.ok, result.error
    assert "Practice Page" in result.data
