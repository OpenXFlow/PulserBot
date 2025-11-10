# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/bible_handler.py
"""
A specialized handler for daily Bible reflection themes.
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
        # FIX: Correctly use the from_dict classmethod to create the model.
        data_model = BibleReflectionData.from_dict(item_data)

        return f"- Passage: {data_model.passage}\n- Reference: {data_model.reference}"


# End of src/handlers/llm/bible_handler.py (v. 0006)
