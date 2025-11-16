# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# tests/conftest.py
"""
Central configuration file for the pytest framework.

This file defines shared fixtures, hooks, and plugins that are available to all
test modules within the 'tests/' directory and its subdirectories.

Key functionalities provided by this file:
1.  A session-scoped fixture to capture all outgoing Telegram API calls.
2.  Automatic mocking of the Telegram channel functions to prevent real API
    calls during tests.
"""

from typing import Any, Dict, Generator, List, Optional

import pytest

from src.channels import telegram_channel

# ============================================================================
# Shared State for Capturing Telegram Calls
# ============================================================================

# A global list to store details of every call made to the mocked Telegram
# functions during a test session. This list is cleared before each test
# by the `telegram_mocker` fixture.
captured_telegram_calls: List[Dict[str, Any]] = []


# ============================================================================
# Mocked Telegram Functions
# ============================================================================

def _mock_send_message(chat_id: str, text: str) -> bool:
    """
    A mock replacement for the real telegram_channel.send_message function.

    Instead of sending an HTTP request, this function appends the call's
    arguments to the `captured_telegram_calls` list for later inspection.

    Args:
        chat_id (str): The target chat ID.
        text (str): The message content.

    Returns:
        bool: Always returns True to simulate a successful API call.
    """
    captured_telegram_calls.append(
        {"type": "message", "chat_id": chat_id, "text": text}
    )
    return True


def _mock_send_photo(
    chat_id: str, photo_url: str, caption: Optional[str] = None
) -> bool:
    """
    A mock replacement for the real telegram_channel.send_photo function.

    Instead of sending an HTTP request, this function appends the call's
    arguments to the `captured_telegram_calls` list for later inspection.

    Args:
        chat_id (str): The target chat ID.
        photo_url (str): The URL of the photo.
        caption (Optional[str]): The caption for the photo.

    Returns:
        bool: Always returns True to simulate a successful API call.
    """
    captured_telegram_calls.append(
        {
            "type": "photo",
            "chat_id": chat_id,
            "photo_url": photo_url,
            "caption": caption,
        }
    )
    return True


# ============================================================================
# Core Pytest Fixture
# ============================================================================

@pytest.fixture(autouse=True)
def telegram_mocker(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    A pytest fixture that automatically mocks Telegram channel functions.

    This fixture is marked with `autouse=True`, so it will be activated for
    every test function without needing to be explicitly requested. It ensures
    that no real network calls are made to the Telegram API during testing.

    It replaces the real `send_message` and `send_photo` functions with mock
    versions that capture their arguments into the `captured_telegram_calls` list.
    The list is automatically cleared before each test run.

    Args:
        monkeypatch (pytest.MonkeyPatch): The pytest fixture for modifying classes,
            methods, or functions at runtime.

    Yields:
        Generator[List[Dict[str, Any]], None, None]: Yields the (empty) list that
        will be used to capture calls during the test.
    """
    # Setup: Clear any calls from previous tests
    captured_telegram_calls.clear()

    # Apply the patches to the telegram_channel module
    monkeypatch.setattr(telegram_channel, "send_message", _mock_send_message)
    monkeypatch.setattr(telegram_channel, "send_photo", _mock_send_photo)

    # Yield control to the test function. The test will run at this point.
    yield captured_telegram_calls

    # Teardown: Clear the list again after the test is done.
    captured_telegram_calls.clear()


# End of tests/conftest.py (v. 0001)