# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/dynamic_template_models.py
"""
Data models for themes processed by the DynamicTemplateHandler.
"""

from dataclasses import dataclass, field
from typing import Dict, List

GERMAN_LESSON_TITLE_MAP: Dict[str, str] = {
    "verbs_irregular": "NEPRAVIDELNÉ SLOVESÁ / IRREGULAR VERBS / UNREGELMÄSSIGE VERBEN",
    "verbs_regular": "PRAVIDELNÉ SLOVESÁ / REGULAR VERBS / REGELMÄSSIGE VERBEN",
    "pronouns": "ZÁMENÁ / PRONOUNS / PRONOMEN",
    "adjectives": "PRÍDAVNÉ MENÁ / ADJECTIVES / ADJEKTIVE",
    "adverbs": "PRÍSLOVKY / ADVERBS / ADVERBIEN",
    "prepositions": "PREDLOŽKY / PREPOSITIONS / PRÄPOSITIONEN",
    "nouns": "PODSTATNÉ MENÁ / NOUNS / SUBSTANTIVE",
}


@dataclass
class GermanTerm:
    """
    Represents a German lesson for non-verb parts of speech.

    Attributes:
        term_de (str): The German term.
        term_en (str): The English translation.
        term_sk (str): The Slovak translation.
        term_plural (str): The plural form, if applicable.
        sentences (List[Dict[str, str]]): A list of example sentences.
    """

    term_de: str = ""
    term_en: str = ""
    term_sk: str = ""
    term_plural: str = ""
    sentences: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "GermanTerm":
        """
        Creates a GermanTerm instance from a dictionary.

        Args:
            data (Dict[str, str]): The raw data from a Google Sheet row.

        Returns:
            GermanTerm: An initialized instance of the class.
        """
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
    """
    Represents a German lesson for verbs, including all tenses.

    Attributes:
        infinitive_de (str): The infinitive in German.
        infinitive_en (str): The English translation of the infinitive.
        infinitive_sk (str): The Slovak translation of the infinitive.
        present_3rd_person (str): The 3rd person singular present tense form.
        preterite (str): The preterite (simple past) form.
        perfect (str): The perfect tense form.
        plusquamperfekt (str): The pluperfect tense form.
        futur1 (str): The future I tense form.
        futur2 (str): The future II tense form.
        sentences (List[Dict[str, str]]): A list of example sentences.
    """

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
        """
        Creates a GermanVerb instance from a dictionary.

        Args:
            data (Dict[str, str]): The raw data from a Google Sheet row.

        Returns:
            GermanVerb: An initialized instance of the class.
        """
        sentences = [
            {
                "de": data.get("sentence_present_de", ""),
                "en": data.get("sentence_present_en", ""),
            },
            {
                "de": data.get("sentence_preterite_de", ""),
                "en": data.get("sentence_preterite_en", ""),
            },
            {
                "de": data.get("sentence_perfect_de", ""),
                "en": data.get("sentence_perfect_en", ""),
            },
            {
                "de": data.get("sentence_plusquamperfekt_de", ""),
                "en": data.get("sentence_plusquamperfekt_en", ""),
            },
            {
                "de": data.get("sentence_futur1_de", ""),
                "en": data.get("sentence_futur1_en", ""),
            },
            {
                "de": data.get("sentence_futur2_de", ""),
                "en": data.get("sentence_futur2_en", ""),
            },
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


# End of src/handlers/template/dynamic_template_models.py (v. 0007)
