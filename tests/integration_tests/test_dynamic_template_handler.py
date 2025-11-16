# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# tests/integration_tests/test_llm_dynamic_handler.py
"""
Unit tests for the individual steps within the 'LLMDynamicHandler' pipeline.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.handlers.llm.llm_dynamic_handler import (
    DynamicContentFetcher,
    DynamicImageFetcher,
    LLMDynamicHandler,
    LLMTextGenerator,
    PromptLoader,
    StaticImageLoader,
    UserValidator,
)
from src.handlers.llm.llm_dynamic_models import MorningBriefingData

# ============================================================================
# Mock Data Constants & Fixtures
# ============================================================================

MOCK_USER = {"description": "test_user"}
MOCK_THEME_CONFIG = {
    "handler_class": "LLMDynamicHandler",
    "prompts": {"slovak": "fake/path/prompt.txt"},
    "dynamic_image": {"provider": "unsplash"},
}
MOCK_DYNAMIC_CONTENT_DATA = {"DATE": "Pondelok, 01.01.2025"}
MOCK_IMAGE_DATA = {
    "image_url": "https://fake.url/image.jpg",
    "attribution_html": "<i>Test author</i>",
}
MOCK_LLM_RESPONSE = "Mockovaný ranný prehľad."
MOCK_PROMPT_CONTENT = "Dátum: {DATE}{IMAGE_ATTRIBUTION}{AI_LINKS_FOOTER}"


# Fixture: Provides a clean handler instance for each test.
@pytest.fixture
def handler_instance() -> LLMDynamicHandler:
    """
    Provides a clean instance of the LLMDynamicHandler for each test.

    This ensures that tests are isolated and do not share state.

    Returns:
        LLMDynamicHandler: A new handler instance with mock configuration.
    """
    return LLMDynamicHandler(theme_config=MOCK_THEME_CONFIG, lang="slovak")


# ============================================================================
# Individual Step Tests
# ============================================================================


def test_step_user_validator(handler_instance: LLMDynamicHandler) -> None:
    """
    Tests that the UserValidator step correctly handles user presence.

    Args:
        handler_instance (LLMDynamicHandler): The handler instance provided by the fixture.
    """
    step = UserValidator()
    assert step.execute(handler_instance, user=MOCK_USER) is True
    assert step.execute(handler_instance, user=None) is False


def test_step_static_image_loader(handler_instance: LLMDynamicHandler) -> None:
    """
    Tests that the StaticImageLoader correctly loads a configured static URL.

    Args:
        handler_instance (LLMDynamicHandler): The handler instance provided by the fixture.
    """
    handler_instance.theme_config["static_image_url"] = "https://static.url/image.png"
    step = StaticImageLoader()
    assert step.execute(handler_instance, user=MOCK_USER) is True
    assert handler_instance.image_url == "https://static.url/image.png"


# Mocks: the image_service to prevent real network calls.
@patch("src.handlers.llm.llm_dynamic_handler.image_service.get_dynamic_image")
def test_step_dynamic_image_fetcher(
    mock_get_image: MagicMock, handler_instance: LLMDynamicHandler
) -> None:
    """
    Tests that the DynamicImageFetcher correctly calls the image service.

    Args:
        mock_get_image (MagicMock): The mocked get_dynamic_image function.
        handler_instance (LLMDynamicHandler): The handler instance provided by the fixture.
    """
    mock_get_image.return_value = MOCK_IMAGE_DATA
    step = DynamicImageFetcher()
    assert step.execute(handler_instance, user=MOCK_USER) is True
    mock_get_image.assert_called_once()
    assert handler_instance.image_url == MOCK_IMAGE_DATA["image_url"]
    assert handler_instance.image_attribution == MOCK_IMAGE_DATA["attribution_html"]


# Mocks: the dynamic_content_service to prevent real data fetching.
@patch(
    "src.handlers.llm.llm_dynamic_handler.dynamic_content_service.get_all_dynamic_data"
)
def test_step_dynamic_content_fetcher(
    mock_get_content: MagicMock, handler_instance: LLMDynamicHandler
) -> None:
    """
    Tests that the DynamicContentFetcher correctly creates the data model.

    Args:
        mock_get_content (MagicMock): The mocked get_all_dynamic_data function.
        handler_instance (LLMDynamicHandler): The handler instance provided by the fixture.
    """
    mock_get_content.return_value = MOCK_DYNAMIC_CONTENT_DATA
    step = DynamicContentFetcher()
    assert step.execute(handler_instance, user=MOCK_USER) is True
    mock_get_content.assert_called_once()
    assert isinstance(handler_instance.data_model, MorningBriefingData)
    assert handler_instance.data_model.DATE == "Pondelok, 01.01.2025"


# Mocks: the ResourceCache to prevent file system access.
@patch("src.handlers.llm.llm_dynamic_handler.ResourceCache.get_prompt")
def test_step_prompt_loader(
    mock_get_prompt: MagicMock, handler_instance: LLMDynamicHandler
) -> None:
    """
    Tests that the PromptLoader correctly retrieves the prompt template.

    Args:
        mock_get_prompt (MagicMock): The mocked ResourceCache.get_prompt method.
        handler_instance (LLMDynamicHandler): The handler instance provided by the fixture.
    """
    mock_get_prompt.return_value = MOCK_PROMPT_CONTENT
    step = PromptLoader()
    assert step.execute(handler_instance, user=MOCK_USER) is True
    mock_get_prompt.assert_called_with("fake/path/prompt.txt")
    assert handler_instance._prompt_template == MOCK_PROMPT_CONTENT


# Mocks: the LLM service to prevent real API calls.
@patch("src.handlers.llm.llm_dynamic_handler.llm_service.call_llm")
# Mocks: the PromptBuilder to isolate the LLMTextGenerator logic.
@patch("src.handlers.llm.llm_dynamic_handler.PromptBuilder.build")
def test_step_llm_text_generator(
    mock_build_prompt: MagicMock,
    mock_call_llm: MagicMock,
    handler_instance: LLMDynamicHandler,
) -> None:
    """
    Tests that the LLMTextGenerator correctly calls the LLM service.

    Args:
        mock_build_prompt (MagicMock): The mocked PromptBuilder.build method.
        mock_call_llm (MagicMock): The mocked llm_service.call_llm function.
        handler_instance (LLMDynamicHandler): The handler instance provided by the fixture.
    """
    mock_build_prompt.return_value = "Final prompt"
    mock_call_llm.return_value = MOCK_LLM_RESPONSE
    step = LLMTextGenerator()
    assert step.execute(handler_instance, user=MOCK_USER) is True
    mock_build_prompt.assert_called_once_with(handler_instance)
    mock_call_llm.assert_called_once_with("Final prompt")
    assert handler_instance._final_text == MOCK_LLM_RESPONSE


# Mocks: the pipeline's execute method to test orchestration in isolation.
@patch("src.handlers.llm.llm_dynamic_handler.DynamicProcessingPipeline.execute")
def test_orchestration_process_method(
    mock_pipeline_execute: MagicMock, handler_instance: LLMDynamicHandler
) -> None:
    """
    Tests that the main `_process` method correctly orchestrates the pipeline.

    Args:
        mock_pipeline_execute (MagicMock): The mocked pipeline's execute method.
        handler_instance (LLMDynamicHandler): The handler instance provided by the fixture.
    """

    def pipeline_side_effect(handler: LLMDynamicHandler, user: Any) -> bool:
        """A function that simulates the pipeline populating the handler."""
        handler._final_text = "Success"
        handler.image_url = "https://success.url"
        return True

    mock_pipeline_execute.side_effect = pipeline_side_effect

    final_text, final_image_url = handler_instance._process(user=MOCK_USER)

    mock_pipeline_execute.assert_called_once_with(handler_instance, MOCK_USER)
    assert final_text == "Success"
    assert final_image_url == "https://success.url"


# End of tests/integration_tests/test_llm_dynamic_handler.py (v. 0013)
