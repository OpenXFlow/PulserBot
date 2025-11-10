# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/dynamic_template_handler.py
"""
Handler for the 'dynamic_template' theme type.
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, Optional, Tuple, Union, cast

from ...services import sheets_service
from .._base.base_handler import BaseHandler
from .dynamic_template_models import GERMAN_LESSON_TITLE_MAP, GermanTerm, GermanVerb


class DynamicTemplateHandler(BaseHandler):
    """
    Handles complex themes that use dynamic template selection without an LLM.

    This handler inherits from BaseHandler and implements the _process method.
    Its logic involves fetching a content key from a rotation sheet, selecting
    the appropriate template based on this key, creating a typed dataclass for the
    data, and formatting the final message.
    """

    def _clean_string(self, text: Any) -> str:
        """
        A helper method to clean strings from sheet cells.

        Args:
            text (Any): The input value from a sheet cell.

        Returns:
            str: The cleaned, single-line string.
        """
        return str(text or "").replace("\n", " ").strip()

    def _normalize_key(self, key: str) -> str:
        """
        Normalizes a worksheet key to its category identifier.

        Args:
            key (str): The raw key from the rotation sheet (e.g., '02_verbs_irregular_de').

        Returns:
            str: The normalized key (e.g., 'verbs_irregular').
        """
        normalized = key.lower()
        parts = normalized.split("_")
        filtered_parts = [
            p for p in parts if not p.isdigit() and p not in ["de", "en", "sk"]
        ]
        return "_".join(filtered_parts)

    def _create_title_from_key(self, key: str) -> str:
        """
        Creates a trilingual lesson title using the centralized title map.

        Args:
            key (str): The raw worksheet key from the rotation sheet.

        Returns:
            str: A formatted title string.
        """
        normalized_key = self._normalize_key(key)
        title = GERMAN_LESSON_TITLE_MAP.get(normalized_key, "NEMČINY")
        return f"LEKCIA: {title}"

    def _get_template_path(self, content_key: str) -> Optional[str]:
        """
        Dynamically selects the correct template path based on the content key.

        Args:
            content_key (str): The raw key from the rotation sheet.

        Returns:
            Optional[str]: The file path to the correct template, or None if not found.
        """
        try:
            prompt_config = self.theme_config["prompts"][self.lang]
            normalized_key = self._normalize_key(content_key)

            if normalized_key in ["verbs_irregular", "verbs_regular"]:
                return cast(str, prompt_config.get("verbs"))
            return cast(str, prompt_config.get("other"))
        except KeyError:
            logging.error("Could not find appropriate template path in theme config.")
            return None

    def _get_image_url(self, content_key: str) -> Optional[str]:
        """
        Gets the appropriate image URL for the lesson category.

        Args:
            content_key (str): The raw key from the rotation sheet.

        Returns:
            Optional[str]: The URL of the image to use, or None.
        """
        category_key = self._normalize_key(content_key)
        specific_url_key = f"static_image_{category_key}_url"

        if specific_url := self.theme_config.get(specific_url_key):
            return cast(str, specific_url)

        return cast(Optional[str], self.theme_config.get("static_image_url"))

    def _build_template_placeholders(
        self, data_model: Union[GermanTerm, GermanVerb], content_key: str
    ) -> Dict[str, Any]:
        """
        Builds the dictionary of placeholders for the template.

        Args:
            data_model (Union[GermanTerm, GermanVerb]): The dataclass instance with lesson data.
            content_key (str): The key from the rotation sheet.

        Returns:
            Dict[str, Any]: A dictionary ready to be used with .format().
        """
        placeholders = asdict(data_model)
        placeholders["lesson_title"] = self._create_title_from_key(content_key)

        if isinstance(data_model, GermanTerm):
            placeholders["term_plural_line"] = (
                f"({data_model.term_plural})" if data_model.term_plural else ""
            )
            for i in range(1, 9):
                sent = (
                    data_model.sentences[i - 1]
                    if i <= len(data_model.sentences)
                    else {"de": "", "en": ""}
                )
                placeholders[f"sentence{i}_de"] = sent.get("de", "")
                placeholders[f"sentence{i}_en"] = sent.get("en", "")

        if isinstance(data_model, GermanVerb):
            tenses = [
                "present",
                "preterite",
                "perfect",
                "plusquamperfekt",
                "futur1",
                "futur2",
            ]
            for i, tense in enumerate(tenses):
                sent = (
                    data_model.sentences[i]
                    if i < len(data_model.sentences)
                    else {"de": "", "en": ""}
                )
                placeholders[f"sentence_{tense}_de"] = sent.get("de", "")
                placeholders[f"sentence_{tense}_en"] = sent.get("en", "")
        return placeholders

    def _process(self) -> Tuple[str | None, str | None]:
        """
        Orchestrates the fetching, composing, and formatting of the content.

        Returns:
            Tuple[str | None, str | None]: A tuple (text, image_url), or (None, None).
        """
        rotation_ref = self.theme_config.get("content_rotation_source")
        if not rotation_ref:
            logging.error("Theme is missing 'content_rotation_source' configuration.")
            return None, None

        rot_ws = sheets_service.get_worksheet(rotation_ref)
        if not rot_ws:
            return None, None
        rot_idx, rot_data = sheets_service.get_unused_item(rot_ws, language=None)

        if (
            not rot_data
            or rot_idx is None
            or not (raw_content_key := rot_data.get("content"))
        ):
            logging.error("Could not get a valid content key from the rotation sheet.")
            return None, None

        content_key = self._clean_string(raw_content_key)
        sheets_service.mark_item_as_used(rot_ws, rot_idx)

        template_path = self._get_template_path(content_key)
        if not template_path:
            return None, None

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_str = f.read()
        except FileNotFoundError:
            logging.error(f"Template file not found at path: {template_path}")
            return None, None

        lesson_ref = {
            "spreadsheet_key": rotation_ref["spreadsheet_key"],
            "worksheet_key": content_key,
        }
        lesson_ws = sheets_service.get_worksheet(lesson_ref)
        if not lesson_ws:
            return None, None
        lesson_idx, lesson_data = sheets_service.get_unused_item(
            lesson_ws, language=None
        )
        if not lesson_data or lesson_idx is None:
            logging.warning(f"No unused content in sheet for key '{content_key}'.")
            return None, None
        sheets_service.mark_item_as_used(lesson_ws, lesson_idx)

        data_model: Optional[Union[GermanTerm, GermanVerb]] = None
        normalized_key = self._normalize_key(content_key)
        if "verbs" in normalized_key:
            data_model = GermanVerb.from_dict(lesson_data)
        else:
            data_model = GermanTerm.from_dict(lesson_data)

        placeholders = self._build_template_placeholders(data_model, content_key)

        placeholders["dynamic_link_html"] = ""
        sg_ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_GermanLesson",
            "worksheet_key": "slow_german_links",
        }
        sg_ws = sheets_service.get_worksheet(sg_ref)
        if sg_ws:
            sg_idx, sg_data = sheets_service.get_unused_item(sg_ws, language=None)
            if sg_data is not None and sg_idx is not None:
                title = self._clean_string(sg_data.get("name", ""))
                link = self._clean_string(sg_data.get("link", ""))
                placeholders["dynamic_link_html"] = (
                    f'Dnešná audio lekcia nemčiny:\n<a href="{link}">{title}</a>'
                )
                sheets_service.mark_item_as_used(sg_ws, sg_idx)

        placeholders["static_grammar_link_html"] = (
            'Preskúmajte gramatiku na:\n<a href="https://deutsch.info/grammar">Deutsch.info</a>'
        )

        final_text = template_str.format(**placeholders)
        image_url = self._get_image_url(content_key)

        return final_text, image_url


# End of src/handlers/template/dynamic_template_handler.py (v. 0032)
