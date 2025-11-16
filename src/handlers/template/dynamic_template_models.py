# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/dynamic_template_models.py
"""
Data models for themes processed by the DynamicTemplateHandler.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Type, Union


@dataclass
class GermanTerm:
    """Represents a German lesson for non-verb parts of speech."""

    term_de: str = ""
    term_en: str = ""
    term_sk: str = ""
    term_plural: str = ""
    sentences: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "GermanTerm":
        """Creates a GermanTerm instance from a dictionary."""
        sentences = [
            {
                "de": data.get(f"sentence{i}_de", ""),
                "en": data.get(f"sentence{i}_en", ""),
            }
            for i in range(1, 9)
            if data.get(f"sentence{i}_de")
        ]
        return cls(
            term_de=data.get("term_de", "N/A"),
            term_en=data.get("term_en", "N/A"),
            term_sk=data.get("term_sk", "N/A"),
            term_plural=data.get("term_plural", ""),
            sentences=sentences,
        )


@dataclass
class GermanVerb:
    """Represents a German lesson for verbs, including all tenses."""

    infinitive_de: str = ""
    infinitive_en: str = ""
    infinitive_sk: str = ""
    present_3rd_person: str = ""
    preterite: str = ""
    perfect: str = ""
    plusquamperfekt: str = ""
    futur1: str = ""
    futur2: str = ""
    sentences: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "GermanVerb":
        """Creates a GermanVerb instance from a dictionary."""
        tenses = [
            "present",
            "preterite",
            "perfect",
            "plusquamperfekt",
            "futur1",
            "futur2",
        ]
        sentences = [
            {
                "de": data.get(f"sentence_{t}_de", ""),
                "en": data.get(f"sentence_{t}_en", ""),
            }
            for t in tenses
        ]
        return cls(
            infinitive_de=data.get("infinitive_de", "N/A"),
            infinitive_en=data.get("infinitive_en", "N/A"),
            infinitive_sk=data.get("infinitive_sk", "N/A"),
            present_3rd_person=data.get("present_3rd_person", ""),
            preterite=data.get("preterite", ""),
            perfect=data.get("perfect", ""),
            plusquamperfekt=data.get("plusquamperfekt", ""),
            futur1=data.get("futur1", ""),
            futur2=data.get("futur2", ""),
            sentences=sentences,
        )


class GermanLessonModelRegistry:
    """A central registry for German lesson configurations and models."""

    _TITLE_MAP: Dict[str, str] = {
        "verbs_irregular": "NEPRAVIDELNÉ SLOVESÁ / IRREGULAR VERBS / UNREGELMÄSSIGE VERBEN",
        "verbs_regular": "PRAVIDELNÉ SLOVESÁ / REGULAR VERBS / REGELMÄSSIGE VERBEN",
        "pronouns": "ZÁMENÁ / PRONOUNS / PRONOMEN",
        "adjectives": "PRÍDAVNÉ MENÁ / ADJECTIVES / ADJEKTIVE",
        "adverbs": "PRÍSLOVKY / ADVERBS / ADVERBIEN",
        "prepositions": "PREDLOŽKY / PREPOSITIONS / PRÄPOSITIONEN",
        "nouns": "PODSTATNÉ MENÁ / NOUNS / SUBSTANTIVE",
    }

    @staticmethod
    def _normalize_key(key: str) -> str:
        """Normalizes a worksheet key to its category identifier."""
        parts = key.lower().split("_")
        return "_".join(
            p for p in parts if not p.isdigit() and p not in ["de", "en", "sk"]
        )

    @classmethod
    def get_model_class_for_key(
        cls, content_key: str
    ) -> Type[Union[GermanTerm, GermanVerb]]:
        """Selects the correct data model class based on the content key."""
        normalized_key = cls._normalize_key(content_key)
        # --- CORRECTED LOGIC ---
        if normalized_key in ["verbs_irregular", "verbs_regular"]:
            return GermanVerb
        return GermanTerm

    @classmethod
    def create_title_from_key(cls, content_key: str) -> str:
        """Creates a formatted, trilingual title for the lesson."""
        normalized_key = cls._normalize_key(content_key)
        title_base = cls._TITLE_MAP.get(normalized_key, "NEMČINY")
        return f"LEKCIA: {title_base}"


# End of src/handlers/template/dynamic_template_models.py (v. 0009)
