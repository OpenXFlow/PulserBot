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
        author (str): The name of the philosopher.
        quote (str): The philosophical quote.
        paradox (str): An associated paradox for reflection (optional).
    """

    author: str = ""
    quote: str = ""
    paradox: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "PhilosophyData":
        """
        Creates a PhilosophyData instance from a dictionary.

        Adapts to the new clean column structure:
        - author
        - quote
        - paradox

        Args:
            data (Dict[str, str]): The raw data from a Google Sheet row.

        Returns:
            PhilosophyData: An initialized instance of the class.
        """
        # New clean structure
        author = data.get("author", "")
        quote = data.get("quote", "")

        # Fallback for legacy structure (if sheet is not updated yet)
        if not author and not quote:
            # Legacy: 'theme' was author, 'verse_reference' was quote
            author = data.get("theme", "Unknown Philosopher")
            quote = data.get("verse_reference", "")

        return cls(
            author=author,
            quote=quote,
            paradox=data.get("paradox", ""),
        )


# End of src/handlers/llm/philosophy_models.py (v. 0002)
