# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/prompt_type/hybrid_dual_static.py
"""
Processing strategy for the 'hybrid_dual_static' theme type using an OOP approach.

This module defines the logic for themes that combine content from two separate
static Google Sheets (e.g., one for artwork, one for a language lesson).
It fetches one row from each source, combines the data using a simple text
template, and does not involve an LLM for text generation.
"""

import logging
from typing import Any, Dict, Tuple

from .. import config
from ..services import sheets_service


class HybridDualStaticStrategy:
    """
    Encapsulates the logic for processing a 'hybrid_dual_static' theme.

    This class holds the state and methods required to fetch data from two
    distinct static sources, format it into a single message, and mark the
    source items as used.

    Attributes:
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        lang (str): The language key for the content.
        app_config (Dict[str, Any]): The global application configuration.
        art_ws (Any): The worksheet object for the art data source.
        lang_ws (Any): The worksheet object for the language data source.
        art_data (Dict[str, Any] | None): The data fetched from the art worksheet.
        art_idx (int | None): The row index of the fetched art data.
        lang_data (Dict[str, Any] | None): The data fetched from the language worksheet.
        lang_idx (int | None): The row index of the fetched language data.
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
        self.art_ws: Any = None
        self.lang_ws: Any = None
        self.art_data: Dict[str, Any] | None = None
        self.art_idx: int | None = None
        self.lang_data: Dict[str, Any] | None = None
        self.lang_idx: int | None = None

    def _fetch_art_data(self) -> bool:
        """
        Fetches a random unused item from the art data source.

        Returns:
            bool: True if data was successfully fetched, False otherwise.
        """
        art_source_name = self.theme_config.get("art_source")
        art_config = self.app_config.get("data_sources", {}).get(art_source_name)
        if not art_config:
            logging.error(f"Art source '{art_source_name}' not found in data_sources.")
            return False
        self.art_ws = sheets_service.get_worksheet(
            art_config["spreadsheet_url"], art_config["worksheet_name"]
        )
        if not self.art_ws:
            return False
        self.art_idx, self.art_data = sheets_service.get_unused_item(
            self.art_ws, language=None
        )
        if not self.art_data or self.art_idx is None:
            logging.warning(f"No unused art content found in '{art_source_name}'.")
            return False
        return True

    def _fetch_language_data(self) -> bool:
        """
        Fetches a random unused item from the language data source.

        Returns:
            bool: True if data was successfully fetched, False otherwise.
        """
        lang_source_name = self.theme_config.get("language_source")
        lang_config = self.app_config.get("data_sources", {}).get(lang_source_name)
        if not lang_config:
            logging.error(f"Language source '{lang_source_name}' not found.")
            return False
        self.lang_ws = sheets_service.get_worksheet(
            lang_config["spreadsheet_url"], lang_config["worksheet_name"]
        )
        if not self.lang_ws:
            return False
        self.lang_idx, self.lang_data = sheets_service.get_unused_item(
            self.lang_ws, language=None
        )
        if not self.lang_data or self.lang_idx is None:
            logging.warning(
                f"No unused language content found in '{lang_source_name}'."
            )
            return False
        return True

    def _format_text(self) -> Tuple[str | None, str | None]:
        """
        Formats the final text message by combining fetched data with a template.

        Returns:
            Tuple[str | None, str | None]: A tuple containing the formatted
            final text and the image URL, or (None, None) if formatting fails.
        """
        if not self.art_data or not self.lang_data:
            return None, None

        image_url = self.art_data.get("image_url")
        base_template = config.load_prompt(
            self.app_config, self.theme_config.get("theme_name", ""), self.lang
        )
        if not base_template:
            logging.error(
                "Could not load prompt template for hybrid_dual_static theme."
            )
            return None, None

        final_text = base_template.format(
            art_title=self.art_data.get("title", ""),
            art_artist=self.art_data.get("artist", ""),
            art_year=self.art_data.get("year", ""),
            art_medium=self.art_data.get("medium", ""),
            art_owner=self.art_data.get("owner", ""),
            art_credit_line=self.art_data.get("creditLine", ""),
            art_object_url=self.art_data.get("objectURL", ""),
            lang_name=self.lang_data.get("name", ""),
            lang_link=self.lang_data.get("link", ""),
        )
        return final_text, image_url

    def _mark_items_as_used(self) -> None:
        """Marks both fetched items as used in their respective sheets."""
        if self.art_ws and self.art_idx is not None:
            sheets_service.mark_item_as_used(self.art_ws, self.art_idx)
        if self.lang_ws and self.lang_idx is not None:
            sheets_service.mark_item_as_used(self.lang_ws, self.lang_idx)

    def execute(self) -> Tuple[str | None, str | None]:
        """
        Orchestrates the entire process of fetching, formatting, and marking.

        Returns:
            Tuple[str | None, str | None]: A tuple containing the final
            text and image URL for distribution, or (None, None) on failure.
        """
        if not self._fetch_art_data() or not self._fetch_language_data():
            return None, None

        final_text, image_url = self._format_text()

        if final_text:
            self._mark_items_as_used()

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
    strategy = HybridDualStaticStrategy(theme_config, lang)
    return strategy.execute()


# End of src/prompt_type/hybrid_dual_static.py (v. 0007)
