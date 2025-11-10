# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/philosophy_models.py
"""
Data model for the philosophy theme processed by the PhilosophyHandler.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class PhilosophyData:
    """
    Represents data for the 'philosophy_mix' theme.

    Attributes:
        quote (str): The philosophical quote.
        philosopher (str): The name of the philosopher.
        paradox (str): An associated paradox for reflection.
    """

    quote: str = ""
    philosopher: str = ""
    paradox: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "PhilosophyData":
        """
        Creates a PhilosophyData instance from a dictionary.

        Args:
            data (Dict[str, str]): The raw data from a Google Sheet row.

        Returns:
            PhilosophyData: An initialized instance of the class.
        """
        return cls(
            quote=data.get("verse_reference", ""),
            philosopher=data.get("theme", "N/A"),
            paradox=data.get("paradox", ""),
        )


# End of src/handlers/llm/philosophy_models.py (v. 0001)
