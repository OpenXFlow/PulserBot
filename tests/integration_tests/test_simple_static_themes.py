# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# tests/integration_tests/test_simple_static_handler.py
"""
Integration tests for the individual steps of the `SimpleStaticHandler` pipeline.

These tests validate each `ProcessingStep` of the `ProcessingPipeline` in
isolation, ensuring that each step correctly modifies the `ProcessingContext`
as expected for different theme configurations.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.handlers.template.simple_static_handler import (
    DataModelBuilder,
    DataSourceValidator,
    ProcessingContext,
    SimpleStaticHandler,
    TemplateLoader,
    TextFormatter,
    UnusedItemFetcher,
    WorksheetFetcher,
)
from src.handlers.template.simple_static_models import EuropeanArtData, FamilyPhotoData

# ============================================================================
# Test Scenarios
# ============================================================================

TEST_SCENARIOS = [
    (
        "european_art",
        EuropeanArtData,
        {"title": "Mona Lisa", "art_title": "Mona Lisa"},
        True,
    ),
    ("family_photo", FamilyPhotoData, {"caption": "Vacation"}, False),
]


# Defines test scenarios for different static themes.
@pytest.mark.parametrize(
    "theme_name, data_model_class, mock_sheet_data, expects_footer", TEST_SCENARIOS
)
class TestSimpleStaticPipelineSteps:
    """Tests each `ProcessingStep` of the `SimpleStaticHandler` pipeline.

    This test class is parameterized to run the same set of tests against
    different handler configurations, ensuring consistent behavior across
    various simple static themes.

    Attributes:
        theme_name: The name of the theme being tested (e.g., 'european_art').
        data_model_class: The Pydantic model class for the theme's data.
        mock_sheet_data: Mock data representing a row from the spreadsheet.
        expects_footer: A boolean indicating if a footer should be generated.
    """

    # Fixture: Provides a theme configuration for the current scenario.
    @pytest.fixture
    def theme_config(self, theme_name: str) -> Dict[str, Any]:
        """Provides a minimal theme configuration for the current test scenario.

        Args:
            theme_name: The name of the theme for which to create the config.

        Returns:
            A dictionary with the theme configuration.
        """
        return {
            "theme_name": theme_name,
            "data_source": {"spreadsheet_key": "fake_key", "worksheet_key": "fake_ws"},
            "prompts": {"slovak": f"fake/{theme_name}.txt"},
        }

    # Fixture: Provides a clean ProcessingContext for each test.
    @pytest.fixture
    def context_instance(self, theme_config: Dict[str, Any]) -> ProcessingContext:
        """Provides a clean `ProcessingContext` for each test.

        Args:
            theme_config: The theme configuration for the current test.

        Returns:
            A new `ProcessingContext` instance for the test.
        """
        return ProcessingContext(theme_config, lang="slovak")

    def test_step_data_source_validator(
        self,
        context_instance: ProcessingContext,
        theme_name: str,  # noqa: ARG002
        data_model_class: Any,  # noqa: ARG002
        mock_sheet_data: Dict[str, Any],  # noqa: ARG002
        expects_footer: bool,  # noqa: ARG002
    ) -> None:
        """Tests the `DataSourceValidator` pipeline step.

        Verifies that the step correctly validates the theme configuration and
        populates the `data_source_ref` in the context.

        Args:
            context_instance: The `ProcessingContext` for the current test.
            theme_name: The parametrized theme name (for context).
            data_model_class: The parametrized data model class (for context).
            mock_sheet_data: The parametrized mock sheet data (for context).
            expects_footer: The parametrized footer expectation (for context).
        """
        step = DataSourceValidator()
        print(f"\n[TEST] Validator for: {context_instance.theme_name}")
        result = step.execute(context_instance)
        assert result is True
        assert context_instance.data_source_ref is not None

    # Mocks the `get_worksheet` function from the sheets service.
    @patch("src.handlers.template.simple_static_handler.sheets_service.get_worksheet")
    def test_step_worksheet_fetcher(
        self,
        mock_get_worksheet: MagicMock,
        context_instance: ProcessingContext,
        theme_name: str,  # noqa: ARG002
        data_model_class: Any,  # noqa: ARG002
        mock_sheet_data: Dict[str, Any],  # noqa: ARG002
        expects_footer: bool,  # noqa: ARG002
    ) -> None:
        """Tests the `WorksheetFetcher` pipeline step.

        Verifies that the step correctly calls the sheets service to get a
        worksheet and stores it in the context.

        Args:
            mock_get_worksheet: A mock for the `sheets_service.get_worksheet` function.
            context_instance: The `ProcessingContext` for the current test.
            theme_name: The parametrized theme name (for context).
            data_model_class: The parametrized data model class (for context).
            mock_sheet_data: The parametrized mock sheet data (for context).
            expects_footer: The parametrized footer expectation (for context).
        """
        mock_get_worksheet.return_value = MagicMock()
        context_instance.data_source_ref = {
            "spreadsheet_key": "key",
            "worksheet_key": "ws",
        }
        step = WorksheetFetcher()
        print(f"\n[TEST] WorksheetFetcher for: {context_instance.theme_name}")
        result = step.execute(context_instance)
        assert result is True
        assert context_instance.worksheet is not None

    # Mocks the `get_unused_item` function from the sheets service.
    @patch("src.handlers.template.simple_static_handler.sheets_service.get_unused_item")
    def test_step_unused_item_fetcher(
        self,
        mock_get_item: MagicMock,
        context_instance: ProcessingContext,
        mock_sheet_data: Dict[str, Any],
        theme_name: str,  # noqa: ARG002
        data_model_class: Any,  # noqa: ARG002
        expects_footer: bool,  # noqa: ARG002
    ) -> None:
        """Tests the `UnusedItemFetcher` pipeline step.

        Verifies that the step correctly calls the sheets service to get an
        unused item and populates the context with the row index and item data.

        Args:
            mock_get_item: A mock for the `sheets_service.get_unused_item` function.
            context_instance: The `ProcessingContext` for the current test.
            mock_sheet_data: The parametrized mock sheet data to be returned by the mock.
            theme_name: The parametrized theme name (for context).
            data_model_class: The parametrized data model class (for context).
            expects_footer: The parametrized footer expectation (for context).
        """
        mock_get_item.return_value = (5, mock_sheet_data)
        context_instance.worksheet = MagicMock()
        step = UnusedItemFetcher()
        print(f"\n[TEST] UnusedItemFetcher for: {context_instance.theme_name}")
        result = step.execute(context_instance)
        assert result is True
        assert context_instance.row_index == 5
        assert context_instance.item_data == mock_sheet_data

    def test_step_data_model_builder(
        self,
        context_instance: ProcessingContext,
        data_model_class: Any,
        mock_sheet_data: Dict[str, Any],
        theme_name: str,  # noqa: ARG002
        expects_footer: bool,  # noqa: ARG002
    ) -> None:
        """Tests the `DataModelBuilder` pipeline step.

        Verifies that the step correctly initializes a Pydantic data model
        from the item data and stores it in the context.

        Args:
            context_instance: The `ProcessingContext` for the current test.
            data_model_class: The Pydantic model class to be instantiated.
            mock_sheet_data: The item data to build the model from.
            theme_name: The parametrized theme name (for context).
            expects_footer: The parametrized footer expectation (for context).
        """
        context_instance.item_data = mock_sheet_data
        step = DataModelBuilder()
        print(f"\n[TEST] DataModelBuilder for: {context_instance.theme_name}")
        result = step.execute(context_instance)
        assert result is True
        assert isinstance(context_instance.data_model, data_model_class)

    # Mocks the `read_text` method of the `Path` object.
    @patch("src.handlers.template.simple_static_handler.Path.read_text")
    def test_step_template_loader(
        self,
        mock_read_text: MagicMock,
        context_instance: ProcessingContext,
        theme_name: str,  # noqa: ARG002
        data_model_class: Any,  # noqa: ARG002
        mock_sheet_data: Dict[str, Any],  # noqa: ARG002
        expects_footer: bool,  # noqa: ARG002
    ) -> None:
        """Tests the `TemplateLoader` pipeline step.

        Verifies that the step correctly reads the template file content
        and stores it in the context.

        Args:
            mock_read_text: A mock for the `Path.read_text` method.
            context_instance: The `ProcessingContext` for the current test.
            theme_name: The parametrized theme name (for context).
            data_model_class: The parametrized data model class (for context).
            mock_sheet_data: The parametrized mock sheet data (for context).
            expects_footer: The parametrized footer expectation (for context).
        """
        mock_read_text.return_value = "Template content"
        step = TemplateLoader()
        print(f"\n[TEST] TemplateLoader for: {context_instance.theme_name}")
        result = step.execute(context_instance)
        assert result is True
        assert context_instance.template_content == "Template content"

    # Mocks the `build_placeholders` method of the `FooterBuilder`.
    @patch(
        "src.handlers.template.simple_static_handler.FooterBuilder.build_placeholders"
    )
    def test_step_text_formatter(
        self,
        mock_build_footer: MagicMock,
        context_instance: ProcessingContext,
        data_model_class: Any,
        mock_sheet_data: Dict[str, Any],
        expects_footer: bool,
        theme_name: str,  # noqa: ARG002
    ) -> None:
        """Tests the `TextFormatter` step, including footer logic.

        Verifies that the step correctly formats the final text by combining
        the template, data model, and footer placeholders.

        Args:
            mock_build_footer: A mock for the `FooterBuilder.build_placeholders` method.
            context_instance: The `ProcessingContext` for the current test.
            data_model_class: The Pydantic model class for the theme's data.
            mock_sheet_data: The item data to build the model from.
            expects_footer: A boolean indicating if a footer should be generated.
            theme_name: The parametrized theme name (for context).
        """
        mock_build_footer.return_value = {
            "AI_LINKS_FOOTER": "AI_LINKS_CONTENT" if expects_footer else ""
        }
        context_instance.data_model = data_model_class.from_dict(mock_sheet_data)

        if context_instance.theme_name == "european_art":
            context_instance.template_content = "Art: {art_title}{AI_LINKS_FOOTER}"
        else:
            context_instance.template_content = "Photo: {caption}{AI_LINKS_FOOTER}"

        step = TextFormatter()
        print(
            f"\n[TEST] Formatter for: {context_instance.theme_name}, expects_footer={expects_footer}"
        )
        result = step.execute(context_instance)
        print(f"[TEST] Formatter result: '{context_instance.final_text}'")

        assert result is True
        assert context_instance.final_text is not None
        if expects_footer:
            assert "AI_LINKS_CONTENT" in context_instance.final_text
        else:
            assert "AI_LINKS_CONTENT" not in context_instance.final_text

    # Mocks the `run` method of the `ProcessingPipeline`.
    @patch("src.handlers.template.simple_static_handler.ProcessingPipeline.run")
    def test_orchestration_process_method(
        self,
        mock_pipeline_run: MagicMock,
        theme_config: Dict[str, Any],
        theme_name: str,  # noqa: ARG002
        data_model_class: Any,  # noqa: ARG002
        mock_sheet_data: Dict[str, Any],  # noqa: ARG002
        expects_footer: bool,  # noqa: ARG002
    ) -> None:
        """Tests that the main `_process` method correctly orchestrates the pipeline.

        This is a higher-level test that ensures the handler's `_process` method
        correctly invokes the pipeline and returns its results.

        Args:
            mock_pipeline_run: A mock for the `ProcessingPipeline.run` method.
            theme_config: The theme configuration for the handler.
            theme_name: The parametrized theme name (for context).
            data_model_class: The parametrized data model class (for context).
            mock_sheet_data: The parametrized mock sheet data (for context).
            expects_footer: The parametrized footer expectation (for context).
        """

        def pipeline_side_effect(context: ProcessingContext) -> bool:
            """Simulates the pipeline populating the context instance.

            Args:
                context: The `ProcessingContext` instance being processed.

            Returns:
                True to indicate a successful pipeline run.
            """
            print(
                f"\n[SIDE_EFFECT] Simulating successful pipeline run for {context.theme_name}"
            )
            context.final_text, context.image_url = "Success", "https://success.url"
            return True

        mock_pipeline_run.side_effect = pipeline_side_effect

        handler = SimpleStaticHandler(theme_config, lang="slovak")
        print(f"\n[TEST] Orchestration for: {handler.theme_config.get('theme_name')}")
        final_text, final_image_url = handler._process()

        mock_pipeline_run.assert_called_once()
        assert final_text == "Success"
        assert final_image_url == "https://success.url"


# End of tests/integration_tests/test_simple_static_handler.py (v. 0007)
