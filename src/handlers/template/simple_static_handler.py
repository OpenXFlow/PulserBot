# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/simple_static_handler.py
"""
Handler for the 'simple_static' theme type with optimized OOP design.
Updated to support Unsplash fallback if image_url is missing in Sheet.
Supports SK, EN, and DE language filtering.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

from ...services import image_service, sheets_service
from .._base.base_handler import BaseHandler
from .simple_static_models import EuropeanArtData, FamilyPhotoData, LiteratureData

# ============================================================================
# Configuration and Registry
# ============================================================================


class ThemeRegistry:
    """A central registry for theme-specific configurations."""

    _MODEL_MAP: Dict[str, Type[Any]] = {
        "family_photo": FamilyPhotoData,
        "family_photo_en": FamilyPhotoData,
        "european_art_sk": EuropeanArtData,
        "european_art_en": EuropeanArtData,
        "european_art_de": EuropeanArtData,
        "world_literature": LiteratureData,
        "world_literature_en": LiteratureData,
        "world_literature_de": LiteratureData,
    }

    _FOOTER_THEMES: set[str] = {
        "european_art_sk",
        "european_art_en",
        "european_art_de",
        "world_literature",
        "world_literature_en",
        "world_literature_de",
    }

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
        self.image_attribution: str = ""  # New field for Unsplash credits


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
            # Filter by language to ensure correct content.
            # context.lang comes from config prompts key (slovak, english, german)
            if context.lang == "english":
                lang_filter = "english"
            elif context.lang == "german":
                lang_filter = "german"
            else:
                lang_filter = "slovak"

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
            # Try to get image from Sheet first (if column exists and is filled)
            context.image_url = getattr(context.data_model, "image_url", "")
            return True
        except Exception as e:
            logging.error(
                f"Failed to create data model for '{context.theme_name}': {e}"
            )
            return False


class DynamicImageFetcher(ProcessingStep):
    """
    NEW: Fetches an image from Unsplash if the sheet didn't provide one.
    """

    def execute(self, context: ProcessingContext) -> bool:
        # 1. If Sheet already has a valid URL, use it and skip Unsplash logic
        if context.image_url and context.image_url.strip():
            return True

        # 2. If no URL in Sheet, check config for Unsplash query
        image_config = context.theme_config.get("dynamic_image")
        if image_config:
            image_data = image_service.get_dynamic_image(image_config)
            if image_data:
                context.image_url = image_data.get("image_url")
                context.image_attribution = image_data.get("attribution_html", "")

        return True


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
                # Looks for e.g. src/resources/template/german/footer_ai_links.txt
                path = Path(f"src/resources/template/{lang}/footer_ai_links.txt")
                cls._cache[lang] = path.read_text(encoding="utf-8").strip()
            except FileNotFoundError:
                logging.warning(f"AI links footer file not found for lang '{lang}'.")
                cls._cache[lang] = ""
        return cls._cache[lang]


class TextFormatter(ProcessingStep):
    """A pipeline step to format the final text using the template and data."""

    def execute(self, context: ProcessingContext) -> bool:
        if not context.data_model or not context.template_content:
            return False

        placeholders = asdict(context.data_model)

        # --- Footer Assembly Logic ---
        placeholders["AI_LINKS_FOOTER"] = ""

        # 1. If attribution exists (from Unsplash), always prepare it
        attribution = context.image_attribution

        # 2. If theme requires AI Links footer, load it
        if ThemeRegistry.needs_footer(context.theme_name):
            ai_links = FooterBuilder._get_ai_links_content(context.lang)

            # Combine Image Attribution + AI Links
            footer_parts = []
            if attribution:
                footer_parts.append(attribution)
            if ai_links:
                footer_parts.append(ai_links)

            placeholders["AI_LINKS_FOOTER"] = "\n".join(footer_parts)
        else:
            # Even if no footer is requested, we should probably show attribution if it exists
            pass

        # Fallback: Ensure IMAGE_ATTRIBUTION key exists for templates that might use it specifically
        placeholders["IMAGE_ATTRIBUTION"] = attribution

        try:
            context.final_text = context.template_content.format_map(placeholders)
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
    Now supports dynamic image fetching fallback.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str):
        super().__init__(theme_config, lang)
        self._pipeline = ProcessingPipeline(
            [
                DataSourceValidator(),
                WorksheetFetcher(),
                UnusedItemFetcher(),
                DataModelBuilder(),
                DynamicImageFetcher(),
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


# End of src/handlers/template/simple_static_handler.py (v. 0022)
