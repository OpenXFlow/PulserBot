# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/dynamic_content_service.py
"""
Service for fetching and composing dynamic content for 'llm_dynamic' themes.
Updated to support language-specific content sheets (SK/EN/DE).
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from babel.dates import format_date

from . import sheets_service


# ============================================================================
# Composition Context and Pipeline Steps
# ============================================================================
class CompositionContext:
    def __init__(
        self,
        app_config: Dict[str, Any],
        theme_config: Dict[str, Any],
        tz: ZoneInfo,
        user: Dict[str, Any],
    ) -> None:
        self.app_config = app_config
        self.theme_config = theme_config
        self.tz = tz
        self.user = user
        self.now = datetime.now(tz)
        self.data_payload: Dict[str, Any] = {}

        # Determine language code for later steps
        theme_name = theme_config.get("theme_name", "")
        if theme_name.endswith("_de"):
            self.lang_code = "de"
            self.locale = "de_DE"
        elif theme_name.endswith("_en") or theme_name.endswith("_english"):
            self.lang_code = "en"
            self.locale = "en_US"
        else:
            self.lang_code = "sk"
            self.locale = "sk_SK"


class CompositionStep(ABC):
    @abstractmethod
    def execute(self, context: CompositionContext) -> bool:
        pass


class DateProviderStep(CompositionStep):
    """Pipeline step that provides the current date and localized day name."""

    def execute(self, context: CompositionContext) -> bool:
        day_name = format_date(context.now, "EEEE", locale=context.locale).capitalize()
        # Format: Pondelok, 01.01.2025
        date_str = f"<b>{day_name}</b>, {context.now.strftime('%d.%m.%Y')}"
        context.data_payload["DATE"] = date_str
        return True


class WeatherPlaceholderProviderStep(CompositionStep):
    def execute(self, context: CompositionContext) -> bool:
        placeholder = "{USER_WEATHER_FORECAST}"
        weather_config = context.user.get("weather", {})
        if "locations" in weather_config and isinstance(
            weather_config.get("locations"), list
        ):
            locations = weather_config["locations"]
            if locations:
                parts = [
                    f"<b>{loc.get('location', '').split(',')[0]}:</b> {{USER_WEATHER_FORECAST_{i}}}"
                    for i, loc in enumerate(locations)
                ]
                placeholder = "\n".join(parts)
        context.data_payload["WEATHER_INFO"] = placeholder
        return True


class DailyInfoProviderStep(CompositionStep):
    """
    Pipeline step to fetch name day (SK) or international day (EN/DE).
    """

    def execute(self, context: CompositionContext) -> bool:
        data = {"NAME_DAY": "", "INTERNATIONAL_DAY": "—"}

        # 1. Select the correct worksheet key based on language
        if context.lang_code == "sk":
            sheet_key = "meniny_sk"
        elif context.lang_code == "en":
            sheet_key = "special_days_en"
        elif context.lang_code == "de":
            sheet_key = "special_days_de"
        else:
            sheet_key = "meniny_sk"

        ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_MorningBriefing",
            "worksheet_key": sheet_key,
        }

        ws = sheets_service.get_worksheet(ref)
        if not ws:
            # If sheet is missing, just proceed with defaults
            context.data_payload.update(data)
            return True

        try:
            # Note: This loads all rows. For calendar sheets (366 rows) this is efficient enough.
            for row in ws.get_all_records():
                if (
                    row.get("day") == context.now.day
                    and row.get("month") == context.now.month
                ):
                    # For SK: Get 'name' and 'international_day'
                    if context.lang_code == "sk":
                        data["NAME_DAY"] = row.get("name", "N/A")
                        day = str(row.get("international_day", "")).strip()
                        data["INTERNATIONAL_DAY"] = day if day else "—"

                    # For EN/DE: Only get 'event_name' (mapped to INTERNATIONAL_DAY)
                    else:
                        event = str(row.get("event_name", "")).strip()
                        data["INTERNATIONAL_DAY"] = event if event else "—"
                        # NAME_DAY remains empty string for EN/DE
                    break
            else:
                if context.lang_code == "sk":
                    data["NAME_DAY"] = "dnes nikto neoslavuje"
        except Exception:
            logging.exception("Failed to get daily info from Google Sheet.")

        context.data_payload.update(data)
        return True


class RotatingContentProviderStep(CompositionStep):
    """Pipeline step to fetch rotating content from language-specific sheets."""

    def execute(self, context: CompositionContext) -> bool:
        content = {"ROTATING_CONTENT_HEADER": "", "ROTATING_CONTENT_BODY": ""}

        # 1. Determine rotation sheet key (e.g., rotation_sk, rotation_en)
        rotation_key = f"rotation_{context.lang_code}"

        rotation_ref = context.theme_config.get("content_rotation_source")

        # If config is generic, override the key to point to specific language rotation
        if rotation_ref:
            rotation_ref = rotation_ref.copy()
            rotation_ref["worksheet_key"] = rotation_key
        else:
            # Fallback if not in config
            rotation_ref = {
                "spreadsheet_key": "YDP_LLM_Dynamic_MorningBriefing",
                "worksheet_key": rotation_key,
            }

        rot_ws = sheets_service.get_worksheet(rotation_ref)
        if not rot_ws:
            context.data_payload.update(content)
            return True

        # 2. Get today's content key (e.g., "fun_facts_en")
        # We pick the next unused item from the rotation list.
        rot_idx, rot_data = sheets_service.get_unused_item(rot_ws, language=None)

        if (
            not rot_data
            or rot_idx is None
            or not (content_key := rot_data.get("content"))
        ):
            context.data_payload.update(content)
            return True

        # Mark rotation as used for today
        sheets_service.mark_item_as_used(rot_ws, rot_idx)

        # 3. Fetch actual content from the specific content sheet
        spreadsheet_key = rotation_ref["spreadsheet_key"]
        content_ref = {"spreadsheet_key": spreadsheet_key, "worksheet_key": content_key}
        content_ws = sheets_service.get_worksheet(content_ref)

        if content_ws:
            # Sheets are now language-specific (e.g. FunFactsEN), so no language filter needed
            content_idx, content_data = sheets_service.get_unused_item(
                content_ws, language=None
            )

            if content_data and content_idx is not None:
                # Load header from config (headers are now localized in config.json)
                try:
                    ws_config = context.app_config["data_sources"][spreadsheet_key][
                        "worksheets"
                    ][content_key]
                    if isinstance(ws_config, dict):
                        content["ROTATING_CONTENT_HEADER"] = ws_config.get("header", "")
                except KeyError:
                    pass

                content["ROTATING_CONTENT_BODY"] = content_data.get("content", "")
                sheets_service.mark_item_as_used(content_ws, content_idx)
            else:
                logging.warning(f"No unused content found for '{content_key}'.")

        context.data_payload.update(content)
        return True


class DailyGreetingProviderStep(CompositionStep):
    """Pipeline step to fetch a daily greeting."""

    def execute(self, context: CompositionContext) -> bool:
        data = {
            "DAILY_GREETING_FOREIGN": "",
            "GREETING_LANGUAGE_ORIGIN": "",
            "DAILY_GREETING_TRANSLATION": "",
        }

        if not context.theme_config.get("components", {}).get("daily_greeting"):
            context.data_payload.update(data)
            return True

        # Determine sheet key based on language (e.g., daily_greetings_sk)
        sheet_key = f"daily_greetings_{context.lang_code}"

        ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_MorningBriefing",
            "worksheet_key": sheet_key,
        }

        ws = sheets_service.get_worksheet(ref)
        if ws:
            # Language specific sheets don't need filtering
            idx, item_data = sheets_service.get_unused_item(ws, language=None)
            if item_data and idx is not None:
                sheets_service.mark_item_as_used(ws, idx)

                data["DAILY_GREETING_FOREIGN"] = item_data.get("greeting_foreign", "")
                data["GREETING_LANGUAGE_ORIGIN"] = item_data.get("language_origin", "")

                # In language-specific sheets, the translation column is just 'translation'
                # (or translation_sk/en/de depending on how you named it in sheet, but standardized 'translation' is best)
                # Fallback logic for backward compatibility with old sheet structure:
                translation = item_data.get("translation", "")
                if not translation:
                    # Try specific columns if 'translation' is empty
                    if context.lang_code == "sk":
                        translation = item_data.get("translation_sk", "")
                    elif context.lang_code == "en":
                        translation = item_data.get("translation_en", "")
                    elif context.lang_code == "de":
                        translation = item_data.get("translation_de", "")

                data["DAILY_GREETING_TRANSLATION"] = translation

        context.data_payload.update(data)
        return True


# ============================================================================
# Main Service and Pipeline
# ============================================================================


class DynamicContentService:
    def __init__(
        self, app_config: Dict[str, Any], theme_config: Dict[str, Any], tz: ZoneInfo
    ) -> None:
        self.app_config = app_config
        self.theme_config = theme_config
        self.tz = tz
        self._morning_briefing_pipeline: List[CompositionStep] = [
            DateProviderStep(),
            WeatherPlaceholderProviderStep(),
            DailyInfoProviderStep(),
            RotatingContentProviderStep(),
            DailyGreetingProviderStep(),
        ]

    def _compose_morning_briefing(self, user: Dict[str, Any]) -> Dict[str, Any]:
        context = CompositionContext(self.app_config, self.theme_config, self.tz, user)
        for step in self._morning_briefing_pipeline:
            if not step.execute(context):
                logging.error(
                    f"Morning briefing pipeline failed at step: {step.__class__.__name__}"
                )
                return {}
        return context.data_payload

    def _compose_german_lesson(self) -> Dict[str, Any]:
        # German lesson logic uses 'DynamicTemplateHandler' logic which handles rotation internally via 'processing_steps'.
        # However, if this service is called for it, we return empty dict to let the handler proceed if needed,
        # but typically DynamicTemplateHandler doesn't use DynamicContentService for the main payload.
        # It uses its own steps.
        # Kept for compatibility if architecture changes.
        return {}

    def get_data(self, user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        theme_name = self.theme_config.get("theme_name", "")

        if "morning_briefing" in theme_name:
            if not user:
                raise ValueError(f"User object is required for '{theme_name}'")
            return self._compose_morning_briefing(user)

        elif "german_lesson" in theme_name:
            return self._compose_german_lesson()

        else:
            logging.warning(
                f"No dynamic content composer found for theme: '{theme_name}'"
            )
            return {}


def get_all_dynamic_data(
    app_config: Dict[str, Any],
    theme_config: Dict[str, Any],
    tz: ZoneInfo,
    user: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Public entry point to get dynamic data.
    """
    service = DynamicContentService(app_config, theme_config, tz)
    return service.get_data(user)


# End of src/services/dynamic_content_service.py (v. 0065)
