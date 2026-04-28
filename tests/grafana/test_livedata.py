"""Grafana live data visual tests — sensor values changing in browser.

Opens dashboards in a headless browser and verifies that sensor values
are actually updating (not static/stale). Takes before/after screenshots
for visual evidence.

Covers: TEST_RG8_001, TEST_RG8_002
"""

import os
import time

import pytest

from .conftest import (
    GRAFANA_URL,
    REAL_DASHBOARD_UID,
    SCREENSHOT_DIR,
    STUB_DASHBOARD_UID,
    wait_for_panels_loaded,
)


@pytest.mark.grafana
class TestLiveDataRendering:
    def _get_visible_text(self, page):
        """Extract all visible text content from the dashboard."""
        return page.evaluate("() => document.body.innerText")

    def _get_panel_values(self, page):
        """Extract numeric values displayed in gauge/stat panels."""
        # Grafana renders values in various elements; grab all visible numbers
        return page.evaluate("""() => {
            const values = [];
            // Gauge and stat panels render values in specific elements
            const selectors = [
                '[class*="gauge-value"]',
                '[class*="singlestat-panel-value"]',
                '[data-testid*="value"]',
                '.css-1frfmkf',  // Grafana gauge value class
            ];
            for (const sel of selectors) {
                for (const el of document.querySelectorAll(sel)) {
                    const text = el.innerText.trim();
                    if (text && /[\\d.]+/.test(text)) {
                        values.push(text);
                    }
                }
            }
            // Fallback: find all large numbers on the page (gauge renders)
            if (values.length === 0) {
                const all = document.body.innerText;
                const matches = all.match(/\\b\\d{1,3}(\\.\\d+)?\\s*(°C|V|km\\/h|%)/g);
                if (matches) values.push(...matches);
            }
            return values;
        }""")

    def test_sensor_values_change_real_cda(self, grafana_page):
        """TEST_RG8_001: Sensor values in real CDA dashboard change over time."""
        grafana_page.goto(
            f"{GRAFANA_URL}/d/{REAL_DASHBOARD_UID}?orgId=1&refresh=5s",
            wait_until="networkidle",
            timeout=30000,
        )
        wait_for_panels_loaded(grafana_page, timeout=30)

        # Capture first snapshot
        text_before = self._get_visible_text(grafana_page)
        grafana_page.screenshot(
            path=os.path.join(SCREENSHOT_DIR, "livedata-before.png"),
            full_page=True,
        )

        # Wait for data to refresh (Grafana refresh interval is 5s)
        time.sleep(8)

        # Force panel refresh by reloading
        grafana_page.reload(wait_until="networkidle", timeout=20000)
        wait_for_panels_loaded(grafana_page, timeout=30)

        text_after = self._get_visible_text(grafana_page)
        grafana_page.screenshot(
            path=os.path.join(SCREENSHOT_DIR, "livedata-after.png"),
            full_page=True,
        )

        # The full page text should differ between snapshots
        # (sensor values change via random walk)
        assert text_before != text_after, (
            "Dashboard content identical after 8 seconds — "
            "sensor values may be static/stale"
        )

    def test_sensor_values_change_stub_cda(self, grafana_page):
        """TEST_RG8_005: Sensor values in stub CDA dashboard change over time."""
        grafana_page.goto(
            f"{GRAFANA_URL}/d/{STUB_DASHBOARD_UID}?orgId=1&refresh=5s",
            wait_until="networkidle",
            timeout=30000,
        )
        wait_for_panels_loaded(grafana_page, timeout=30)

        text_before = self._get_visible_text(grafana_page)
        grafana_page.screenshot(
            path=os.path.join(SCREENSHOT_DIR, "stub-livedata-before.png"),
            full_page=True,
        )

        time.sleep(8)

        grafana_page.reload(wait_until="networkidle", timeout=20000)
        wait_for_panels_loaded(grafana_page, timeout=30)

        text_after = self._get_visible_text(grafana_page)
        grafana_page.screenshot(
            path=os.path.join(SCREENSHOT_DIR, "stub-livedata-after.png"),
            full_page=True,
        )

        assert text_before != text_after, (
            "Stub dashboard content identical after 8 seconds — "
            "sensor values may be static/stale"
        )

    def test_dtc_table_has_rows(self, grafana_page):
        """TEST_RG8_002: DTC Status Board table renders rows with fault data."""
        grafana_page.goto(
            f"{GRAFANA_URL}/d/{REAL_DASHBOARD_UID}?orgId=1",
            wait_until="networkidle",
            timeout=30000,
        )
        wait_for_panels_loaded(grafana_page, timeout=30)

        grafana_page.screenshot(
            path=os.path.join(SCREENSHOT_DIR, "dtc-table.png"),
            full_page=True,
        )

        # Look for table rows in the rendered page
        table_rows = grafana_page.query_selector_all("table tbody tr")
        if not table_rows:
            # Grafana 10+ may use different table rendering
            table_rows = grafana_page.query_selector_all(
                '[data-testid*="table"] [role="row"]'
            )

        # The page text should contain DTC-related content
        content = grafana_page.content().lower()
        has_dtc_content = any(
            term in content
            for term in ["0x01", "overtemp", "battery", "fault", "brake", "sensor"]
        )

        assert len(table_rows) > 0 or has_dtc_content, (
            "DTC Status Board table has no visible rows or fault data"
        )

    def test_screenshot_visual_baseline(self, grafana_page):
        """Capture full dashboard screenshots for manual visual review."""
        for uid, name in [
            (REAL_DASHBOARD_UID, "baseline-real"),
            (STUB_DASHBOARD_UID, "baseline-stub"),
        ]:
            grafana_page.goto(
                f"{GRAFANA_URL}/d/{uid}?orgId=1",
                wait_until="networkidle",
                timeout=30000,
            )
            wait_for_panels_loaded(grafana_page, timeout=30)
            path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
            grafana_page.screenshot(path=path, full_page=True)
            assert os.path.isfile(path), f"Screenshot not saved: {path}"
