# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/bible_study_handler.py
"""
A specialized handler for Bible study themes.
Updated to support explicit verse text payload.
"""

from typing import Any, Dict

from .._base.llm_static_base import LLMStaticBaseHandler
from .bible_models import BibleStudyData


class BibleStudyHandler(LLMStaticBaseHandler):
    """
    Handles Bible study themes like 'novy_zakon_sk' and 'stary_zakon_sk'.
    """

    def _build_content_payload(self, item_data: Dict[str, Any]) -> str:
        """
        Builds the specific part of the prompt payload from the Bible study sheet data.

        Args:
            item_data (Dict[str, Any]): The dictionary of data fetched from
                the Google Sheet row for a Bible study theme.

        Returns:
            str: A formatted string for the LLM prompt.
        """
        data_model = BibleStudyData.from_dict(item_data)

        # If explicit text is provided in the sheet, pass it to the prompt.
        if data_model.verse_text:
            return (
                f"- Verse Reference: {data_model.verse_reference}\n"
                f"- Text: {data_model.verse_text}"
            )

        # Fallback: Send only reference, let LLM find the text
        return f"- Verse Reference: {data_model.verse_reference}"


# End of src/handlers/llm/bible_study_handler.py (v. 0004)
