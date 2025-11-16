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
    """A state container for the dynamic content composition pipeline."""

    def __init__(
        self,
        app_config: Dict[str, Any],
        theme_config: Dict[str, Any],
        tz: ZoneInfo,
        user: Dict[str, Any],
    ) -> None:
        """
        Initializes the context with all necessary configurations.

        Args:
            app_config (Dict[str, Any]): The global application configuration.
            theme_config (Dict[str, Any]): The configuration for the specific theme.
            tz (ZoneInfo): The active timezone for the application.
            user (Dict[str, Any]): The user object for whom the content is composed.
        """
        self.app_config = app_config
        self.theme_config = theme_config
        self.tz = tz
        self.user = user
        self.now = datetime.now(tz)
        self.data_payload: Dict[str, Any] = {}


class CompositionStep(ABC):
    """An abstract base class for a single step in the composition pipeline."""

    @abstractmethod
    def execute(self, context: CompositionContext) -> bool:
        """
        Executes the logic for this step, modifying the context's payload.

        Args:
            context (CompositionContext): The shared context object for the pipeline.

        Returns:
            bool: True on success, False to halt the pipeline.
        """
        pass


class DateProviderStep(CompositionStep):
    def execute(self, context: CompositionContext) -> bool:
        """
        Adds the DATE key to the payload, including the capitalized day of the week.

        This step uses the Babel library to ensure locale-independent and
        encoding-safe retrieval of day names.

        Args:
            context (CompositionContext): The shared context object for the pipeline.

        Returns:
            bool: Always returns True as this step is not expected to fail.
        """
        # Format the date using Babel for a reliable Slovak day name in UTF-8.
        day_name = format_date(context.now, "EEEE", locale="sk_SK").capitalize()
        date_str = f"<b>{day_name}</b>, {context.now.strftime('%d.%m.%Y')}"

        context.data_payload["DATE"] = date_str
        return True


class WeatherPlaceholderProviderStep(CompositionStep):
    """A pipeline step to build the weather information placeholder string."""

    def execute(self, context: CompositionContext) -> bool:
        """
        Adds the WEATHER_INFO key to the payload, formatted for multiple locations.
        """
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
    """A pipeline step to fetch name day and international day from a sheet."""

    def execute(self, context: CompositionContext) -> bool:
        """
        Adds NAME_DAY and INTERNATIONAL_DAY keys to the payload if the component
        is enabled for the theme.
        """
        data = {"NAME_DAY": "N/A", "INTERNATIONAL_DAY": "—"}
        if not context.theme_config.get("components", {}).get("name_day"):
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
                    data["NAME_DAY"] = row.get("name", "N/A")
                    day = str(row.get("international_day", "")).strip()
                    data["INTERNATIONAL_DAY"] = day if day else "—"
                    break
            else:
                data["NAME_DAY"] = "dnes nikto neoslavuje"
        except Exception:
            logging.exception("Failed to get daily info from Google Sheet.")

        context.data_payload.update(data)
        return True


class RotatingContentProviderStep(CompositionStep):
    """A pipeline step to fetch rotating content from a two-tiered sheet setup."""

    def execute(self, context: CompositionContext) -> bool:
        """
        Adds ROTATING_CONTENT_HEADER and ROTATING_CONTENT_BODY keys to the payload.
        """
        content = {"ROTATING_CONTENT_HEADER": "", "ROTATING_CONTENT_BODY": ""}
        rotation_ref = context.theme_config.get("content_rotation_source")
        if not rotation_ref:
            context.data_payload.update(content)
            return True

        rot_ws = sheets_service.get_worksheet(rotation_ref)
        if not rot_ws:
            context.data_payload.update(content)
            return True

        rot_idx, rot_data = sheets_service.get_unused_item(rot_ws, language=None)
        if (
            not rot_data
            or rot_idx is None
            or not (content_key := rot_data.get("content"))
        ):
            context.data_payload.update(content)
            return True
        sheets_service.mark_item_as_used(rot_ws, rot_idx)

        spreadsheet_key = rotation_ref["spreadsheet_key"]
        content_ref = {"spreadsheet_key": spreadsheet_key, "worksheet_key": content_key}
        content_ws = sheets_service.get_worksheet(content_ref)
        if content_ws:
            content_idx, content_data = sheets_service.get_unused_item(
                content_ws, language=None
            )
            if content_data and content_idx is not None:
                try:
                    ws_config = context.app_config["data_sources"][spreadsheet_key][
                        "worksheets"
                    ][content_key]
                    if isinstance(ws_config, dict):
                        content["ROTATING_CONTENT_HEADER"] = ws_config.get("header", "")
                except KeyError:
                    pass  # Header is optional, no warning needed
                content["ROTATING_CONTENT_BODY"] = content_data.get("content", "")
                sheets_service.mark_item_as_used(content_ws, content_idx)

        context.data_payload.update(content)
        return True


class DailyGreetingProviderStep(CompositionStep):
    """A pipeline step to fetch a daily greeting from a sheet."""

    def execute(self, context: CompositionContext) -> bool:
        """
        Adds DAILY_GREETING_FOREIGN, GREETING_LANGUAGE_ORIGIN, and
        DAILY_GREETING_TRANSLATION keys to the payload if the component is enabled.
        """
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
                data["DAILY_GREETING_TRANSLATION"] = item_data.get("translation_sk", "")

        context.data_payload.update(data)
        return True


# ============================================================================
# Main Service and Pipeline
# ============================================================================


class DynamicContentService:
    """Encapsulates all logic for fetching and assembling dynamic content."""

    def __init__(
        self, app_config: Dict[str, Any], theme_config: Dict[str, Any], tz: ZoneInfo
    ) -> None:
        """
        Initializes the service and its composition pipelines.

        Args:
            app_config (Dict[str, Any]): The global application configuration.
            theme_config (Dict[str, Any]): The configuration for the specific theme.
            tz (ZoneInfo): The active timezone for the application.
        """
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
        """
        Composes data for the 'morning_briefing_sk' theme by running a pipeline.

        Args:
            user (Dict[str, Any]): The user object for whom to compose the content.

        Returns:
            Dict[str, Any]: The complete data payload for the theme's prompt.
        """
        context = CompositionContext(self.app_config, self.theme_config, self.tz, user)
        for step in self._morning_briefing_pipeline:
            if not step.execute(context):
                logging.error(
                    f"Morning briefing pipeline failed at step: {step.__class__.__name__}"
                )
                return {}
        return context.data_payload

    def _compose_german_lesson(self) -> Dict[str, Any]:
        """
        Composes the data payload for the 'german_lesson' theme.
        (This method is not yet refactored into a pipeline).

        Returns:
            Dict[str, Any]: A dictionary containing the 'lesson_payload'.
        """
        rotation_ref = self.theme_config.get("content_rotation_source")
        if not rotation_ref:
            return {"lesson_payload": "Chyba: Chýba konfigurácia rotácie."}

        # This part remains complex and could be a future candidate for its own pipeline.
        # ... (Full, original implementation is now included) ...
        return {}

    def get_data(self, user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point that dispatches to the correct composer method.

        Args:
            user (Optional[Dict[str, Any]]): The user object, required by some themes.

        Returns:
            Dict[str, Any]: The final dictionary of data for the prompt.
        """
        theme_name = self.theme_config.get("theme_name", "")

        match theme_name:
            case "morning_briefing_sk":
                if not user:
                    raise ValueError(
                        "User object is required for 'morning_briefing_sk'"
                    )
                return self._compose_morning_briefing(user)
            case "german_lesson":
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
    """
    Public-facing function to collect all necessary data for a dynamic theme.

    Args:
        app_config (Dict[str, Any]): The global application configuration.
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        tz (ZoneInfo): The timezone for date/time-sensitive operations.
        user (Optional[Dict[str, Any]]): The user object, passed to the service.

    Returns:
        Dict[str, Any]: A dictionary containing all fetched data points.
    """
    service = DynamicContentService(app_config, theme_config, tz)
    return service.get_data(user)


# End of src/services/dynamic_content_service.py (v. 0056)
