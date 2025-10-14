# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/dynamic_content_service.py
"""
Service for fetching real-time and rotating dynamic content for 'llm_dynamic' themes.

This module is responsible for gathering all data components required for dynamic
themes. It handles fixed components (like weather), the two-tiered content
rotation, and fetching dynamic images from external providers.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Tuple
from zoneinfo import ZoneInfo

import httpx

from .. import config
from . import sheets_service


def _get_daily_info_from_sheet(
    app_config: Dict[str, Any], now: datetime
) -> Tuple[str, str]:
    """
    Fetches name day and international day for a specific date from a Google Sheet.

    Args:
        app_config (Dict[str, Any]): The global application configuration.
        now (datetime): The current datetime object, timezone-aware.

    Returns:
        Tuple[str, str]: A tuple containing the name day and the international day.
                         Returns ("N/A", "—") on failure.
    """
    logging.info("Fetching daily info (name day, international day)...")
    try:
        source_config = app_config.get("data_sources", {}).get("name_days_sk")
        if not source_config:
            logging.error("Data source 'name_days_sk' not found in config.")
            return "N/A", "—"

        worksheet = sheets_service.get_worksheet(
            source_config["spreadsheet_url"], source_config["worksheet_name"]
        )
        if not worksheet:
            return "N/A", "—"

        all_values = worksheet.get_all_values()
        if len(all_values) < 2:
            logging.warning("Worksheet for name days is empty.")
            return "N/A", "—"

        header, *records_values = all_values
        all_records = [dict(zip(header, row)) for row in records_values]

        for row in all_records:
            if (
                int(row.get("day", 0)) == now.day
                and int(row.get("month", 0)) == now.month
            ):
                name = str(row.get("name", "N/A"))
                international_day = str(row.get("international_day", "")).strip()
                return name, international_day if international_day else "—"
        logging.warning(f"No name day entry found for date {now.day}.{now.month}.")
        return "dnes nikto neoslavuje", "—"
    except Exception as e:
        logging.exception(f"Failed to get daily info from Google Sheet: {e}")
        return "N/A", "—"


def _get_weather_forecast(location: str) -> str:
    """
    Fetches and formats the weather forecast from OpenWeatherMap.

    Args:
        location (str): The location string (e.g., "Bratislava,SK").

    Returns:
        str: A formatted string with the weather forecast, or a fallback message.
    """
    logging.info(f"Fetching weather forecast for '{location}'...")
    forecast = {"morning": "N/A", "noon": "N/A", "evening": "N/A"}
    try:
        base_url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": location,
            "appid": config.OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "sk",
        }
        with httpx.Client(timeout=10.0) as client:
            res = client.get(base_url, params=params)
            res.raise_for_status()
            data = res.json()
        for period in data.get("list", []):
            hour = int(period.get("dt_txt", " ").split(" ")[1].split(":")[0])
            temp = period.get("main", {}).get("temp")
            desc = period.get("weather", [{}])[0].get("description", "")
            if temp is None:
                continue
            forecast_str = f"{round(temp)}°C, {desc}"
            if 5 <= hour <= 9 and forecast["morning"] == "N/A":
                forecast["morning"] = forecast_str
            if 11 <= hour <= 14 and forecast["noon"] == "N/A":
                forecast["noon"] = forecast_str
            if 17 <= hour <= 20 and forecast["evening"] == "N/A":
                forecast["evening"] = forecast_str
        return f"Ráno: {forecast['morning']}, Na obed: {forecast['noon']}, Večer: {forecast['evening']}"
    except Exception as e:
        logging.error(f"Failed to get weather forecast: {e}")
        return "Predpoveď počasia nie je momentálne dostupná."


def _get_rotating_content(
    app_config: Dict[str, Any], rotation_source_key: str
) -> Tuple[str, str]:
    """
    Performs a two-tiered fetch to get a unique, rotating piece of content.

    Args:
        app_config (Dict[str, Any]): The global application configuration.
        rotation_source_key (str): The key for the rotation control sheet in data_sources.

    Returns:
        Tuple[str, str]: A tuple containing the header text and the content body.
    """
    rotation_config = app_config.get("data_sources", {}).get(rotation_source_key)
    if not rotation_config:
        logging.error(
            f"Rotation source '{rotation_source_key}' not found in data_sources."
        )
        return "", ""
    rotation_ws = sheets_service.get_worksheet(
        rotation_config["spreadsheet_url"], rotation_config["worksheet_name"]
    )
    if not rotation_ws:
        return "", ""
    rot_idx, rot_data = sheets_service.get_unused_item(rotation_ws, language=None)
    if not rot_data or rot_idx is None:
        logging.error("Could not get a content type from the rotation sheet.")
        return "Chyba", "Nepodarilo sa načítať typ obsahu."
    content_type_key = rot_data.get("content")
    if not content_type_key:
        logging.error("Rotation sheet is missing 'content' column.")
        return "", ""
    sheets_service.mark_item_as_used(rotation_ws, rot_idx)

    content_config = app_config.get("data_sources", {}).get(content_type_key)
    if not content_config:
        logging.error(f"Data source for '{content_type_key}' not found.")
        return "", ""

    header_text = content_config.get("header_text", "")
    content_ws = sheets_service.get_worksheet(
        content_config["spreadsheet_url"], content_config["worksheet_name"]
    )
    if not content_ws:
        return header_text, "Obsah pre túto tému nie je dostupný."

    content_idx, content_data = sheets_service.get_unused_item(
        content_ws, language=None
    )
    if not content_data or content_idx is None:
        return header_text, "Všetok obsah pre túto kategóriu sa vyčerpal."

    content_body = content_data.get("content", "")
    sheets_service.mark_item_as_used(content_ws, content_idx)
    return header_text, content_body


def _get_daily_greeting(app_config: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Fetches a single, unused daily greeting from the designated Google Sheet.

    Args:
        app_config (Dict[str, Any]): The global application configuration.

    Returns:
        Tuple[str, str, str]: A tuple containing the foreign greeting, its language
                              of origin, and its Slovak translation.
    """
    greeting_config = app_config.get("data_sources", {}).get("daily_greetings")
    if not greeting_config:
        logging.warning("Data source 'daily_greetings' not configured.")
        return "", "", ""
    worksheet = sheets_service.get_worksheet(
        greeting_config["spreadsheet_url"], greeting_config["worksheet_name"]
    )
    if not worksheet:
        return "", "", ""
    row_idx, item_data = sheets_service.get_unused_item(worksheet, language=None)
    if not item_data or row_idx is None:
        logging.warning("No unused greetings found.")
        return "", "", ""
    sheets_service.mark_item_as_used(worksheet, row_idx)
    return (
        item_data.get("greeting_foreign", ""),
        item_data.get("language_origin", ""),
        item_data.get("translation_sk", ""),
    )


def get_all_dynamic_data(
    app_config: Dict[str, Any], theme_config: Dict[str, Any], tz: ZoneInfo
) -> Dict[str, Any]:
    """
    Collects all necessary data for a dynamic theme.

    Args:
        app_config (Dict[str, Any]): The global application configuration.
        theme_config (Dict[str, Any]): The configuration for the specific theme being processed.
        tz (ZoneInfo): The timezone for date/time-sensitive operations.

    Returns:
        Dict[str, Any]: A dictionary containing all fetched data points, ready
                        to be injected into a prompt.
    """
    now = datetime.now(tz)
    dynamic_data = {
        "DATE": now.strftime("%d.%m.%Y"),
        "NAME_DAY": "N/A",
        "INTERNATIONAL_DAY": "—",
        "WEATHER_LOCATION": "N/A",
        "WEATHER_INFO": "N/A",
        "ROTATING_CONTENT_HEADER": "",
        "ROTATING_CONTENT_BODY": "",
        "DAILY_GREETING_FOREIGN": "",
        "GREETING_LANGUAGE_ORIGIN": "",
        "DAILY_GREETING_TRANSLATION": "",
    }

    components = theme_config.get("components", {})
    if components.get("name_day"):
        name_day, international_day = _get_daily_info_from_sheet(app_config, now)
        dynamic_data["NAME_DAY"] = name_day
        dynamic_data["INTERNATIONAL_DAY"] = international_day

    if components.get("weather"):
        location = components["weather"].get("location")
        if location:
            dynamic_data["WEATHER_LOCATION"] = location.split(",")[0]
            dynamic_data["WEATHER_INFO"] = _get_weather_forecast(location)

    if rotation_source_key := theme_config.get("content_rotation_source"):
        header, body = _get_rotating_content(app_config, rotation_source_key)
        dynamic_data["ROTATING_CONTENT_HEADER"] = header
        dynamic_data["ROTATING_CONTENT_BODY"] = body

    if components.get("daily_greeting"):
        greeting, origin, translation = _get_daily_greeting(app_config)
        dynamic_data["DAILY_GREETING_FOREIGN"] = greeting
        dynamic_data["GREETING_LANGUAGE_ORIGIN"] = origin
        dynamic_data["DAILY_GREETING_TRANSLATION"] = translation

    return dynamic_data


# End of src/services/dynamic_content_service.py (v. 0020)
