# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/bible_study_handler.py
"""
A specialized handler for Bible study themes.

This module defines the BibleStudyHandler class, which inherits from
LLMStaticBaseHandler and provides the specific logic for constructing
the content payload for Bible study prompts (e.g., Old and New Testament).
"""

from typing import Any, Dict

from .._base.llm_static_base import LLMStaticBaseHandler
from .bible_models import BibleStudyData


class BibleStudyHandler(LLMStaticBaseHandler):
    """
    Handles Bible study themes like 'novy_zakon_sk' and 'stary_zakon_sk'.

    This class provides the concrete implementation for building the content
    payload required by the Bible study prompt. It uses the BibleStudyData
    model to structure the data.
    """

    def _build_content_payload(self, item_data: Dict[str, Any]) -> str:
        """
        Builds the specific part of the prompt payload from the Bible study sheet data.

        This method converts the raw dictionary data into a structured
        BibleStudyData object and then creates the formatted string for the LLM.

        Args:
            item_data (Dict[str, Any]): The dictionary of data fetched from
                the Google Sheet row for a Bible study theme.

        Returns:
            str: A formatted string containing the verse reference to be
            injected into the main LLM prompt.
        """
        # Create a typed dataclass instance from the raw dictionary
        data_model = BibleStudyData.from_dict(item_data)

        # Build the payload using the type-safe attributes of the model
        return f"- Verse Reference: {data_model.verse_reference}"


# End of src/handlers/llm/bible_study_handler.py (v. 0003)
