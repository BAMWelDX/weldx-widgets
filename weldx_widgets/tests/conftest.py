"""Pytest configuration."""
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_package():
    """Set up testing package."""
    import matplotlib as mpl

    """Set Agg matplotlib backend for this module."""
    mpl.use("Agg", force=True)
    yield
