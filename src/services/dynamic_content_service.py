# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/dynamic_content_service.py
"""
Service for fetching and composing dynamic content for 'llm_dynamic' themes.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from . import sheets_service


class DynamicContentService:
    """
    Encapsulates all logic for fetching and assembling dynamic content.

    Attributes:
        app_config (Dict[str, Any]): The global application configuration.
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        tz (ZoneInfo): The active timezone for the application.
    """

    def __init__(
        self, app_config: Dict[str, Any], theme_config: Dict[str, Any], tz: ZoneInfo
    ) -> None:
        """
        Initializes the service.

        Args:
            app_config (Dict[str, Any]): The global application configuration.
            theme_config (Dict[str, Any]): The configuration for the theme.
            tz (ZoneInfo): The timezone for date/time-sensitive operations.
        """
        self.app_config = app_config
        self.theme_config = theme_config
        self.tz = tz

    def _get_daily_info_from_sheet(self, now: datetime) -> Dict[str, str]:
        """
        Fetches name day and international day for a specific date.

        Args:
            now (datetime): The current timezone-aware datetime object.

        Returns:
            Dict[str, str]: A dictionary containing 'NAME_DAY' and 'INTERNATIONAL_DAY'.
        """
        data = {"NAME_DAY": "N/A", "INTERNATIONAL_DAY": "—"}
        ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_MorningBriefing",
            "worksheet_key": "meniny_sk",
        }
        ws = sheets_service.get_worksheet(ref)
        if not ws:
            return data
        try:
            for row in ws.get_all_records():
                if row.get("day") == now.day and row.get("month") == now.month:
                    data["NAME_DAY"] = row.get("name", "N/A")
                    day = str(row.get("international_day", "")).strip()
                    data["INTERNATIONAL_DAY"] = day if day else "—"
                    return data
            data["NAME_DAY"] = "dnes nikto neoslavuje"
            return data
        except Exception:
            logging.exception("Failed to get daily info from Google Sheet.")
            return data

    def _get_rotating_content(
        self, rotation_ref: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Performs a two-tiered fetch for rotating content.

        Args:
            rotation_ref (Dict[str, str]): The data source reference for the rotation sheet.

        Returns:
            Optional[Dict[str, Any]]: A dict with header and body, or None on failure.
        """
        rot_ws = sheets_service.get_worksheet(rotation_ref)
        if not rot_ws:
            return None
        rot_idx, rot_data = sheets_service.get_unused_item(rot_ws, language=None)
        if (
            not rot_data
            or rot_idx is None
            or not (content_key := rot_data.get("content"))
        ):
            return None
        sheets_service.mark_item_as_used(rot_ws, rot_idx)

        spreadsheet_key = rotation_ref["spreadsheet_key"]
        content_ref = {"spreadsheet_key": spreadsheet_key, "worksheet_key": content_key}
        content_ws = sheets_service.get_worksheet(content_ref)
        if not content_ws:
            return {"header": "Chyba", "body": "Zdroj obsahu nebol nájdený."}

        content_idx, content_data = sheets_service.get_unused_item(
            content_ws, language=None
        )
        if not content_data or content_idx is None:
            return {
                "header": "",
                "body": "Všetok obsah pre túto kategóriu sa vyčerpal.",
            }

        header_text = ""
        try:
            ws_config = self.app_config["data_sources"][spreadsheet_key]["worksheets"][
                content_key
            ]
            if isinstance(ws_config, dict):
                header_text = ws_config.get("header", "")
        except KeyError:
            logging.warning(
                f"Could not find config for '{content_key}' to extract header."
            )

        sheets_service.mark_item_as_used(content_ws, content_idx)
        return {"header": header_text, "body": content_data.get("content", "")}

    def _get_daily_greeting(self) -> Dict[str, str]:
        """
        Fetches a single, unused daily greeting.

        Returns:
            Dict[str, str]: A dictionary with greeting data.
        """
        data = {
            "DAILY_GREETING_FOREIGN": "",
            "GREETING_LANGUAGE_ORIGIN": "",
            "DAILY_GREETING_TRANSLATION": "",
        }
        ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_MorningBriefing",
            "worksheet_key": "daily_greetings",
        }
        ws = sheets_service.get_worksheet(ref)
        if not ws:
            return data
        idx, item_data = sheets_service.get_unused_item(ws, language=None)
        if not item_data or idx is None:
            return data
        sheets_service.mark_item_as_used(ws, idx)
        data["DAILY_GREETING_FOREIGN"] = item_data.get("greeting_foreign", "")
        data["GREETING_LANGUAGE_ORIGIN"] = item_data.get("language_origin", "")
        data["DAILY_GREETING_TRANSLATION"] = item_data.get("translation_sk", "")
        return data

    def _clean_string(self, text: Any) -> str:
        """A helper to clean strings from sheet cells."""
        return str(text or "").replace("\n", " ").strip()

    def _create_title_from_key(self, key: str) -> str:
        """Creates a trilingual lesson title based on the worksheet key."""
        title_map = {
            "verbs_irregular": "NEPRAVIDELNÉ SLOVESÁ / IRREGULAR VERBS / UNREGELMÄSSIGE VERBEN",
            "verbs_regular": "PRAVIDELNÉ SLOVESÁ / REGULAR VERBS / REGELMÄSSIGE VERBEN",
            "pronouns": "ZÁMENÁ / PRONOUNS / PRONOMEN",
            "adjectives": "PRÍDAVNÉ MENÁ / ADJECTIVES / ADJEKTIVE",
            "adverbs": "PRÍSLOVKY / ADVERBS / ADVERBIEN",
            "prepositions": "PREDLOŽKY / PREPOSITIONS / PRÄPOSITIONEN",
            "nouns": "PODSTATNÉ MENÁ / NOUNS / SUBSTANTIVE",
        }
        parts = key.split("_")
        for part in parts:
            if part in title_map:
                return f"LEKCIA: {title_map[part]}"
        return "LEKCIA NEMČINY"

    def _build_lesson_payload(
        self, content_key: str, lesson_data: Dict[str, Any]
    ) -> str:
        """Builds a structured markdown string from the lesson data."""
        title = self._create_title_from_key(content_key)

        if "verbs" in content_key:
            return f"""# {title}
DE: {self._clean_string(lesson_data.get("infinitive_de", "N/A"))}
ENG: {self._clean_string(lesson_data.get("infinitive_en", "N/A"))}
SK: {self._clean_string(lesson_data.get("infinitive_sk", "N/A"))}

### Prítomný čas: {self._clean_string(lesson_data.get("present_3rd_person", ""))}
DE: {self._clean_string(lesson_data.get("sentence_present_de", ""))}
ENG: {self._clean_string(lesson_data.get("sentence_present_en", ""))}

### Préteritum: {self._clean_string(lesson_data.get("preterite", ""))}
DE: {self._clean_string(lesson_data.get("sentence_preterite_de", ""))}
ENG: {self._clean_string(lesson_data.get("sentence_preterite_en", ""))}

### Perfekt: {self._clean_string(lesson_data.get("perfect", ""))}
DE: {self._clean_string(lesson_data.get("sentence_perfect_de", ""))}
ENG: {self._clean_string(lesson_data.get("sentence_perfect_en", ""))}"""
        else:
            payload = f"""# {title}
DE: {self._clean_string(lesson_data.get("term_de", "N/A"))}
ENG: {self._clean_string(lesson_data.get("term_en", "N/A"))}
SK: {self._clean_string(lesson_data.get("term_sk", "N/A"))}"""
            if term_plural := self._clean_string(lesson_data.get("term_plural")):
                payload += f"\nPlurál: {term_plural}"

            payload += "\n\n### Príkladové vety:"
            for i in range(1, 9):
                if de_sent := self._clean_string(lesson_data.get(f"sentence{i}_de")):
                    en_sent = self._clean_string(lesson_data.get(f"sentence{i}_en", ""))
                    payload += f"\n{i}.  DE: {de_sent}\n    ENG: {en_sent}"
            return payload

    def _compose_morning_briefing(self) -> Dict[str, Any]:
        """
        Composes all data components for the 'morning_briefing_sk' theme.

        Returns:
            Dict[str, Any]: A dictionary of all data points for the prompt.
        """
        now = datetime.now(self.tz)
        data = {
            "DATE": now.strftime("%d.%m.%Y"),
            "NAME_DAY": "N/A",
            "INTERNATIONAL_DAY": "—",
            "WEATHER_LOCATION": "{USER_WEATHER_LOCATION}",
            "WEATHER_INFO": "{USER_WEATHER_FORECAST}",
            "ROTATING_CONTENT_HEADER": "",
            "ROTATING_CONTENT_BODY": "",
            "DAILY_GREETING_FOREIGN": "",
            "GREETING_LANGUAGE_ORIGIN": "",
            "DAILY_GREETING_TRANSLATION": "",
        }
        components = self.theme_config.get("components", {})

        if components.get("name_day"):
            data.update(self._get_daily_info_from_sheet(now))

        if rotation_ref := self.theme_config.get("content_rotation_source"):
            if rotating_content := self._get_rotating_content(rotation_ref):
                data["ROTATING_CONTENT_HEADER"] = rotating_content["header"]
                data["ROTATING_CONTENT_BODY"] = rotating_content["body"]

        if components.get("daily_greeting"):
            data.update(self._get_daily_greeting())

        return data

    def _compose_german_lesson(self) -> Dict[str, Any]:
        """
        Composes the data payload for the 'german_lesson' theme.

        Returns:
            Dict[str, Any]: A dictionary containing the 'lesson_payload'.
        """
        rotation_ref = self.theme_config.get("content_rotation_source")
        if not rotation_ref:
            return {"lesson_payload": "Chyba: Chýba konfigurácia rotácie."}

        slow_german_link_payload = "Dnešná audio lekcia nemčiny:\n"
        sg_ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_GermanLesson",
            "worksheet_key": "slow_german_links",
        }
        sg_ws = sheets_service.get_worksheet(sg_ref)
        if sg_ws:
            sg_idx, sg_data = sheets_service.get_unused_item(sg_ws, language=None)
            if sg_data is not None and sg_idx is not None:
                title, link = (
                    self._clean_string(sg_data.get("name", "")),
                    self._clean_string(sg_data.get("link", "")),
                )
                slow_german_link_payload += f'<a href="{link}">{title}</a>'
                sheets_service.mark_item_as_used(sg_ws, sg_idx)

        rot_ws = sheets_service.get_worksheet(rotation_ref)
        if not rot_ws:
            return {
                "lesson_payload": f"{slow_german_link_payload}\n\nChyba: Nepodarilo sa načítať hárok rotácie."
            }
        rot_idx, rot_data = sheets_service.get_unused_item(rot_ws, language=None)
        if (
            not rot_data
            or rot_idx is None
            or not (content_key := rot_data.get("content"))
        ):
            return {
                "lesson_payload": f"{slow_german_link_payload}\n\nChyba: Nepodarilo sa získať typ lekcie."
            }
        sheets_service.mark_item_as_used(rot_ws, rot_idx)

        lesson_ref = {
            "spreadsheet_key": rotation_ref["spreadsheet_key"],
            "worksheet_key": content_key,
        }
        lesson_ws = sheets_service.get_worksheet(lesson_ref)
        if not lesson_ws:
            return {
                "lesson_payload": f"{slow_german_link_payload}\n\nChyba: Nepodarilo sa načítať hárok s lekciou."
            }
        lesson_idx, lesson_data = sheets_service.get_unused_item(
            lesson_ws, language=None
        )
        if not lesson_data or lesson_idx is None:
            return {
                "lesson_payload": f"{slow_german_link_payload}\n\nChyba: Žiadny nepoužitý obsah pre túto lekciu."
            }
        sheets_service.mark_item_as_used(lesson_ws, lesson_idx)

        lesson_body = self._build_lesson_payload(content_key, lesson_data)
        final_payload = f'{lesson_body}\n\n<b>Ďalšie zdroje:</b>\n{slow_german_link_payload}\nPreskúmajte gramatiku na:\n<a href="https://deutsch.info/grammar">Deutsch.info</a>'
        return {"lesson_payload": final_payload.strip()}

    def get_data(self) -> Dict[str, Any]:
        """
        Main entry point that dispatches to the correct composer method.

        Returns:
            Dict[str, Any]: The final dictionary of data for the prompt.
        """
        theme_name = self.theme_config.get("theme_name", "")
        if theme_name == "morning_briefing_sk":
            return self._compose_morning_briefing()
        if theme_name == "german_lesson":
            return self._compose_german_lesson()
        logging.warning(f"No dynamic content composer found for theme: '{theme_name}'")
        return {}


def get_all_dynamic_data(
    app_config: Dict[str, Any], theme_config: Dict[str, Any], tz: ZoneInfo
) -> Dict[str, Any]:
    """
    Public-facing function to collect all necessary data for a dynamic theme.

    Args:
        app_config (Dict[str, Any]): The global application configuration.
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        tz (ZoneInfo): The timezone for date/time-sensitive operations.

    Returns:
        Dict[str, Any]: A dictionary containing all fetched data points.
    """
    service = DynamicContentService(app_config, theme_config, tz)
    return service.get_data()


# End of src/services/dynamic_content_service.py (v. 0049)
