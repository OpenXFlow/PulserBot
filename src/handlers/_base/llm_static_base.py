# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/_base/llm_static_base.py
"""
Defines the abstract base class for all llm_static content handlers.

This module provides the `LLMStaticBaseHandler` class, which encapsulates
the common logic for themes that fetch static data from a sheet and use an
LLM to generate creative text.
"""

import logging
from abc import abstractmethod
from typing import Any, Dict, Optional, Tuple

from ... import config
from ...services import image_service, llm_service, sheets_service
from .base_handler import BaseHandler


class LLMStaticBaseHandler(BaseHandler):
    """
    An abstract base class for handlers that use a static data source and an LLM.

    This class handles the generic workflow: fetching an image, getting an item
    from a Google Sheet, generating text via an LLM, and marking the item as used.
    Subclasses must implement the `_build_content_payload` method to provide
    the specific data formatting for the LLM prompt.

    Attributes:
        image_url (Optional[str]): The URL of the image to be sent.
        image_attribution (str): The HTML attribution string for the image.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str) -> None:
        """
        Initializes the LLMStaticBaseHandler.

        Args:
            theme_config (Dict[str, Any]): The configuration for the specific theme.
            lang (str): The language key for the content (e.g., 'slovak').
        """
        super().__init__(theme_config, lang)
        self.image_url: Optional[str] = None
        self.image_attribution: str = ""
        # The global app_config is loaded here as it's needed by this base class
        self.app_config, _ = config.load_app_config()

    def _fetch_image_data(self) -> None:
        """
        Fetches a dynamic image from an external provider if configured for the theme.
        """
        if image_config := self.theme_config.get("dynamic_image"):
            image_data = image_service.get_dynamic_image(image_config)
            if image_data:
                self.image_url = image_data.get("image_url")
                self.image_attribution = image_data.get("attribution_html", "")

    @abstractmethod
    def _build_content_payload(self, item_data: Dict[str, Any]) -> str:
        """
        Builds the specific part of the prompt payload from the sheet data.

        This method must be implemented by concrete subclasses to define how
        the data from a Google Sheet row is formatted into a string for the LLM.

        Args:
            item_data (Dict[str, Any]): The dictionary of data fetched from
                the Google Sheet row.

        Returns:
            str: A formatted string to be injected into the main LLM prompt.
        """
        raise NotImplementedError

    def _generate_llm_text(self, item_data: Dict[str, Any]) -> Optional[str]:
        """
        Constructs the final prompt and calls the LLM for text generation.

        Args:
            item_data (Dict[str, Any]): The dictionary of data from the Google Sheet.

        Returns:
            Optional[str]: The generated text from the LLM, or None on failure.
        """
        base_prompt_path = self.theme_config["prompts"][self.lang]
        try:
            with open(base_prompt_path, "r", encoding="utf-8") as f:
                base_prompt = f.read()
        except FileNotFoundError:
            logging.error(f"Prompt file not found at path: {base_prompt_path}")
            return None

        content_payload = self._build_content_payload(item_data)

        final_prompt = base_prompt.format(
            content_payload=content_payload,
            language=self.lang,
            IMAGE_ATTRIBUTION=self.image_attribution,
            TESTAMENT_NAME=self.theme_config.get("testament_name", ""),
        )

        reflection_text = llm_service.call_llm(final_prompt)
        if not reflection_text:
            logging.warning(
                f"LLM returned an empty response for theme '{self.theme_config.get('theme_name', '')}'."
            )
            return None
        return reflection_text

    def _process(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Executes the common workflow for llm_static handlers.

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing the final
            generated text and an optional image URL, or (None, None) on failure.
        """
        self._fetch_image_data()
        data_source_ref = self.theme_config.get("data_source")
        if not data_source_ref:
            logging.error(
                f"Theme '{self.theme_config.get('theme_name', 'Unknown')}' is missing 'data_source'."
            )
            return None, None

        worksheet = sheets_service.get_worksheet(data_source_ref)
        if not worksheet:
            return None, None

        row_index, item_data = sheets_service.get_unused_item(worksheet, self.lang)
        if not item_data or row_index is None:
            logging.warning(
                f"No unused content for theme '{self.theme_config.get('theme_name', '')}' in lang '{self.lang}'."
            )
            return None, None

        reflection_text = self._generate_llm_text(item_data)
        if reflection_text:
            sheets_service.mark_item_as_used(worksheet, row_index)
            return reflection_text, self.image_url
        return None, None


# End of src/handlers/_base/llm_static_base.py (v. 0001)
