# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/simple_static_handler.py
"""
Handler for the 'simple_static' theme type.
"""

import logging
from dataclasses import asdict
from typing import Any, Tuple

from ...services import sheets_service
from .._base.base_handler import BaseHandler
from .simple_static_models import EuropeanArtData, FamilyPhotoData


class SimpleStaticHandler(BaseHandler):
    """
    Handles themes that fetch a single row from a Google Sheet and format it
    using a simple text template, without involving an LLM.
    """

    def _process(self) -> Tuple[str | None, str | None]:
        """
        Orchestrates the fetching, model creation, and formatting of simple static content.

        Returns:
            Tuple[str | None, str | None]: A tuple containing the final formatted text
            and an optional image URL. Returns (None, None) on failure.
        """
        data_source_ref = self.theme_config.get("data_source")
        theme_name = self.theme_config.get("theme_name", "Unknown Theme")

        if not data_source_ref:
            logging.error(
                f"Theme '{theme_name}' is missing 'data_source' configuration."
            )
            return None, None

        worksheet = sheets_service.get_worksheet(data_source_ref)
        if not worksheet:
            return None, None

        row_index, item_data = sheets_service.get_unused_item(worksheet, language=None)
        if not item_data or row_index is None:
            logging.warning(f"No unused content found for theme '{theme_name}'.")
            return None, None

        # --- NEW: Create a dataclass instance based on the theme name ---
        data_model: Any = None
        if theme_name == "family_photo":
            data_model = FamilyPhotoData.from_dict(item_data)
        elif theme_name == "european_art":
            data_model = EuropeanArtData.from_dict(item_data)

        if not data_model:
            logging.error(f"No data model mapping found for theme '{theme_name}'.")
            return None, None

        template_path = self.theme_config.get("prompts", {}).get(self.lang)
        if not template_path:
            logging.error(
                f"No template path found for theme '{theme_name}' and lang '{self.lang}'."
            )
            return None, None

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                base_template = f.read()
        except FileNotFoundError:
            logging.error(f"Template file not found at path: {template_path}")
            return None, None

        # Convert the dataclass instance to a dictionary for formatting
        placeholders = asdict(data_model)

        try:
            final_text = base_template.format(**placeholders)
        except KeyError as e:
            logging.error(
                f"Placeholder {e} in template for theme '{theme_name}' is not defined in the dataclass."
            )
            return None, None

        image_url = data_model.image_url
        sheets_service.mark_item_as_used(worksheet, row_index)

        return final_text, image_url


# End of src/handlers/template/simple_static_handler.py (v. 0009)
