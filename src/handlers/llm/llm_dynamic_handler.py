# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/llm_dynamic_handler.py
"""
Handler for the 'llm_dynamic' theme type with optimized OOP design.
Fully backward compatible with original implementation.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ... import config
from ...services import dynamic_content_service, image_service, llm_service
from .._base.base_handler import BaseHandler
from .llm_dynamic_models import MorningBriefingData

# ============================================================================
# Resource Manager (Singleton Pattern with Caching)
# ============================================================================


class ResourceCache:
    """Centralized cache for frequently accessed resources."""

    # Changed from Optional[str] to Dict to support multiple languages
    _footer_cache: Dict[str, str] = {}
    _prompts_cache: Dict[str, str] = {}

    @classmethod
    def get_footer(cls, lang: str) -> str:
        """
        Get AI links footer content (cached per language).
        
        Args:
            lang (str): Language code (e.g., 'slovak', 'english').
        """
        if lang not in cls._footer_cache:
            # Construct path dynamically based on language
            footer_path = Path(f"src/resources/template/{lang}/footer_ai_links.txt")
            try:
                with open(footer_path, "r", encoding="utf-8") as f:
                    cls._footer_cache[lang] = f.read().strip()
            except FileNotFoundError:
                logging.warning(f"AI links footer file not found at: {footer_path}. Using empty footer.")
                cls._footer_cache[lang] = ""
        return cls._footer_cache[lang]

    @classmethod
    def get_prompt(cls, prompt_path: str) -> Optional[str]:
        """Get prompt template content (cached)."""
        if prompt_path not in cls._prompts_cache:
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    cls._prompts_cache[prompt_path] = f.read()
            except FileNotFoundError:
                logging.error(f"Prompt file not found at path: {prompt_path}")
                return None
        return cls._prompts_cache[prompt_path]


# ============================================================================
# Processing Steps (Strategy Pattern)
# ============================================================================


class ProcessingStep(ABC):
    """Base class for processing steps."""

    @abstractmethod
    def execute(
        self, handler: "LLMDynamicHandler", user: Optional[Dict[str, Any]]
    ) -> bool:
        """Execute the step. Returns True on success, False on failure."""
        pass


class UserValidator(ProcessingStep):
    """Validates that user object is provided."""

    def execute(
        self, handler: "LLMDynamicHandler", user: Optional[Dict[str, Any]]
    ) -> bool:
        if not user:
            logging.error("User object is required for dynamic content processing.")
            return False
        return True


class StaticImageLoader(ProcessingStep):
    """Loads static image URL if configured."""

    def execute(
        self, handler: "LLMDynamicHandler", user: Optional[Dict[str, Any]]
    ) -> bool:
        if static_url := handler.theme_config.get("static_image_url"):
            handler.image_url = static_url
        return True


class DynamicImageFetcher(ProcessingStep):
    """Fetches dynamic image from external provider."""

    def execute(
        self, handler: "LLMDynamicHandler", user: Optional[Dict[str, Any]]
    ) -> bool:
        if handler.image_url:
            return True

        image_config = handler.theme_config.get("dynamic_image")
        if not image_config:
            return True

        image_data = image_service.get_dynamic_image(image_config)
        if image_data:
            handler.image_url = image_data.get("image_url")
            handler.image_attribution = image_data.get("attribution_html", "")

        return True


class DynamicContentFetcher(ProcessingStep):
    """Fetches all dynamic content data points."""

    def execute(
        self, handler: "LLMDynamicHandler", user: Optional[Dict[str, Any]]
    ) -> bool:
        raw_data = dynamic_content_service.get_all_dynamic_data(
            handler.app_config, handler.theme_config, handler.tz, user=user
        )

        if not raw_data:
            logging.error("Dynamic content service returned no data.")
            return False

        if "IMAGE_URL" in raw_data:
            handler.image_url = raw_data.get("IMAGE_URL")
            handler.image_attribution = raw_data.get("IMAGE_ATTRIBUTION", "")

        try:
            handler.data_model = MorningBriefingData.from_dict(raw_data)
            return True
        except Exception as e:
            logging.error(f"Failed to create data model: {e}")
            return False


class PromptLoader(ProcessingStep):
    """Loads and caches prompt template."""

    def execute(
        self, handler: "LLMDynamicHandler", user: Optional[Dict[str, Any]]
    ) -> bool:
        prompt_path = handler.theme_config.get("prompts", {}).get(handler.lang)
        if not prompt_path:
            logging.error(f"No prompt path found for lang '{handler.lang}'.")
            return False

        handler._prompt_template = ResourceCache.get_prompt(prompt_path)
        return handler._prompt_template is not None


class PromptBuilder:
    """Builds final prompt with all placeholders."""

    @staticmethod
    def build(handler: "LLMDynamicHandler") -> Optional[str]:
        """Build final prompt from template and data."""
        if not handler.data_model or not handler._prompt_template:
            logging.error("Cannot build prompt: missing data model or template.")
            return None

        placeholders = asdict(handler.data_model)
        placeholders["IMAGE_ATTRIBUTION"] = handler.image_attribution

        # Pass the handler's language to get the correct footer
        footer = ResourceCache.get_footer(handler.lang)
        
        if handler.image_attribution and footer:
            footer = "\n" + footer
        placeholders["AI_LINKS_FOOTER"] = footer

        try:
            return handler._prompt_template.format(**placeholders)
        except KeyError as e:
            logging.error(f"Missing placeholder {e} in prompt template.")
            return None
        except Exception as e:
            logging.error(f"Error formatting prompt: {e}")
            return None


class LLMTextGenerator(ProcessingStep):
    """Generates text using LLM service."""

    def execute(
        self, handler: "LLMDynamicHandler", user: Optional[Dict[str, Any]]
    ) -> bool:
        final_prompt = PromptBuilder.build(handler)
        if not final_prompt:
            return False

        handler._final_text = llm_service.call_llm(final_prompt)

        if not handler._final_text:
            logging.warning("LLM returned an empty response for dynamic theme.")
            return False

        return True


# ============================================================================
# Pipeline
# ============================================================================


class DynamicProcessingPipeline:
    """Executes dynamic content processing steps in sequence."""

    def __init__(self) -> None:
        self.steps = [
            UserValidator(),
            StaticImageLoader(),
            DynamicImageFetcher(),
            DynamicContentFetcher(),
            PromptLoader(),
            LLMTextGenerator(),
        ]

    def execute(
        self, handler: "LLMDynamicHandler", user: Optional[Dict[str, Any]]
    ) -> bool:
        """Execute all steps. Stops at first failure."""
        for step in self.steps:
            if not step.execute(handler, user):
                return False
        return True


# ============================================================================
# Main Handler (Backward Compatible)
# ============================================================================


class LLMDynamicHandler(BaseHandler):
    """
    Handles themes that fetch multiple dynamic data points and use an LLM.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str) -> None:
        """Initialize the handler with configuration."""
        super().__init__(theme_config, lang)

        self.app_config, self.tz = config.load_app_config()
        self.image_url: Optional[str] = None
        self.image_attribution: str = ""
        self.data_model: Optional[MorningBriefingData] = None

        self._prompt_template: Optional[str] = None
        self._final_text: Optional[str] = None
        self._pipeline = DynamicProcessingPipeline()

    def _fetch_image_data(self) -> None:
        """
        Fetches a dynamic image. NOTE: Maintained for backward compatibility.
        """
        step = DynamicImageFetcher()
        step.execute(self, None)

    def _fetch_content_data(self, user: Optional[Dict[str, Any]] = None) -> bool:
        """
        Fetches dynamic content. NOTE: Maintained for backward compatibility.
        """
        if not user:
            logging.error("User object is required.")
            return False
        step = DynamicContentFetcher()
        return step.execute(self, user)

    def _generate_llm_text(self) -> Optional[str]:
        """
        Generates text via LLM. NOTE: Maintained for backward compatibility.
        """
        if not PromptLoader().execute(self, None):
            return None
        if LLMTextGenerator().execute(self, None):
            return self._final_text
        return None

    def _process(
        self, user: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Orchestrates content generation by running the processing pipeline.
        """
        self.image_url = None
        self.image_attribution = ""
        self.data_model = None
        self._prompt_template = None
        self._final_text = None

        if self._pipeline.execute(self, user):
            return self._final_text, self.image_url

        return None, None


# End of src/handlers/llm/llm_dynamic_handler.py (v. 0029)