"""Pytest configuration."""
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_package():
    """Set up testing package."""
    import matplotlib

    """Set Agg matplotlib backend for this module."""
    matplotlib.use("Agg", force=True)
    yield
