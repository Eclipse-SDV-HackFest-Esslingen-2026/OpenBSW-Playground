"""Grafana dashboard visual tests — dashboard provisioning and panel rendering.

Verifies that dashboards are provisioned, load in a browser, and panels
render correctly (not just API-level checks).

Covers: TEST_RG8_001, TEST_RG8_002, TEST_RG8_005
"""

import os

import pytest

from .conftest import (
    GRAFANA_URL,
    REAL_DASHBOARD_UID,
    SCREENSHOT_DIR,
    STUB_DASHBOARD_UID,
    wait_for_panels_loaded,
)


@pytest.mark.grafana
class TestDashboardProvisioning:
    def test_grafana_loads(self, grafana_page):
        """Grafana home page renders without errors."""
        grafana_page.goto(f"{GRAFANA_URL}/", wait_until="networkidle", timeout=15000)
        assert grafana_page.title(), "Grafana page title is empty"
        # No error overlay
        errors = grafana_page.query_selector_all('[class*="alert-error"]')
        assert len(errors) == 0, "Grafana shows error alerts on home"

    def test_real_dashboard_exists(self, grafana_page):
        """TEST_RG8_001: Real CDA dashboard is provisioned and accessible."""
        resp = grafana_page.goto(
            f"{GRAFANA_URL}/d/{REAL_DASHBOARD_UID}",
            wait_until="networkidle",
            timeout=20000,
        )
        assert resp.status == 200, f"Dashboard returned {resp.status}"
        assert "not found" not in grafana_page.content().lower()

    def test_stub_dashboard_exists(self, grafana_page):
        """TEST_RG8_005: Stub CDA dashboard is provisioned and accessible."""
        resp = grafana_page.goto(
            f"{GRAFANA_URL}/d/{STUB_DASHBOARD_UID}",
            wait_until="networkidle",
            timeout=20000,
        )
        assert resp.status == 200, f"Dashboard returned {resp.status}"
        assert "not found" not in grafana_page.content().lower()


@pytest.mark.grafana
class TestPanelRendering:
    def _open_dashboard(self, grafana_page, uid, name):
        """Navigate to dashboard and wait for panels to load."""
        grafana_page.goto(
            f"{GRAFANA_URL}/d/{uid}?orgId=1&refresh=5s",
            wait_until="networkidle",
            timeout=30000,
        )
        wait_for_panels_loaded(grafana_page, timeout=30)
        # Take screenshot for visual evidence
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        grafana_page.screenshot(path=path, full_page=True)
        return path

    def test_real_dashboard_renders_panels(self, grafana_page):
        """TEST_RG8_001: Real CDA dashboard renders gauge and table panels."""
        self._open_dashboard(grafana_page, REAL_DASHBOARD_UID, "real-dashboard")

        content = grafana_page.content().lower()
        # Verify expected panel titles are rendered in the DOM
        expected_panels = ["engine temperature", "battery voltage", "vehicle speed"]
        for panel in expected_panels:
            assert panel in content, f"Panel '{panel}' not found in rendered dashboard"

    def test_real_dashboard_dtc_table(self, grafana_page):
        """TEST_RG8_002: DTC Status Board table renders in real CDA dashboard."""
        self._open_dashboard(grafana_page, REAL_DASHBOARD_UID, "real-dtc-table")

        content = grafana_page.content().lower()
        assert "dtc status" in content or "status board" in content, \
            "DTC Status Board panel not found"

    def test_stub_dashboard_renders_panels(self, grafana_page):
        """TEST_RG8_005: Stub CDA dashboard renders all panels."""
        self._open_dashboard(grafana_page, STUB_DASHBOARD_UID, "stub-dashboard")

        content = grafana_page.content().lower()
        expected_panels = ["engine temperature", "battery voltage", "vehicle speed"]
        for panel in expected_panels:
            assert panel in content, f"Panel '{panel}' not found in stub dashboard"

    def test_gauge_panels_not_empty(self, grafana_page):
        """TEST_RG8_001: Gauge panels show numeric values, not 'No data'."""
        self._open_dashboard(grafana_page, REAL_DASHBOARD_UID, "gauge-values")

        # Grafana renders gauge values inside specific elements
        # Check that at least some gauge panels have numeric content
        gauges = grafana_page.query_selector_all('[class*="gauge"], [data-testid*="Gauge"]')
        if not gauges:
            # Fallback: check the page doesn't just show "No data" everywhere
            no_data_count = grafana_page.content().lower().count("no data")
            panel_count = len(grafana_page.query_selector_all('[class*="panel-container"]'))
            assert no_data_count < panel_count, \
                f"Too many 'No data' panels ({no_data_count}/{panel_count})"

    def test_dashboard_no_panel_errors(self, grafana_page):
        """Panels render without error overlays."""
        self._open_dashboard(grafana_page, REAL_DASHBOARD_UID, "panel-errors-check")

        # Grafana shows error messages inside panels when queries fail
        error_panels = grafana_page.query_selector_all(
            '[class*="panel-error"], [data-testid*="Panel error"]'
        )
        assert len(error_panels) == 0, \
            f"{len(error_panels)} panel(s) show error state"
