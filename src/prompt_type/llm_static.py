# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/prompt_type/llm_static.py
"""
Processing strategy for the 'llm_static' theme type using an OOP approach.

This strategy fetches a single row of static content from a Google Sheet,
combines it with a base prompt, and uses an LLM to generate the final
creative text. It may also fetch a dynamic image.
"""

import logging
from typing import Any, Dict, Tuple

from .. import config
from ..services import image_service, llm_service, sheets_service


class LLMStaticStrategy:
    """
    Encapsulates the logic for processing a static theme powered by an LLM.

    This class holds the state and methods required to fetch static data,
    format it into a final prompt, call the LLM for text generation, and
    return the complete, ready-to-send content.

    Attributes:
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        lang (str): The language key for the content.
        app_config (Dict[str, Any]): The global application configuration.
        image_url (str | None): The URL of the image to be sent.
        image_attribution (str): The HTML attribution string for the image.
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
        self.app_config, _ = config.load_app_config()
        self.image_url: str | None = None
        self.image_attribution: str = ""

    def _fetch_image_data(self) -> None:
        """Fetches a dynamic image if configured for the theme."""
        if image_config := self.theme_config.get("dynamic_image"):
            image_data = image_service.get_dynamic_image(image_config)
            if image_data:
                self.image_url = image_data.get("image_url")
                self.image_attribution = image_data.get("attribution_html", "")

    def _generate_llm_text(self, item_data: Dict[str, Any]) -> str | None:
        """
        Constructs the final prompt and calls the LLM for text generation.

        Args:
            item_data (Dict[str, Any]): The dictionary of data fetched from the Google Sheet row.

        Returns:
            str | None: The generated text from the LLM, or None if generation fails.
        """
        base_prompt = config.load_prompt(
            self.app_config, self.theme_config.get("theme_name", ""), self.lang
        )
        if not base_prompt:
            logging.error("Could not load prompt for llm_static theme.")
            return None

        content_payload = "\n".join(
            [
                f"- {key.replace('_', ' ').title()}: {value}"
                for key, value in item_data.items()
                if key not in ["language", "used", "date_used", "theme", "content"]
            ]
        )

        final_prompt = base_prompt.format(
            content_payload=content_payload,
            language=self.lang,
            IMAGE_ATTRIBUTION=self.image_attribution,
            TESTAMENT_NAME=self.theme_config.get("testament_name", ""),
        )

        reflection_text = llm_service.call_llm(final_prompt)
        if not reflection_text:
            logging.warning("LLM returned an empty response for llm_static theme.")
            return None

        return reflection_text

    def execute(self) -> Tuple[str | None, str | None]:
        """
        Orchestrates the entire process of fetching data, generating text, and returning content.

        Returns:
            Tuple[str | None, str | None]: A tuple containing the final
            text and image URL for distribution, or (None, None) on failure.
        """
        self._fetch_image_data()

        # --- FIX: Use the public functions from sheets_service, not get_gspread_client ---
        worksheet = sheets_service.get_worksheet(
            self.theme_config["spreadsheet_url"], self.theme_config["worksheet_name"]
        )
        if not worksheet:
            # get_worksheet already logs the error, so we can just return.
            return None, None

        row_index, item_data = sheets_service.get_unused_item(worksheet, self.lang)
        if not item_data or row_index is None:
            logging.warning("No unused content found for llm_static theme.")
            return None, None

        reflection_text = self._generate_llm_text(item_data)

        if reflection_text:
            sheets_service.mark_item_as_used(worksheet, row_index)
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
    strategy = LLMStaticStrategy(theme_config, lang)
    return strategy.execute()


# End of src/prompt_type/llm_static.py (v. 0003)
