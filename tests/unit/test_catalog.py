"""Tier 1 — Stub CDA catalog validation (no ECU needed)."""

import json
import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG_PATH = os.path.join(REPO_ROOT, "OpenBSW-SOVD-Demo/sovd-cda/catalog.json")


@pytest.fixture
def catalog():
    if not os.path.isfile(CATALOG_PATH):
        pytest.skip("catalog.json not found")
    with open(CATALOG_PATH) as f:
        return json.load(f)


@pytest.mark.unit
class TestCatalog:
    def test_catalog_loads(self, catalog):
        """Catalog JSON is valid and non-empty."""
        assert catalog is not None
        assert len(catalog) > 0

    def test_catalog_has_components(self, catalog):
        """Catalog defines at least one component."""
        # Adapt key based on actual catalog structure
        assert any(
            key in catalog
            for key in ("components", "entities", "ecus", "data")
        ), f"Catalog keys: {list(catalog.keys())}"
