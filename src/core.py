# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/core.py
"""
The core orchestration module for the YourDailyPulse application.
"""

import importlib
import logging
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Type

import psutil

from . import config
from .channels import telegram_channel
from .handlers._base.base_handler import BaseHandler
from .services import sheets_service, weather_service

# A map to resolve handler class names to their module paths
HANDLER_MAP = {
    "BibleHandler": "src.handlers.llm.bible_handler",
    "BibleStudyHandler": "src.handlers.llm.bible_study_handler",
    "PhilosophyHandler": "src.handlers.llm.philosophy_handler",
    "LLMDynamicHandler": "src.handlers.llm.llm_dynamic_handler",
    "SimpleStaticHandler": "src.handlers.template.simple_static_handler",
    "DynamicTemplateHandler": "src.handlers.template.dynamic_template_handler",
}


class JobProcessor:
    """
    Encapsulates all logic and state for a single job execution.

    Attributes:
        time_key (str): The schedule key for the current job (e.g., 'time1').
        user_filter (Optional[list[str]]): An optional filter for specific users.
        app_config (Dict[str, Any]): The loaded application configuration.
        tz (ZoneInfo): The active timezone for the application.
    """

    def __init__(self, time_key: str, user_filter: Optional[list[str]] = None) -> None:
        """
        Initializes the JobProcessor.

        Args:
            time_key (str): The schedule key to be processed.
            user_filter (Optional[list[str]]): Optional list of user descriptions.
        """
        self.time_key = time_key
        self.user_filter = user_filter
        self.app_config, self.tz = config.load_app_config()

    def _get_memory_usage(self) -> str:
        """
        Gets the current memory usage of the process.

        Returns:
            str: A string representing the memory usage in megabytes.
        """
        process = psutil.Process(os.getpid())
        return f"{process.memory_info().rss / 1024**2:.2f} MB"

    def _prepare_content_groups(
        self,
    ) -> Optional[defaultdict[Tuple[str, str], List[Dict[str, Any]]]]:
        """
        Filters users and groups them by (theme, language) for efficient processing.

        Returns:
            Optional[defaultdict[...]]: A dictionary where keys are (theme, language)
            tuples and values are lists of user objects, or None if no users are subscribed.
        """
        active_users = [
            u for u in self.app_config.get("users", []) if u.get("active", True)
        ]
        target_users = active_users

        if self.user_filter:
            target_users = [
                u for u in active_users if u.get("description") in self.user_filter
            ]
            if not target_users:
                logging.warning("No active users found matching the filter.")
                return None

        subscribed_users = [
            u for u in target_users if u.get("subscriptions", {}).get(self.time_key)
        ]
        if not subscribed_users:
            logging.info(f"No active users subscribed for '{self.time_key}'.")
            return None

        content_groups: defaultdict[Tuple[str, str], List[Dict[str, Any]]] = (
            defaultdict(list)
        )
        for user in subscribed_users:
            themes = user.get("subscriptions", {}).get(self.time_key, [])
            lang = user.get("language", "slovak")
            for theme in themes:
                content_groups[(theme, lang)].append(user)

        logging.info(f"Found {len(content_groups)} content groups to process.")
        return content_groups

    def _process_group(
        self, theme: str, lang: str, theme_config: Dict[str, Any]
    ) -> Tuple[str | None, str | None]:
        """
        Dynamically instantiates and executes the correct handler for a theme.

        Args:
            theme (str): The name of the theme being processed.
            lang (str): The language key for the content.
            theme_config (Dict[str, Any]): The configuration for the theme.

        Returns:
            Tuple[str | None, str | None]: A tuple (text, image_url), or (None, None).
        """
        handler_class_name = theme_config.get("handler_class")
        if not handler_class_name:
            logging.error(f"Theme '{theme}' is missing 'handler_class' configuration.")
            return None, None

        theme_config["theme_name"] = theme
        module_path = HANDLER_MAP.get(handler_class_name)

        if not module_path:
            logging.error(
                f"No module path in HANDLER_MAP for handler '{handler_class_name}'."
            )
            return None, None

        try:
            module = importlib.import_module(module_path)
            handler_class: Type[BaseHandler] = getattr(module, handler_class_name)
            handler_instance = handler_class(theme_config, lang)
            return handler_instance.execute()
        except (ImportError, AttributeError):
            logging.exception(
                f"Could not find or instantiate handler '{handler_class_name}'."
            )
            return None, None
        except Exception:
            logging.exception(f"Unexpected error processing theme '{theme}'.")
            return None, None

    def _distribute_content(
        self,
        users: List[Dict[str, Any]],
        theme_config: Dict[str, Any],
        text: str,
        image_url: Optional[str],
    ) -> None:
        """
        Distributes content to users, handling final personalization.

        Args:
            users (List[Dict[str, Any]]): A list of user objects to send the content to.
            theme_config (Dict[str, Any]): The configuration of the theme being processed.
            text (str): The message text, possibly containing placeholders.
            image_url (Optional[str]): The URL of an image to send.
        """
        theme_name = theme_config.get("theme_name", "Unknown")
        for user in users:
            final_text = text
            if "{USER_WEATHER_FORECAST}" in final_text:
                weather_config = user.get("weather")
                location_name = "N/A"
                forecast = "Počasie nie je pre teba nakonfigurované."

                if weather_config and (location := weather_config.get("location")):
                    location_name = location.split(",")[0]

                    user_lang = user.get("language", "sk")
                    lang_code = user_lang[:2]

                    forecast = weather_service.get_weather_forecast(
                        location, weather_config.get("units", "metric"), lang_code
                    )

                final_text = final_text.replace(
                    "{USER_WEATHER_LOCATION}", location_name
                )
                final_text = final_text.replace("{USER_WEATHER_FORECAST}", forecast)

            logging.info(
                f"Distributing content for '{theme_name}' to '{user.get('description')}'."
            )
            for channel in user.get("channels", []):
                if channel.get("platform") == "telegram":
                    identifier = channel.get("identifier")
                    if image_url:
                        telegram_channel.send_photo(identifier, image_url, final_text)
                    else:
                        telegram_channel.send_message(identifier, final_text)

    def execute(self) -> None:
        """
        Orchestrates the entire job execution from preparation to distribution.
        """
        logging.info(
            f"--- 🟢 Starting job for '{self.time_key}'. Memory: {self._get_memory_usage()} ---"
        )
        try:
            if not self.app_config:
                logging.error("Aborting job: missing application configuration.")
                return

            sheets_service.initialize_sheets_service(self.app_config)
            content_groups = self._prepare_content_groups()
            if not content_groups:
                return

            for (theme, lang), users_in_group in content_groups.items():
                theme_config = self.app_config.get("themes", {}).get(theme)
                if not theme_config:
                    logging.error(f"Theme '{theme}' not found in config. Skipping.")
                    continue

                reflection_text, image_url = self._process_group(
                    theme, lang, theme_config
                )
                if reflection_text:
                    self._distribute_content(
                        users_in_group, theme_config, reflection_text, image_url
                    )
        finally:
            logging.info(
                f"--- 🏁 Job for '{self.time_key}' finished. Memory: {self._get_memory_usage()} ---"
            )


def generate_and_send(time_key: str, user_filter: Optional[list[str]] = None) -> None:
    """
    Public-facing entry point that creates and runs a JobProcessor.

    Args:
        time_key (str): The schedule key (e.g., 'time1') to be processed.
        user_filter (Optional[list[str]]): An optional list of user descriptions.
    """
    processor = JobProcessor(time_key, user_filter)
    processor.execute()


# End of src/core.py (v. 0037)
