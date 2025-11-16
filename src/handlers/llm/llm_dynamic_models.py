# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/llm/llm_dynamic_models.py
"""
Data model for themes processed by the LLMDynamicHandler.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class MorningBriefingData:
    """
    Represents the composed data for the 'morning_briefing_sk' theme.

    This dataclass serves as a structured container for all the dynamic pieces
    of information that are assembled by the DynamicContentService before being
    passed to the LLM for final formatting.

    Attributes:
        DATE (str): The current date, formatted.
        NAME_DAY (str): The name day for the current date.
        INTERNATIONAL_DAY (str): The international day, if any.
        WEATHER_LOCATION (str): A placeholder for the weather location name.
        WEATHER_INFO (str): A placeholder for the weather forecast.
        ROTATING_CONTENT_HEADER (str): The header for the rotating content section.
        ROTATING_CONTENT_BODY (str): The body of the rotating content.
        DAILY_GREETING_FOREIGN (str): A daily greeting in a foreign language.
        GREETING_LANGUAGE_ORIGIN (str): The origin language of the greeting.
        DAILY_GREETING_TRANSLATION (str): The Slovak translation of the greeting.
        IMAGE_ATTRIBUTION (str): The HTML attribution for the background image.
    """

    DATE: str = ""
    NAME_DAY: str = ""
    INTERNATIONAL_DAY: str = ""
    WEATHER_LOCATION: str = "{USER_WEATHER_LOCATION}"
    WEATHER_INFO: str = "{USER_WEATHER_FORECAST}"
    ROTATING_CONTENT_HEADER: str = ""
    ROTATING_CONTENT_BODY: str = ""
    DAILY_GREETING_FOREIGN: str = ""
    GREETING_LANGUAGE_ORIGIN: str = ""
    DAILY_GREETING_TRANSLATION: str = ""
    IMAGE_ATTRIBUTION: str = ""  # Reverted back from FOOTER_CONTENT

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MorningBriefingData":
        """
        Creates a MorningBriefingData instance from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary of composed data from
                the DynamicContentService.

        Returns:
            MorningBriefingData: An initialized instance of the class with
            data safely extracted from the input dictionary.
        """
        return cls(
            DATE=data.get("DATE", ""),
            NAME_DAY=data.get("NAME_DAY", "N/A"),
            INTERNATIONAL_DAY=data.get("INTERNATIONAL_DAY", "—"),
            WEATHER_LOCATION=data.get("WEATHER_LOCATION", "{USER_WEATHER_LOCATION}"),
            WEATHER_INFO=data.get("WEATHER_INFO", "{USER_WEATHER_FORECAST}"),
            ROTATING_CONTENT_HEADER=data.get("ROTATING_CONTENT_HEADER", ""),
            ROTATING_CONTENT_BODY=data.get("ROTATING_CONTENT_BODY", ""),
            DAILY_GREETING_FOREIGN=data.get("DAILY_GREETING_FOREIGN", ""),
            GREETING_LANGUAGE_ORIGIN=data.get("GREETING_LANGUAGE_ORIGIN", ""),
            DAILY_GREETING_TRANSLATION=data.get("DAILY_GREETING_TRANSLATION", ""),
            IMAGE_ATTRIBUTION=data.get("IMAGE_ATTRIBUTION", ""),
        )


# End of src/handlers/llm/llm_dynamic_models.py (v. 0004)
