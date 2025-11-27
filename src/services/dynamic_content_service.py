# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/dynamic_content_service.py
"""
Service for fetching and composing dynamic content for 'llm_dynamic' themes.
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


class CompositionStep(ABC):
    @abstractmethod
    def execute(self, context: CompositionContext) -> bool:
        pass


class DateProviderStep(CompositionStep):
    """Pipeline step that provides the current date and localized day name."""

    def execute(self, context: CompositionContext) -> bool:
        theme_name = context.theme_config.get("theme_name", "")

        if theme_name.endswith("_en") or theme_name.endswith("_english"):
            locale = "en_US"
        else:
            locale = "sk_SK"

        day_name = format_date(context.now, "EEEE", locale=locale).capitalize()

        if locale == "en_US":
            date_str = f"<b>{day_name}</b>, {context.now.strftime('%d.%m.%Y')}"
        else:
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
    """Pipeline step to fetch name day and international day."""

    def execute(self, context: CompositionContext) -> bool:
        data = {"NAME_DAY": "", "INTERNATIONAL_DAY": "—"}

        theme_name = context.theme_config.get("theme_name", "")
        is_english = theme_name.endswith("_en") or theme_name.endswith("_english")

        if not is_english and not context.theme_config.get("components", {}).get(
            "name_day"
        ):
            context.data_payload.update(data)
            return True

        ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_MorningBriefing",
            "worksheet_key": "meniny_sk",
        }
        ws = sheets_service.get_worksheet(ref)
        if not ws:
            context.data_payload.update(data)
            return True

        try:
            for row in ws.get_all_records():
                if (
                    row.get("day") == context.now.day
                    and row.get("month") == context.now.month
                ):
                    if not is_english:
                        data["NAME_DAY"] = row.get("name", "N/A")

                    day = str(row.get("international_day", "")).strip()
                    data["INTERNATIONAL_DAY"] = day if day else "—"
                    break
            else:
                if not is_english:
                    data["NAME_DAY"] = "dnes nikto neoslavuje"
        except Exception:
            logging.exception("Failed to get daily info from Google Sheet.")

        context.data_payload.update(data)
        return True


class RotatingContentProviderStep(CompositionStep):
    """Pipeline step to fetch rotating content (quotes, history)."""

    HEADER_TRANSLATIONS = {
        "<b>🏛️ Dnes v histórii:</b>": "<b>🏛️ Today in History:</b>",
        "<b>💡 Zaujímavosť:</b>": "<b>💡 Fun Fact:</b>",
        "<b>✒️ Citát dňa:</b>": "<b>✒️ Quote of the Day:</b>",
        "<b>🤔 Podnet na zamyslenie:</b>": "<b>🤔 Reflection:</b>",
        "<b>🎯 Dnešná mikro-výzva:</b>": "<b>🎯 Today's Micro-Challenge:</b>",
        "<b>✨ Perspektíva dňa:</b>": "<b>✨ Perspective of the Day:</b>",
        "<b>📖 Slovo dňa:</b>": "<b>📖 Word of the Day:</b>",
    }

    def execute(self, context: CompositionContext) -> bool:
        content = {"ROTATING_CONTENT_HEADER": "", "ROTATING_CONTENT_BODY": ""}
        rotation_ref = context.theme_config.get("content_rotation_source")
        if not rotation_ref:
            context.data_payload.update(content)
            return True

        rot_ws = sheets_service.get_worksheet(rotation_ref)
        if not rot_ws:
            context.data_payload.update(content)
            return True

        # Rotation Logic:
        # Ideally, we should rotate independently for SK/EN, but for simplicity,
        # we can use the same content TYPE (e.g. Quote) for both, but fetch the correct language content.
        # The 'Rotation' sheet doesn't usually have languages, it just says "Today show Quotes".
        rot_idx, rot_data = sheets_service.get_unused_item(rot_ws, language=None)

        if (
            not rot_data
            or rot_idx is None
            or not (content_key := rot_data.get("content"))
        ):
            context.data_payload.update(content)
            return True

        # Only mark rotation as used if we are successful?
        # Actually, since both languages share the rotation schedule, marking it used once is fine.
        # But this means if SK runs first, it advances rotation. EN will then pick the NEXT one?
        # NO. Because 'get_unused_item' picks a random unused.
        # Ideally, rotation should be date-based, not 'unused' based, to be sync.
        # For now, we keep logic: The first run of the day (regardless of lang) picks the topic.
        sheets_service.mark_item_as_used(rot_ws, rot_idx)

        spreadsheet_key = rotation_ref["spreadsheet_key"]
        content_ref = {"spreadsheet_key": spreadsheet_key, "worksheet_key": content_key}
        content_ws = sheets_service.get_worksheet(content_ref)

        if content_ws:
            # --- FIX: Determine language for content fetching ---
            theme_name = context.theme_config.get("theme_name", "")
            target_lang = (
                "english"
                if theme_name.endswith("_en") or theme_name.endswith("_english")
                else "slovak"
            )
            # ----------------------------------------------------

            content_idx, content_data = sheets_service.get_unused_item(
                content_ws,
                language=target_lang,  # <--- PASSING LANGUAGE HERE
            )

            if content_data and content_idx is not None:
                try:
                    ws_config = context.app_config["data_sources"][spreadsheet_key][
                        "worksheets"
                    ][content_key]
                    if isinstance(ws_config, dict):
                        raw_header = ws_config.get("header", "")

                        if target_lang == "english":
                            content["ROTATING_CONTENT_HEADER"] = (
                                self.HEADER_TRANSLATIONS.get(raw_header, raw_header)
                            )
                        else:
                            content["ROTATING_CONTENT_HEADER"] = raw_header

                except KeyError:
                    pass

                content["ROTATING_CONTENT_BODY"] = content_data.get("content", "")
                sheets_service.mark_item_as_used(content_ws, content_idx)
            else:
                logging.warning(
                    f"No unused content found for '{content_key}' in language '{target_lang}'."
                )

        context.data_payload.update(content)
        return True


class DailyGreetingProviderStep(CompositionStep):
    """Pipeline step to fetch a daily greeting from a sheet."""

    def execute(self, context: CompositionContext) -> bool:
        data = {
            "DAILY_GREETING_FOREIGN": "",
            "GREETING_LANGUAGE_ORIGIN": "",
            "DAILY_GREETING_TRANSLATION": "",
        }

        if not context.theme_config.get("components", {}).get("daily_greeting"):
            context.data_payload.update(data)
            return True

        ref = {
            "spreadsheet_key": "YDP_LLM_Dynamic_MorningBriefing",
            "worksheet_key": "daily_greetings",
        }
        ws = sheets_service.get_worksheet(ref)
        if ws:
            idx, item_data = sheets_service.get_unused_item(ws, language=None)
            if item_data and idx is not None:
                sheets_service.mark_item_as_used(ws, idx)
                data["DAILY_GREETING_FOREIGN"] = item_data.get("greeting_foreign", "")

                data["GREETING_LANGUAGE_ORIGIN"] = item_data.get("language_origin", "")

                theme_name = context.theme_config.get("theme_name", "")
                is_english = theme_name.endswith("_en") or theme_name.endswith(
                    "_english"
                )

                if is_english:
                    translation = (
                        item_data.get("translation_en")
                        or item_data.get("translation_en ")
                        or item_data.get("translation_sk", "")
                    )
                else:
                    translation = item_data.get("translation_sk", "")

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
        rotation_ref = self.theme_config.get("content_rotation_source")
        if not rotation_ref:
            return {"lesson_payload": "Error: Rotation config missing."}
        return {}

    def get_data(self, user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        theme_name = self.theme_config.get("theme_name", "")

        match theme_name:
            case "morning_briefing_sk" | "morning_briefing_en":
                if not user:
                    raise ValueError(f"User object is required for '{theme_name}'")
                return self._compose_morning_briefing(user)
            case "german_lesson" | "german_lesson_en":
                return self._compose_german_lesson()
            case _:
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
    service = DynamicContentService(app_config, theme_config, tz)
    return service.get_data(user)


# End of src/services/dynamic_content_service.py (v. 0063)
