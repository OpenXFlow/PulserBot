# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/config.py
"""
Central configuration module for the YourDailyPulse application.

This module handles loading of environment variables, setting up logging,
and provides utility functions for loading the main application configuration
and dynamically accessing prompt/template files.
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
UNSPLASH_ACCESS_KEY: str = os.environ.get("UNSPLASH_ACCESS_KEY", "")
TIMEZONE_STR: str = os.environ.get("TZ", "Europe/Bratislava")

assert GROQ_API_KEY, "Critical error: Environment variable GROQ_API_KEY is not set."
assert TELEGRAM_TOKEN, (
    "Critical error: Environment variable TELEGRAM_BOT_TOKEN is not set."
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

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    root_logger.addHandler(console_handler)

    if os.environ.get("SENTRY_DSN"):
        sentry_handler = SentryLogsHandler(level=logging.INFO)
        root_logger.addHandler(sentry_handler)

    logging.info(f"Logging configured successfully with level: {LOG_LEVEL_STR}")


def load_app_config() -> Tuple[Dict[str, Any], ZoneInfo]:
    """
    Loads the main configuration from config.json and prepares the timezone object.

    Returns:
        Tuple[Dict[str, Any], ZoneInfo]: A tuple containing the loaded configuration
        data as a dictionary and the configured timezone object.
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.critical(f"Failed to load or parse config.json: {e}", exc_info=True)
        # Return an empty dict but a valid default timezone to prevent crashes
        return {}, ZoneInfo("UTC")

    try:
        tz = ZoneInfo(TIMEZONE_STR)
    except ZoneInfoNotFoundError:
        logging.warning(
            f"Timezone '{TIMEZONE_STR}' not found. Defaulting to 'Europe/Bratislava'."
        )
        tz = ZoneInfo("Europe/Bratislava")

    return config_data, tz


def load_prompt(theme_config: Dict[str, Any], language: str) -> str | None:
    """
    Dynamically loads the content of a prompt or template file.

    This function is now designed to handle the new hierarchical structure of
    the 'prompts' key in the theme configuration.

    Args:
        theme_config (Dict[str, Any]): The configuration dictionary for a specific theme.
        language (str): The language key (e.g., 'slovak').

    Returns:
        str | None: The content of the prompt/template file as a string,
        or None if the path cannot be resolved or the file is not found.
    """
    try:
        prompt_path = theme_config["prompts"][language]
        # Since the path is now a direct string in the config, we can use it.
        # This works for simple themes like llm_static, simple_static.
        # For complex types like dynamic_template, the strategy itself will handle
        # selecting the correct path from the nested dictionary.
        if not isinstance(prompt_path, str):
            logging.error(
                f"Expected a string for prompt path, but got {type(prompt_path)} for theme."
            )
            return None

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except KeyError as e:
        theme_name = theme_config.get("theme_name", "unknown theme")
        logging.error(
            f"Configuration key missing for prompt/template path for theme '{theme_name}' in language '{language}': {e}"
        )
        return None
    except FileNotFoundError:
        logging.error(f"Prompt/template file not found at path: {prompt_path}")
        return None
    except Exception:
        logging.exception(
            "An unexpected error occurred while loading a prompt/template."
        )
        return None


# End of src/config.py (v. 0008)
