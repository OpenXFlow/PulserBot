# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/prompt_type/simple_static.py
"""
Processing strategy for the 'simple_static' theme type using an OOP approach.

This strategy fetches a single row from a pre-defined Google Sheet,
extracts data directly from its columns (like photo_url, caption, etc.),
and formats a final message using a simple text template, without
involving an LLM for text generation.
"""

import logging
from typing import Any, Dict, Tuple

from .. import config
from ..services import sheets_service


class SimpleStaticStrategy:
    """
    Encapsulates the logic for processing a simple, non-LLM static theme.

    This class holds the state and methods required to fetch data from a
    single static source and format it using a template.

    Attributes:
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        lang (str): The language key for the content.
        app_config (Dict[str, Any]): The global application configuration.
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

    def execute(self) -> Tuple[str | None, str | None]:
        """
        Orchestrates the entire process of fetching, formatting, and marking content.
        This is the main public method of the class.

        Returns:
            Tuple[str | None, str | None]: A tuple containing the final
            text and image URL for distribution, or (None, None) on failure.
        """
        worksheet = sheets_service.get_worksheet(
            self.theme_config["spreadsheet_url"], self.theme_config["worksheet_name"]
        )
        if not worksheet:
            # get_worksheet already logs the error, so we can just return.
            return None, None

        # This theme type is language-agnostic, so we pass language=None
        row_index, item_data = sheets_service.get_unused_item(worksheet, language=None)
        if not item_data or row_index is None:
            logging.warning(
                f"No unused content found for theme '{self.theme_config.get('worksheet_name')}'."
            )
            return None, None

        base_template = config.load_prompt(
            self.app_config, self.theme_config.get("theme_name", ""), self.lang
        )
        if not base_template:
            logging.error("Could not load prompt template for simple_static theme.")
            return None, None

        image_url = item_data.get("photo_url")
        caption = item_data.get("caption", "")
        family_quote = item_data.get("family_quotes", "")

        try:
            final_text = base_template.format(
                caption=caption, family_quote=family_quote
            )
        except KeyError as e:
            logging.error(
                f"Placeholder {e} not found in prompt for theme '{self.theme_config.get('theme_name', '')}'."
            )
            return None, None

        sheets_service.mark_item_as_used(worksheet, row_index)

        return final_text, image_url


def process(theme_config: Dict[str, Any], lang: str) -> Tuple[str | None, str | None]:
    """
    Public-facing function that acts as the entry point for this strategy.

    Args:
        theme_config (Dict[str, Any]): The configuration for the theme.
        lang (str): The language key.

    Returns:
        Tuple[str | None, str | None]: The result from the strategy's execute method.
    """
    strategy = SimpleStaticStrategy(theme_config, lang)
    return strategy.execute()


# End of src/prompt_type/simple_static.py (v. 0004)
