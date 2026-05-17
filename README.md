# Pytest Playwright Hybrid Automation Framework

This is a Python UI/API hybrid automation framework using Pytest, Playwright sync APIs, Page Object Model, reusable base components, configuration management, logging, screenshot capture, and an Extent-style HTML report via `pytest-html`.

## Framework Structure

```text
config/              environment configuration
core/                BasePage and reusable browser actions
pages/               Page Object Model classes
tests/               Pytest test suites
utils/               config, artifacts, logger, requests API helper
artifacts/           timestamped run reports, logs, screenshots, traces, videos
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
python3 -m pytest --capture-trace on --capture-video on
python3 -m pytest --artifact-root artifacts
```

## Reporting

Each execution creates a timestamped artifact folder:

```text
artifacts/YYYYMMDD_HHMMSS/
```

The HTML report is generated at:

```text
artifacts/YYYYMMDD_HHMMSS/reports/extent_report.html
```

Logs are saved under:

```text
artifacts/YYYYMMDD_HHMMSS/logs/automation.log
```

Failure screenshots, Playwright traces, videos, and browser console/network logs are saved under:

```text
artifacts/YYYYMMDD_HHMMSS/screenshots/
artifacts/YYYYMMDD_HHMMSS/traces/
artifacts/YYYYMMDD_HHMMSS/videos/
artifacts/YYYYMMDD_HHMMSS/browser_logs/
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
- Capture screenshots, traces, browser console logs, network failures, URL, and page title on failure.
- Add run metadata to the HTML report.

## IDE Import

Open this folder directly in PyCharm, VS Code, or another Python IDE. Set the interpreter to the virtual environment and run tests using Pytest.
