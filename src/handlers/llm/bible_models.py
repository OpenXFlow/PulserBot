# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/bible_models.py
"""
Data models for Bible-related themes processed by LLM-based handlers.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class BibleReflectionData:
    """
    Represents data for a daily Bible reflection theme ('bible_sk', 'bible_en').

    Attributes:
        passage (str): The full text of the biblical passage.
        reference (str): The citation for the passage (e.g., "John 3:16").
    """

    passage: str = ""
    reference: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "BibleReflectionData":
        """
        Creates a BibleReflectionData instance from a dictionary.

        Args:
            data (Dict[str, str]): The raw data from a Google Sheet row.

        Returns:
            BibleReflectionData: An initialized instance of the class.
        """
        verse_ref_content = data.get("verse_reference", "")
        return cls(
            passage=verse_ref_content,
            reference=verse_ref_content,
        )


@dataclass
class BibleStudyData:
    """
    Represents data for a Bible study theme ('novy_zakon_sk', 'stary_zakon_sk').

    Attributes:
        verse_reference (str): The reference to the biblical verse or passage
            (e.g., "Genesis 1:1-3").
    """

    verse_reference: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "BibleStudyData":
        """
        Creates a BibleStudyData instance from a dictionary.

        Args:
            data (Dict[str, str]): The raw data from a Google Sheet row.

        Returns:
            BibleStudyData: An initialized instance of the class.
        """
        return cls(verse_reference=data.get("verse_reference", "N/A"))


# End of src/handlers/llm/bible_models.py (v. 0001)
