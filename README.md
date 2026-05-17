# Pytest Playwright Hybrid Automation Framework

This is a Python UI/API hybrid automation framework using Pytest, Playwright sync APIs, Page Object Model, reusable base components, configuration management, logging, screenshot capture, and an Extent-style HTML report via `pytest-html`.

## Framework Structure

```text
config/              environment configuration
core/                BasePage and reusable browser actions
pages/               Page Object Model classes
tests/               Pytest test suites
utils/               config, logger, requests API helper
reports/             generated HTML reports
screenshots/         failure screenshots
logs/                automation logs
test_data/           test data files
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install
```

## Run Tests

```bash
python3 -m pytest
python3 -m pytest -m smoke
python3 -m pytest --target-browser chromium --run-headed --action-slowmo 300
python3 -m pytest --target-env qa --app-url https://rahulshettyacademy.com/AutomationPractice/
python3 -m pytest --capture-screenshot off
```

## Reporting

The HTML report is generated at:

```text
reports/extent_report.html
```

Failure screenshots are saved under:

```text
screenshots/
```

Logs are saved under:

```text
logs/automation.log
```

## Implemented Coverage

- Launch browser through Pytest fixtures.
- Use POM through `pages/practice_page.py`.
- Reuse synchronized actions through `core/base_page.py`.
- Select radio buttons with parametrized test data.
- Use autocomplete suggestion box.
- Select dropdown value.
- Select checkbox.
- Handle JavaScript alert.
- Hide and show textbox.
- Validate application reachability with a `requests` utility.

## IDE Import

Open this folder directly in PyCharm, VS Code, or another Python IDE. Set the interpreter to the virtual environment and run tests using Pytest.
