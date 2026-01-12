# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/weather_service.py
"""
A dedicated service module for all interactions with the OpenWeatherMap API.
Updated to support asynchronous I/O and In-Memory Caching to minimize API calls.
Supports SK, EN, and DE localizations.
"""

import logging
from typing import Any, Dict

import httpx

from .. import config


class WeatherService:
    """
    Encapsulates all logic for fetching weather forecasts asynchronously.
    Includes caching mechanism to prevent duplicate calls for the same location within one run.
    """

    # Internal cache to store results during a single script execution
    # Key: "location|lang|units", Value: Formatted string
    _cache: Dict[str, str] = {}

    TRANSLATIONS = {
        "sk": {
            "morning": "Ráno",
            "noon": "Na obed",
            "evening": "Večer",
            "missing_key": "Predpoveď počasia nie je dostupná (chýba API kľúč).",
            "no_data": "Pre danú lokalitu neboli nájdené žiadne dáta.",
            "not_found": "Lokalita '{location}' nebola nájdená.",
            "unavailable": "Predpoveď počasia nie je momentálne dostupná.",
            "limit_reached": "Denný limit pre počasie bol vyčerpaný.",
        },
        "en": {
            "morning": "Morning",
            "noon": "Noon",
            "evening": "Evening",
            "missing_key": "Weather forecast not available (missing API key).",
            "no_data": "No data found for this location.",
            "not_found": "Location '{location}' not found.",
            "unavailable": "Weather forecast is currently unavailable.",
            "limit_reached": "Daily weather API limit reached.",
        },
        "de": {
            "morning": "Morgens",
            "noon": "Mittags",
            "evening": "Abends",
            "missing_key": "Wettervorhersage nicht verfügbar (API-Schlüssel fehlt).",
            "no_data": "Keine Daten für diesen Ort gefunden.",
            "not_found": "Ort '{location}' nicht gefunden.",
            "unavailable": "Wettervorhersage ist derzeit nicht verfügbar.",
            "limit_reached": "Tägliches Wetter-API-Limit erreicht.",
        },
    }

    async def get_weather_forecast(
        self, location: str, units: str = "metric", lang: str = "sk"
    ) -> str:
        """
        Fetches and formats a weather forecast for a specific location asynchronously.
        Uses caching to avoid repeated API calls for the same location.

        Args:
            location (str): The location string (e.g., "Bratislava,SK").
            units (str): The units for temperature ('metric' or 'imperial').
            lang (str): The language code ('sk', 'en', 'de').

        Returns:
            str: A formatted string with the weather forecast.
        """
        # 1. Normalize inputs for cache key
        valid_lang = lang if lang in self.TRANSLATIONS else "sk"
        t = self.TRANSLATIONS[valid_lang]

        cache_key = f"{location.lower().strip()}|{valid_lang}|{units}"

        # 2. Check Cache
        if cache_key in self._cache:
            logging.debug(f"Weather Cache HIT for '{location}' ({valid_lang})")
            return self._cache[cache_key]

        # 3. API Call (if not in cache)
        logging.info(
            f"Weather Cache MISS. Fetching API for '{location}' in '{valid_lang}'..."
        )

        if not config.OPENWEATHER_API_KEY:
            logging.error("OpenWeatherMap API key is not configured.")
            return t["missing_key"]

        result_str = t["unavailable"]  # Default fallback

        try:
            params = {
                "q": location,
                "appid": config.OPENWEATHER_API_KEY,
                "units": units,
                "lang": valid_lang,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://api.openweathermap.org/data/2.5/forecast", params=params
                )

                # Specific handling for Rate Limiting (429)
                if res.status_code == 429:
                    logging.warning("OpenWeatherMap API limit reached (429).")
                    # We cache the error message too, so we don't hammer the API again in this run
                    self._cache[cache_key] = t["limit_reached"]
                    return t["limit_reached"]

                res.raise_for_status()
                data = res.json()

            if not data.get("list"):
                logging.warning(f"No forecast data returned for location '{location}'.")
                return t["no_data"]

            forecast: Dict[str, Any] = {
                "morning": "N/A",
                "noon": "N/A",
                "evening": "N/A",
            }

            for period in data["list"]:
                hour = int(period["dt_txt"].split(" ")[1][:2])
                temp = period.get("main", {}).get("temp")
                desc = period.get("weather", [{}])[0].get("description", "N/A")

                # Small correction for Slovak language quirks in API
                if valid_lang == "sk":
                    desc = desc.replace("pretežno", "prevažne")

                if temp is None:
                    continue

                forecast_str = f"{round(temp)}°C, {desc}"
                if 5 <= hour <= 9 and forecast["morning"] == "N/A":
                    forecast["morning"] = forecast_str
                if 11 <= hour <= 14 and forecast["noon"] == "N/A":
                    forecast["noon"] = forecast_str
                if 17 <= hour <= 20 and forecast["evening"] == "N/A":
                    forecast["evening"] = forecast_str

            result_str = f"{t['morning']}: {forecast['morning']}, {t['noon']}: {forecast['noon']}, {t['evening']}: {forecast['evening']}"

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logging.error(f"Weather location '{location}' not found (404).")
                location_name = location.split(",")[0]
                result_str = t["not_found"].replace("{location}", location_name)
            else:
                logging.exception(f"HTTP error while fetching weather forecast: {e}")

        except Exception:
            logging.exception(
                "An unexpected error occurred while fetching weather forecast."
            )

        # 4. Save result to cache (even if it's an error message, to prevent retry loops)
        self._cache[cache_key] = result_str
        return result_str


# Singleton Instance
_weather_service_instance = WeatherService()


async def get_weather_forecast(
    location: str, units: str = "metric", lang: str = "sk"
) -> str:
    """
    Public-facing async function to get a formatted weather forecast.
    """
    return await _weather_service_instance.get_weather_forecast(location, units, lang)


# End of src/services/weather_service.py (v. 0006)
