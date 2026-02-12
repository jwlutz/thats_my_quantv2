"""
Pytest configuration for options_pricer tests.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "live: tests that require live market data (skipped by default)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip live tests by default unless -m live is specified."""
    if config.getoption("-m") != "live":
        skip_live = pytest.mark.skip(reason="need -m live option to run")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)