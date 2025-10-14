# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/config.py
"""
Central configuration module for the YourDailyPulse application.
"""

import json
import logging
import os
from typing import Any, Dict, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sentry_sdk.integrations.logging import SentryLogsHandler

# --- Environment Variables ---
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
TELEGRAM_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OPENWEATHER_API_KEY: str = os.environ.get("OPENWEATHER_API_KEY", "")
UNSPLASH_ACCESS_KEY: str = os.environ.get("UNSPLASH_ACCESS_KEY", "")  # <-- NEW
TIMEZONE_STR: str = os.environ.get("TZ", "Europe/Bratislava")

assert GROQ_API_KEY, "Critical error: Environment variable GROQ_API_KEY is not set."
assert TELEGRAM_TOKEN, (
    "Critical error: Environment variable TELEGRAM_BOT_TOKEN is not set."
)
assert OPENWEATHER_API_KEY, (
    "Critical error: Environment variable OPENWEATHER_API_KEY is not set."
)

LOG_LEVEL_STR: str = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging() -> None:
    """
    Configures logging to output to both console and Sentry.
    """
    log_level = getattr(logging, LOG_LEVEL_STR, logging.INFO)
    log_format = "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. Handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # 2. Handler for Sentry
    sentry_handler = SentryLogsHandler(level=log_level)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(sentry_handler)

    logging.info(f"Logging configured successfully with level: {LOG_LEVEL_STR}")


def load_app_config() -> Tuple[Dict[str, Any], ZoneInfo]:
    """
    Loads the main configuration from config.json and prepares the timezone object.
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.critical(f"Failed to load or parse config.json: {e}")
        return {}, ZoneInfo("UTC")

    try:
        tz = ZoneInfo(TIMEZONE_STR)
    except ZoneInfoNotFoundError:
        logging.warning(
            f"Timezone '{TIMEZONE_STR}' not found. Defaulting to 'Europe/Bratislava'."
        )
        tz = ZoneInfo("Europe/Bratislava")

    return config_data, tz


def load_prompt(config: Dict[str, Any], theme: str, language: str) -> str | None:
    """
    Dynamically loads the content of a prompt file based on theme and language.
    """
    try:
        prompt_path = config["themes"][theme]["prompts"][language]
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except KeyError as e:
        logging.error(f"Configuration key missing for prompt '{theme}/{language}': {e}")
        return None
    except FileNotFoundError:
        logging.error(f"Prompt file not found at path: {prompt_path}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading prompt: {e}")
        return None


# End of src/config.py (v. 0007)
