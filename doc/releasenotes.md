# Release Notes

## v1.0.0 — 2026-04-21

**Quality Infrastructure Release**

First release establishing the syspilot requirements engineering and quality
infrastructure for the OpenBSW-Playground project.

### Added

- **syspilot Framework** — 12 agents, 4 skills, 11 prompts, templates, scripts
- **Sphinx + sphinx-needs** — Documentation framework with 4 need types
  (REQ, SPEC, IMPL, TEST)
- **139 traceability elements** — 100% linked, 0 orphans
  - 61 requirements (REQ\_RG1–RG8) converted from markdown
  - 8 architecture specifications (SPEC\_ARCH\_\*)
  - 10 implementation links (IMPL\_\*)
  - 60 test definitions (TEST\_\*) with automated/manual status
- **Traceability views** — needtable and needflow visualizations
- **CI Pipelines** — 3 GitHub Actions workflows
  - `build.yml` — CMake build of SOVD Demo ECU
  - `docs.yml` — Sphinx build (warnings-as-errors) + needs.json validation
  - `test.yml` — 4-tier test pyramid (unit → ECU → SOVD → Grafana visual)
- **Executable test suite** — 18 test files
  - Tier 1: 7 unit tests (catalog validation, UDS protocol helpers)
  - Tier 2: 10 ECU integration test files (DoIP, sessions, RDBI/WDBI, DTC)
  - Tier 3: 4 SOVD API test files (health, components, faults, data)
  - Tier 4: 2 Grafana visual test files (Playwright dashboard rendering)

### Fixed

- `.gitignore` pattern blocking `doc/sovd-demo/` from git tracking
- Missing `openbsw` entry in `.gitmodules`

### Removed

- Obsolete SOME/IP analysis files (AUTOSAR\_SOMEIP\_SOURCES.md, etc.)

### Validation

- `sphinx-build -W`: zero warnings, zero errors
- `pytest tests/unit/`: 7/7 passing
- needs.json: 139 elements, 0 broken links, 100% coverage
