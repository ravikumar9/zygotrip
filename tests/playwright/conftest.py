"""
Pytest configuration for end-to-end tests using Playwright
"""
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def browser_context_args():
    """Configure browser context for local HTTPS testing"""
    return {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,  # Critical for local HTTPS dev server
    }


@pytest.fixture(scope="session")
def browser_launch_args():
    """Configure browser launch arguments"""
    return {
        "headless": False,  # Always show visual browser
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-web-resources",
        ],
    }


def pytest_collection_modifyitems(config, items):
    """Configure pytest markers"""
    for item in items:
        # Mark all tests as playwright tests
        if "playwright" in str(item.fspath):
            item.add_marker(pytest.mark.playwright)
