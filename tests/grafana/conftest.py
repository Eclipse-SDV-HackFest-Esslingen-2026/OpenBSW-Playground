"""Shared fixtures for Grafana visual rendering tests.

Uses Playwright for headless browser testing to verify dashboards
actually render panels with live data.
"""

import os
import time

import pytest

GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.environ.get("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.environ.get("GRAFANA_PASSWORD", "admin")

REAL_DASHBOARD_UID = "openbsw-sovd-demo"
STUB_DASHBOARD_UID = "openbsw-stub-cda"

SCREENSHOT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "test-results", "screenshots"
)


@pytest.fixture(scope="session")
def browser_context():
    """Create a Playwright browser context for the test session."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright not installed: pip install playwright && playwright install chromium")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture
def grafana_page(browser_context):
    """Create a new page logged into Grafana."""
    page = browser_context.new_page()

    # Login to Grafana
    page.goto(f"{GRAFANA_URL}/login", wait_until="networkidle", timeout=15000)

    # If anonymous access is enabled, we may already be logged in
    if "/login" in page.url:
        page.fill('input[name="user"]', GRAFANA_USER)
        page.fill('input[name="password"]', GRAFANA_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=10000)

    yield page
    page.close()


@pytest.fixture(scope="session", autouse=True)
def screenshot_dir():
    """Ensure screenshot directory exists."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    return SCREENSHOT_DIR


def wait_for_panels_loaded(page, timeout=30):
    """Wait until Grafana panels have finished loading (spinners gone)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        # Check for loading spinners
        spinners = page.query_selector_all('[class*="panel-loading"]')
        if not spinners:
            # Also check for "No data" which means loaded but empty
            return True
        time.sleep(1)
    return False
