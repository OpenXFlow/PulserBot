# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/llm_dynamic_handler.py
"""
Handler for the 'llm_dynamic' theme type.
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, Optional, Tuple

from ... import config
from ...services import dynamic_content_service, image_service, llm_service
from .._base.base_handler import BaseHandler
from .llm_dynamic_models import MorningBriefingData


class LLMDynamicHandler(BaseHandler):
    """
    Handles themes that fetch multiple dynamic data points and use an LLM.

    Attributes:
        app_config (Dict[str, Any]): The global application configuration.
        tz (ZoneInfo): The active timezone for the application.
        image_url (Optional[str]): The URL of the image to be sent.
        image_attribution (str): The HTML attribution string for the image.
        data_model (Optional[MorningBriefingData]): The structured data container.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str) -> None:
        """
        Initializes the handler.

        Args:
            theme_config (Dict[str, Any]): The configuration for the theme.
            lang (str): The language key for the content.
        """
        super().__init__(theme_config, lang)
        self.app_config, self.tz = config.load_app_config()
        self.image_url: Optional[str] = None
        self.image_attribution: str = ""
        self.data_model: Optional[MorningBriefingData] = None

    def _fetch_image_data(self) -> None:
        """Fetches a dynamic image from an external provider if configured."""
        if image_config := self.theme_config.get("dynamic_image"):
            image_data = image_service.get_dynamic_image(image_config)
            if image_data:
                self.image_url = image_data.get("image_url")
                self.image_attribution = image_data.get("attribution_html", "")

    def _fetch_content_data(self) -> bool:
        """
        Fetches all dynamic data points and populates the data model.

        Returns:
            bool: True if data was fetched and model created successfully, False otherwise.
        """
        raw_data = dynamic_content_service.get_all_dynamic_data(
            self.app_config, self.theme_config, self.tz
        )
        if not raw_data:
            logging.error("Dynamic content service returned no data.")
            return False

        if "IMAGE_URL" in raw_data:
            self.image_url = raw_data.get("IMAGE_URL")
            self.image_attribution = raw_data.get("IMAGE_ATTRIBUTION", "")

        self.data_model = MorningBriefingData.from_dict(raw_data)
        self.data_model.IMAGE_ATTRIBUTION = self.image_attribution
        return True

    def _generate_llm_text(self) -> Optional[str]:
        """
        Formats the final prompt and calls the LLM to generate the message text.

        Returns:
            Optional[str]: The generated text from the LLM, or None on failure.
        """
        if not self.data_model:
            logging.error(
                "Cannot generate text because data model has not been populated."
            )
            return None

        prompt_path = self.theme_config.get("prompts", {}).get(self.lang)
        if not prompt_path:
            logging.error(f"No prompt path found for theme and lang '{self.lang}'.")
            return None

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                base_prompt = f.read()
        except FileNotFoundError:
            logging.error(f"Prompt file not found at path: {prompt_path}")
            return None

        placeholders = asdict(self.data_model)
        final_prompt = base_prompt.format(**placeholders)

        reflection_text = llm_service.call_llm(final_prompt)
        if not reflection_text:
            logging.warning("LLM returned an empty response for dynamic theme.")
            return None
        return reflection_text

    def _process(self) -> Tuple[str | None, str | None]:
        """
        Orchestrates the fetching, generation, and returning of dynamic content.

        Returns:
            Tuple[str | None, str | None]: A tuple (text, image_url), or (None, None).
        """
        if static_url := self.theme_config.get("static_image_url"):
            self.image_url = static_url
        if not self.image_url:
            self._fetch_image_data()

        if not self._fetch_content_data():
            return None, None

        reflection_text = self._generate_llm_text()
        if reflection_text:
            return reflection_text, self.image_url
        return None, None


# End of src/handlers/llm/llm_dynamic_handler.py (v. 0015)
