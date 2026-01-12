# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/bible_handler.py
"""
A specialized handler for daily Bible reflection themes.
Updated to support explicit verse text payload.
"""

from typing import Any, Dict

from .._base.llm_static_base import LLMStaticBaseHandler
from .bible_models import BibleReflectionData


class BibleHandler(LLMStaticBaseHandler):
    """
    Handles daily Bible reflection themes like 'bible_sk' and 'bible_en'.
    """

    def _build_content_payload(self, item_data: Dict[str, Any]) -> str:
        """
        Builds the specific part of the prompt payload from the Bible sheet data.

        Args:
            item_data (Dict[str, Any]): The dictionary of data from the sheet.

        Returns:
            str: A formatted string for the LLM prompt.
        """
        data_model = BibleReflectionData.from_dict(item_data)

        # If we have the explicit text (e.g. from SK sheet), send it to the LLM.
        # This prevents the LLM from hallucinating a bad translation.
        if data_model.verse_text:
            return (
                f"- Reference: {data_model.reference}\n- Text: {data_model.verse_text}"
            )

        # Fallback for EN/DE where text might be missing in sheet -> LLM will look it up
        return f"- Reference: {data_model.reference}"


# End of src/handlers/llm/bible_handler.py (v. 0008)
