# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# tests/integration_tests/test_llm_static_handler.py
"""
Unit tests for the logical steps within the 'LLMStaticBaseHandler' pipeline,
parameterized to cover all related themes.
"""

import io
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.handlers._base.llm_static_base import LLMStaticBaseHandler
from src.handlers.llm.bible_handler import BibleHandler
from src.handlers.llm.bible_study_handler import BibleStudyHandler
from src.handlers.llm.philosophy_handler import PhilosophyHandler

# ============================================================================
# Mock Data Constants
# ============================================================================

MOCK_LLM_RESPONSE = "<b>Mockovaný LLM text</b>"
MOCK_IMAGE_URL = "https://fake-images.com/test_image.jpg"
MOCK_IMAGE_ATTRIBUTION = "<i>Photo by Mock Author on Unsplash</i>"
MOCK_AI_LINKS = "Skopíruj text a diskutuj s AI:..."

# ============================================================================
# Test Scenarios using pytest.mark.parametrize
# ============================================================================

TEST_SCENARIOS = [
    ("bible_sk", BibleHandler, {"verse_reference": "Žalm 23,1"}),
    (
        "philosophy_mix",
        PhilosophyHandler,
        {"verse_reference": "Myšlienka", "theme": "Filozof", "paradox": "Paradox"},
    ),
    ("novy_zakon_sk", BibleStudyHandler, {"verse_reference": "Matúš 5,3"}),
    ("stary_zakon_sk", BibleStudyHandler, {"verse_reference": "Genezis 1,1"}),
]


# Defines test scenarios for each theme that uses the LLMStaticBaseHandler.
@pytest.mark.parametrize("theme_name, handler_class, mock_sheet_data", TEST_SCENARIOS)
class TestLLMStaticPipelineSteps:
    """
    Tests the individual logical steps of the `LLMStaticBaseHandler` pipeline.

    This test class is parameterized to run the same set of tests against
    different handler configurations, ensuring consistent behavior across
    various themes.
    """

    # Fixture: Provides a minimal theme configuration for the current test.
    @pytest.fixture
    def theme_config(self, theme_name: str, handler_class: Any) -> Dict[str, Any]:
        """
        Provides a minimal, consistent theme configuration for the current test.

        Args:
            theme_name (str): The name of the theme for which to create the config.
            handler_class (Any): The handler class to be used in the configuration.

        Returns:
            Dict[str, Any]: A dictionary with the theme configuration.
        """
        return {
            "handler_class": handler_class.__name__,
            "data_source": {"spreadsheet_key": "fake_key", "worksheet_key": "fake_ws"},
            "dynamic_image": {"provider": "unsplash"},
            "prompts": {"slovak": f"fake/{theme_name}.txt"},
        }

    # Fixture: Provides a clean handler instance for each test.
    @pytest.fixture
    def handler_instance(self, handler_class: Any, theme_config: Dict[str, Any]) -> Any:
        """
        Provides a clean instance of a handler for each test.

        Args:
            handler_class (Any): The handler class to be instantiated.
            theme_config (Dict[str, Any]): The theme configuration for the handler.

        Returns:
            Any: A configured handler instance ready for testing.
        """
        return handler_class(theme_config=theme_config, lang="slovak")

    def test_step_1_fetch_image_data(
        self,
        handler_instance: LLMStaticBaseHandler,
        monkeypatch: pytest.MonkeyPatch,
        theme_name: str,
        handler_class: Any,
        mock_sheet_data: Dict[str, Any],
    ) -> None:
        """
        Tests the `_fetch_image_data` step in isolation for the current theme.

        Args:
            handler_instance (LLMStaticBaseHandler): The handler instance to be tested.
            monkeypatch (pytest.MonkeyPatch): The pytest fixture for modifying behavior.
            theme_name (str): The parametrized theme name (unused).
            handler_class (Any): The parametrized handler class (unused).
            mock_sheet_data (Dict[str, Any]): The parametrized sheet data (unused).
        """
        mock_image_service = MagicMock(
            return_value={
                "image_url": MOCK_IMAGE_URL,
                "attribution_html": MOCK_IMAGE_ATTRIBUTION,
            }
        )
        monkeypatch.setattr(
            "src.handlers._base.llm_static_base.image_service.get_dynamic_image",
            mock_image_service,
        )

        handler_instance._fetch_image_data()

        mock_image_service.assert_called_once()
        assert handler_instance.image_url == MOCK_IMAGE_URL
        assert handler_instance.image_attribution == MOCK_IMAGE_ATTRIBUTION

    # Mocks: the built-in open function to prevent file system access.
    @patch("builtins.open")
    # Mocks: the LLM service to prevent real network calls.
    @patch("src.handlers._base.llm_static_base.llm_service.call_llm")
    def test_step_2_generate_llm_text(
        self,
        mock_call_llm: MagicMock,
        mock_open: MagicMock,
        handler_instance: LLMStaticBaseHandler,
        mock_sheet_data: Dict[str, Any],
    ) -> None:
        """
        Tests the `_generate_llm_text` step in isolation for the current theme.

        Args:
            mock_call_llm (MagicMock): A mock for the `llm_service.call_llm` service.
            mock_open (MagicMock): A mock for the `open` function.
            handler_instance (LLMStaticBaseHandler): The handler instance to be tested.
            mock_sheet_data (Dict[str, Any]): The mock data for the current scenario.
        """
        handler_instance.image_attribution = MOCK_IMAGE_ATTRIBUTION

        def open_side_effect(file: Any, *args: Any, **kwargs: Any) -> io.StringIO:
            if "prompt" in str(file):
                return io.StringIO(
                    "Prompt:<blockquote>{IMAGE_ATTRIBUTION}{AI_LINKS_FOOTER}</blockquote>"
                )
            if "footer" in str(file):
                return io.StringIO(MOCK_AI_LINKS)
            return io.StringIO("")

        mock_open.side_effect = open_side_effect
        mock_call_llm.return_value = MOCK_LLM_RESPONSE

        final_text = handler_instance._generate_llm_text(mock_sheet_data)

        mock_call_llm.assert_called_once()
        assert final_text is not None
        assert final_text == MOCK_LLM_RESPONSE

    # Mocks: the entire sheets_service module for this test.
    @patch("src.handlers._base.llm_static_base.sheets_service")
    def test_step_3_process_orchestration(
        self,
        mock_sheets_service: MagicMock,
        handler_instance: LLMStaticBaseHandler,
        monkeypatch: pytest.MonkeyPatch,
        mock_sheet_data: Dict[str, Any],
    ) -> None:
        """
        Tests the `_process` method, which orchestrates the pipeline.

        Args:
            mock_sheets_service (MagicMock): A mock for the `sheets_service`.
            handler_instance (LLMStaticBaseHandler): The handler instance to be tested.
            monkeypatch (pytest.MonkeyPatch): The pytest fixture for modifying behavior.
            mock_sheet_data (Dict[str, Any]): The mock data for the current scenario.
        """
        mock_sheets_service.get_worksheet.return_value = MagicMock()
        mock_sheets_service.get_unused_item.return_value = (10, mock_sheet_data)

        monkeypatch.setattr(
            handler_instance,
            "_fetch_image_data",
            lambda: setattr(handler_instance, "image_url", MOCK_IMAGE_URL),
        )
        monkeypatch.setattr(
            handler_instance, "_generate_llm_text", lambda data: "Final complete text"
        )

        final_text, final_image_url = handler_instance._process()

        assert final_image_url == MOCK_IMAGE_URL
        assert final_text == "Final complete text"
        mock_sheets_service.mark_item_as_used.assert_called_once_with(
            mock_sheets_service.get_worksheet.return_value, 10
        )


# End of tests/integration_tests/test_llm_static_handler.py (v. 0004)
