# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/simple_static_handler.py
"""
Handler for the 'simple_static' theme type with optimized OOP design.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

from ...services import sheets_service
from .._base.base_handler import BaseHandler
from .simple_static_models import EuropeanArtData, FamilyPhotoData


# ============================================================================
# Configuration and Registry
# ============================================================================
class ThemeRegistry:
    """A central registry for theme-specific configurations."""

    _MODEL_MAP: Dict[str, Type[Any]] = {
        "family_photo": FamilyPhotoData,
        "family_photo_en": FamilyPhotoData,
        "european_art": EuropeanArtData,
        "european_art_en": EuropeanArtData,
    }

    _FOOTER_THEMES: set[str] = {"european_art", "european_art_en"}

    @classmethod
    def get_model_class(cls, theme_name: str) -> Optional[Type[Any]]:
        """
        Gets the data model class associated with a given theme name.
        """
        model = cls._MODEL_MAP.get(theme_name)
        if not model:
            logging.error(f"No data model mapping found for theme '{theme_name}'.")
        return model

    @classmethod
    def needs_footer(cls, theme_name: str) -> bool:
        """
        Checks if a theme is configured to have a footer.
        """
        return theme_name in cls._FOOTER_THEMES


# ============================================================================
# Processing Steps (Strategy Pattern)
# ============================================================================
class ProcessingContext:
    """
    A state container that holds all data during the execution of a pipeline.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str):
        self.theme_config: Dict[str, Any] = theme_config
        self.lang: str = lang
        self.theme_name: str = theme_config.get("theme_name", "Unknown Theme")
        self.data_source_ref: Optional[Dict[str, str]] = None
        self.worksheet: Optional[Any] = None  # gspread.Worksheet is not typed here
        self.row_index: Optional[int] = None
        self.item_data: Optional[Dict[str, Any]] = None
        self.data_model: Optional[Any] = None
        self.template_content: Optional[str] = None
        self.final_text: Optional[str] = None
        self.image_url: Optional[str] = None


class ProcessingStep(ABC):
    """An abstract base class for a single step in the processing pipeline."""

    @abstractmethod
    def execute(self, context: ProcessingContext) -> bool:
        pass


class DataSourceValidator(ProcessingStep):
    """A pipeline step to validate the 'data_source' configuration."""

    def execute(self, context: ProcessingContext) -> bool:
        context.data_source_ref = context.theme_config.get("data_source")
        if not context.data_source_ref:
            logging.error(f"Theme '{context.theme_name}' is missing 'data_source'.")
            return False
        return True


class WorksheetFetcher(ProcessingStep):
    """A pipeline step to fetch the Google Sheet worksheet."""

    def execute(self, context: ProcessingContext) -> bool:
        if context.data_source_ref:
            context.worksheet = sheets_service.get_worksheet(context.data_source_ref)
        if not context.worksheet:
            logging.error(
                f"Failed to fetch worksheet for theme '{context.theme_name}'."
            )
            return False
        return True


class UnusedItemFetcher(ProcessingStep):
    """A pipeline step to retrieve a random, unused item from the worksheet."""

    def execute(self, context: ProcessingContext) -> bool:
        if context.worksheet:
            # --- UPDATED: Force filtering by language ---
            # Before: language=None
            # Now: map context.lang ('english'/'slovak') to sheets_service expectation

            lang_filter = "english" if context.lang == "english" else "slovak"

            # Note: For European Art, if the sheet does NOT have a 'language' column,
            # this might filter out everything if not handled carefully.
            # Assuming European Art uses the same sheet for both EN/SK (metadata are universal),
            # we might need exception or verify column existence.
            # BUT: For Family Photos we definitely want filtering.

            # Safe approach: If theme is 'european_art' (metadata only), maybe ignore language?
            # No, better to standardise: Add 'language' column to ALL sheets, even Art.

            context.row_index, context.item_data = sheets_service.get_unused_item(
                context.worksheet, language=lang_filter
            )

        if not context.item_data or context.row_index is None:
            logging.warning(
                f"No unused content found for theme '{context.theme_name}' in language '{context.lang}'."
            )
            return False
        return True


class DataModelBuilder(ProcessingStep):
    """A pipeline step to create a structured data model from raw sheet data."""

    def execute(self, context: ProcessingContext) -> bool:
        model_class = ThemeRegistry.get_model_class(context.theme_name)
        if not model_class or not context.item_data:
            return False

        try:
            context.data_model = model_class.from_dict(context.item_data)
            return True
        except Exception as e:
            logging.error(
                f"Failed to create data model for '{context.theme_name}': {e}"
            )
            return False


class TemplateLoader(ProcessingStep):
    """A pipeline step to load the content of the template file from disk."""

    def execute(self, context: ProcessingContext) -> bool:
        template_path_str = context.theme_config.get("prompts", {}).get(context.lang)
        if not template_path_str:
            logging.error(f"No template path for theme '{context.theme_name}'.")
            return False

        try:
            template_path = Path(template_path_str)
            context.template_content = template_path.read_text(encoding="utf-8")
            return True
        except FileNotFoundError:
            logging.error(f"Template file not found at path: {template_path_str}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred reading template file: {e}")
            return False


class FooterBuilder:
    """A helper class to construct footer content."""

    _cache: Dict[str, str] = {}

    @classmethod
    def _get_ai_links_content(cls, lang: str) -> str:
        if lang not in cls._cache:
            try:
                path = Path(f"src/resources/template/{lang}/footer_ai_links.txt")
                cls._cache[lang] = path.read_text(encoding="utf-8").strip()
            except FileNotFoundError:
                logging.warning(f"AI links footer file not found for lang '{lang}'.")
                cls._cache[lang] = ""
        return cls._cache[lang]

    @classmethod
    def build_placeholders(cls, theme_name: str, lang: str) -> Dict[str, str]:
        placeholders = {"IMAGE_ATTRIBUTION": "", "AI_LINKS_FOOTER": ""}
        if ThemeRegistry.needs_footer(theme_name):
            placeholders["AI_LINKS_FOOTER"] = cls._get_ai_links_content(lang)
        return placeholders


class TextFormatter(ProcessingStep):
    """A pipeline step to format the final text using the template and data."""

    def execute(self, context: ProcessingContext) -> bool:
        if not context.data_model or not context.template_content:
            return False

        placeholders = asdict(context.data_model)
        placeholders.update(
            FooterBuilder.build_placeholders(context.theme_name, context.lang)
        )

        try:
            context.final_text = context.template_content.format_map(placeholders)
            context.image_url = getattr(context.data_model, "image_url", None)
            return True
        except KeyError as e:
            logging.error(
                f"Placeholder {e} missing in template for '{context.theme_name}'."
            )
            return False


class ItemMarker(ProcessingStep):
    """A final pipeline step to mark the Google Sheet row as used."""

    def execute(self, context: ProcessingContext) -> bool:
        try:
            if context.worksheet and context.row_index:
                sheets_service.mark_item_as_used(context.worksheet, context.row_index)
        except Exception as e:
            logging.error(
                f"Failed to mark item as used for '{context.theme_name}': {e}"
            )
        return True


# ============================================================================
# Pipeline Orchestrator
# ============================================================================
class ProcessingPipeline:
    def __init__(self, steps: list[ProcessingStep]):
        self.steps = steps

    def run(self, context: ProcessingContext) -> bool:
        for step in self.steps:
            if not step.execute(context):
                return False
        return True


# ============================================================================
# Main Handler Implementation
# ============================================================================
class SimpleStaticHandler(BaseHandler):
    """
    Handles themes that fetch a single row from a Google Sheet and format it
    using a simple text template, without involving an LLM.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str):
        super().__init__(theme_config, lang)
        self._pipeline = self._build_pipeline()

    def _build_pipeline(self) -> ProcessingPipeline:
        return ProcessingPipeline(
            [
                DataSourceValidator(),
                WorksheetFetcher(),
                UnusedItemFetcher(),
                DataModelBuilder(),
                TemplateLoader(),
                TextFormatter(),
                ItemMarker(),
            ]
        )

    def _process(self, **kwargs: Any) -> Tuple[Optional[str], Optional[str]]:
        context = ProcessingContext(self.theme_config, self.lang)

        if self._pipeline.run(context):
            return context.final_text, context.image_url

        return None, None


# End of src/handlers/template/simple_static_handler.py (v. 0020)
