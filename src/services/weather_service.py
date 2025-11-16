# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/weather_service.py
"""
A dedicated service module for all interactions with the OpenWeatherMap API.
"""

import logging
from typing import Any, Dict

import httpx

from .. import config


class WeatherService:
    """
    Encapsulates all logic for fetching weather forecasts.
    """

    def get_weather_forecast(
        self, location: str, units: str = "metric", lang: str = "sk"
    ) -> str:
        """
        Fetches and formats a weather forecast for a specific location.

        Args:
            location (str): The location string (e.g., "Bratislava,SK").
            units (str): The units for temperature ('metric' or 'imperial').
            lang (str): The language code for the description.

        Returns:
            str: A formatted string with the weather forecast.
        """
        logging.info(f"Fetching weather forecast for '{location}' in lang '{lang}'...")
        forecast: Dict[str, Any] = {"morning": "N/A", "noon": "N/A", "evening": "N/A"}

        if not config.OPENWEATHER_API_KEY:
            logging.error("OpenWeatherMap API key is not configured.")
            return "Predpoveď počasia nie je dostupná (chýba API kľúč)."

        try:
            params = {
                "q": location,
                "appid": config.OPENWEATHER_API_KEY,
                "units": units,
                "lang": lang,  # <-- FIX: Use the 'lang' parameter passed to the function
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    "https://api.openweathermap.org/data/2.5/forecast", params=params
                )
                res.raise_for_status()

            data = res.json()
            if not data.get("list"):
                logging.warning(f"No forecast data returned for location '{location}'.")
                return "Pre danú lokalitu neboli nájdené žiadne dáta."

            for period in data["list"]:
                hour = int(period["dt_txt"].split(" ")[1][:2])
                temp = period.get("main", {}).get("temp")
                desc = period.get("weather", [{}])[0].get("description", "N/A")

                # Quick fix for a known typo in the OpenWeatherMap Slovak translation
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

            return f"Ráno: {forecast['morning']}, Na obed: {forecast['noon']}, Večer: {forecast['evening']}"

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logging.error(f"Weather location '{location}' not found (404).")
                return f"Lokalita '{location.split(',')[0]}' nebola nájdená."
            logging.exception("HTTP error while fetching weather forecast.")
        except Exception:
            logging.exception(
                "An unexpected error occurred while fetching weather forecast."
            )

        return "Predpoveď počasia nie je momentálne dostupná."


_weather_service_instance = WeatherService()


def get_weather_forecast(location: str, units: str = "metric", lang: str = "sk") -> str:
    """
    Public-facing function to get a formatted weather forecast.
    """
    return _weather_service_instance.get_weather_forecast(location, units, lang)


# End of src/services/weather_service.py (v. 0002)
