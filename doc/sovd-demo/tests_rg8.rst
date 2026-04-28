RG-8 Tests — Observability & Dashboard
=======================================

Test cases for monitoring and visualization.
Visual rendering verified via Playwright headless browser tests.

.. contents::
   :local:
   :depth: 1

.. test:: Grafana displays live sensor data (real CDA)
   :id: TEST_RG8_001
   :status: done
   :tags: rg8, grafana, observability, visual
   :tests: REQ_RG8_001

   Playwright opens Grafana dashboard (UID ``openbsw-sovd-demo``) in a headless
   browser. Verifies gauge panels for EngineTemp, BatteryVoltage, VehicleSpeed
   render with numeric values (not "No data"). Polls twice with 8s interval to
   confirm values are changing (not static/stale). Takes before/after screenshots.

   Executable: ``tests/grafana/test_dashboard.py::TestPanelRendering``,
   ``tests/grafana/test_livedata.py::TestLiveDataRendering::test_sensor_values_change_real_cda``

.. test:: Grafana displays active faults (real CDA)
   :id: TEST_RG8_002
   :status: done
   :tags: rg8, grafana, observability, visual
   :tests: REQ_RG8_002

   Playwright verifies the DTC Status Board table panel renders in the browser
   with visible fault rows. Checks for DTC-related content (codes, names,
   status) in the rendered DOM.

   Executable: ``tests/grafana/test_dashboard.py::TestPanelRendering::test_real_dashboard_dtc_table``,
   ``tests/grafana/test_livedata.py::TestLiveDataRendering::test_dtc_table_has_rows``

.. test:: Status dashboard shows system health
   :id: TEST_RG8_003
   :status: manual
   :tags: rg8, observability
   :tests: REQ_RG8_003

   Run ``demo.sh --status``. Verify ASCII output shows ECU, CDA, DoIP, and
   Grafana health status with colour coding. Verify auto-detection of CDA mode.
   Reference: ``demo.sh show_status_once()``.

.. test:: Log file captures ECU and CDA output
   :id: TEST_RG8_004
   :status: manual
   :tags: rg8, observability, logging
   :tests: REQ_RG8_004

   Start demo. Verify ``/tmp/openbsw-demo.log`` is created. Verify it contains
   both ECU and CDA output lines. Verify log is appended, not overwritten.

.. test:: Separate Grafana dashboard for stub CDA
   :id: TEST_RG8_005
   :status: done
   :tags: rg8, grafana, observability, visual
   :tests: REQ_RG8_005

   Playwright opens the stub CDA dashboard (UID ``openbsw-stub-cda``) in a
   headless browser. Verifies panels render, sensor values display, and values
   change over time. Takes screenshots for visual evidence.

   Executable: ``tests/grafana/test_dashboard.py::TestDashboardProvisioning::test_stub_dashboard_exists``,
   ``tests/grafana/test_dashboard.py::TestPanelRendering::test_stub_dashboard_renders_panels``,
   ``tests/grafana/test_livedata.py::TestLiveDataRendering::test_sensor_values_change_stub_cda``
