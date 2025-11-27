# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/philosophy_handler.py
"""
A specialized handler for the 'philosophy_mix' theme.
"""

from typing import Any, Dict

from .._base.llm_static_base import LLMStaticBaseHandler
from .philosophy_models import PhilosophyData


class PhilosophyHandler(LLMStaticBaseHandler):
    """
    Handles the 'philosophy_mix' theme.
    """

    def _build_content_payload(self, item_data: Dict[str, Any]) -> str:
        """
        Builds the specific part of the prompt payload from the philosophy sheet data.

        Args:
            item_data (Dict[str, Any]): The dictionary of data fetched from
                the Google Sheet row for the philosophy theme.

        Returns:
            str: A formatted string containing the philosopher, quote, and paradox.
        """
        # Create a typed dataclass instance from the raw dictionary
        data_model = PhilosophyData.from_dict(item_data)

        # Build the payload using the type-safe attributes of the model
        # Note: If paradox is empty, we can leave it out or let LLM handle it.
        # We send it anyway as the prompt expects it.

        return (
            f"- Philosopher: {data_model.author}\n"
            f"- Quote: {data_model.quote}\n"
            f"- Paradox for reflection: {data_model.paradox}"
        )


# End of src/handlers/llm/philosophy_handler.py (v. 0004)
