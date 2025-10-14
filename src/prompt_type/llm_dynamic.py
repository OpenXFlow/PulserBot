# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/prompt_type/llm_dynamic.py
"""
Processing strategy for the 'llm_dynamic' theme type using an OOP approach.

This strategy orchestrates the fetching of multiple dynamic data points (e.g.,
weather, name days, rotating content) from various services. It then injects this
data into a base prompt and uses an LLM to generate the final creative text.
A dynamic image may also be fetched.
"""

import logging
from typing import Any, Dict, Tuple

from .. import config
from ..services import dynamic_content_service, image_service, llm_service


class LLMDynamicStrategy:
    """
    Encapsulates the logic for processing a dynamic theme powered by an LLM.

    This class holds the state and methods required to fetch all dynamic data,
    format it into a final prompt, call the LLM for text generation, and
    return the complete, ready-to-send content.

    Attributes:
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        lang (str): The language key for the content.
        app_config (Dict[str, Any]): The global application configuration.
        tz (ZoneInfo): The timezone for date/time-sensitive operations.
        image_url (str | None): The URL of the image to be sent.
        image_attribution (str): The HTML attribution string for the image.
        dynamic_data (Dict[str, Any]): A dictionary holding all fetched data points.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str):
        """
        Initializes the strategy with theme configuration and language.

        Args:
            theme_config (Dict[str, Any]): The configuration dictionary for the specific theme.
            lang (str): The language key for the content.
        """
        self.theme_config = theme_config
        self.lang = lang
        self.app_config, self.tz = config.load_app_config()
        self.image_url: str | None = None
        self.image_attribution: str = ""
        self.dynamic_data: Dict[str, Any] = {}

    def _fetch_image_data(self) -> None:
        """
        Fetches the primary dynamic image (e.g., from Unsplash).

        This method is called first to get a default image. The result can be
        overridden later if another service provides a different image.
        """
        if image_config := self.theme_config.get("dynamic_image"):
            image_data = image_service.get_dynamic_image(image_config)
            if image_data:
                self.image_url = image_data.get("image_url")
                self.image_attribution = image_data.get("attribution_html", "")

    def _fetch_content_data(self) -> None:
        """
        Fetches all other dynamic data points (weather, name days, etc.).

        This method calls the main data aggregator in dynamic_content_service.
        """
        self.dynamic_data = dynamic_content_service.get_all_dynamic_data(
            self.app_config, self.theme_config, self.tz
        )

        if self.dynamic_data.get("IMAGE_URL"):
            self.image_url = self.dynamic_data.get("IMAGE_URL")
            self.image_attribution = self.dynamic_data.get("IMAGE_ATTRIBUTION", "")

    def _generate_llm_text(self) -> str | None:
        """
        Formats the final prompt and calls the LLM to generate the message text.

        Returns:
            str | None: The generated text from the LLM, or None if generation fails.
        """
        self.dynamic_data["IMAGE_ATTRIBUTION"] = self.image_attribution

        base_prompt = config.load_prompt(
            self.app_config, self.theme_config.get("theme_name", ""), self.lang
        )
        if not base_prompt:
            logging.error(
                f"Could not load prompt for dynamic theme using name '{self.theme_config.get('theme_name', '')}'."
            )
            return None

        final_prompt = base_prompt.format(**self.dynamic_data)
        reflection_text = llm_service.call_llm(final_prompt)

        if not reflection_text:
            logging.warning("LLM returned an empty response for dynamic theme.")
            return None

        return reflection_text

    def execute(self) -> Tuple[str | None, str | None]:
        """
        Orchestrates the entire process of fetching, generating, and returning content.

        Returns:
            Tuple[str | None, str | None]: A tuple containing the final
            text and image URL for distribution, or (None, None) on failure.
        """
        self._fetch_image_data()
        self._fetch_content_data()

        reflection_text = self._generate_llm_text()

        if reflection_text:
            return reflection_text, self.image_url

        return None, None


def process(theme_config: Dict[str, Any], lang: str) -> Tuple[str | None, str | None]:
    """
    Public-facing function that acts as the entry point for this strategy.

    Args:
        theme_config (Dict[str, Any]): The configuration for the theme.
        lang (str): The language key.

    Returns:
        Tuple[str | None, str | None]: The result from the strategy's execute method.
    """
    strategy = LLMDynamicStrategy(theme_config, lang)
    return strategy.execute()


# End of src/prompt_type/llm_dynamic.py (v. 0007)```
