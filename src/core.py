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
from abc import ABC, abstractmethod
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

# ============================================================================
# Processing Context and Pipeline Steps
# ============================================================================


class ProcessingContext:
    """A state container that holds data across the job processing pipeline."""

    def __init__(self, time_key: str, user_filter: Optional[List[str]] = None) -> None:
        """
        Initializes the context with the job's primary parameters.

        Args:
            time_key (str): The schedule key for the current job (e.g., 'time1').
            user_filter (Optional[List[str]]): An optional filter for specific users.
        """
        self.time_key = time_key
        self.user_filter = user_filter
        self.app_config, self.tz = config.load_app_config()
        self.content_groups: Optional[
            defaultdict[Tuple[str, str], List[Dict[str, Any]]]
        ] = None


class ProcessingStep(ABC):
    """An abstract base class for a single step in the job processing pipeline."""

    @abstractmethod
    def execute(self, context: ProcessingContext) -> bool:
        """
        Executes the logic for this step.

        Args:
            context (ProcessingContext): The shared context object for the pipeline.

        Returns:
            bool: True on success, False to halt the pipeline.
        """
        pass


class InitializeServices(ProcessingStep):
    """Pipeline step to initialize necessary external services."""

    def execute(self, context: ProcessingContext) -> bool:
        """
        Initializes the Google Sheets service with the application configuration.

        Args:
            context (ProcessingContext): The shared context object.

        Returns:
            bool: True on success, False if configuration is missing.
        """
        if not context.app_config:
            logging.error("Aborting job: missing application configuration.")
            return False
        sheets_service.initialize_sheets_service(context.app_config)
        return True


class PrepareContentGroups(ProcessingStep):
    """Pipeline step to filter users and group them by content needs."""

    def execute(self, context: ProcessingContext) -> bool:
        """
        Filters active and subscribed users and groups them by (theme, language)
        for efficient, single-generation processing.

        Args:
            context (ProcessingContext): The shared context object.

        Returns:
            bool: True on success, False if no matching users are found.
        """
        active_users = [
            u for u in context.app_config.get("users", []) if u.get("active", True)
        ]
        target_users = active_users

        if context.user_filter:
            target_users = [
                u for u in active_users if u.get("description") in context.user_filter
            ]
            if not target_users:
                logging.warning("No active users found matching the filter.")
                return False

        subscribed_users = [
            u for u in target_users if u.get("subscriptions", {}).get(context.time_key)
        ]
        if not subscribed_users:
            logging.info(f"No active users subscribed for '{context.time_key}'.")
            return False

        groups: defaultdict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
        for user in subscribed_users:
            themes = user.get("subscriptions", {}).get(context.time_key, [])
            lang = user.get("language", "slovak")
            for theme in themes:
                groups[(theme, lang)].append(user)

        logging.info(f"Found {len(groups)} content groups to process.")
        context.content_groups = groups
        return True


class ProcessAndDistributeGroups(ProcessingStep):
    """
    The main pipeline step that processes each content group based on its
    configured strategy (e.g., generate-once or per-user) and distributes
    the generated content.
    """

    def _instantiate_handler(
        self, theme: str, lang: str, theme_config: Dict[str, Any]
    ) -> Optional[BaseHandler]:
        """
        Dynamically instantiates the correct handler for a theme.

        Args:
            theme (str): The name of the theme.
            lang (str): The language key for the content.
            theme_config (Dict[str, Any]): The configuration for the theme.

        Returns:
            Optional[BaseHandler]: An instance of the handler, or None on failure.
        """
        theme_config["theme_name"] = theme
        handler_class_name = theme_config.get("handler_class")
        if not handler_class_name or not (
            module_path := HANDLER_MAP.get(handler_class_name)
        ):
            logging.error(f"Handler for theme '{theme}' is not configured correctly.")
            return None
        try:
            module = importlib.import_module(module_path)
            handler_class: Type[BaseHandler] = getattr(module, handler_class_name)
            return handler_class(theme_config, lang)
        except (ImportError, AttributeError) as e:
            logging.exception(
                f"Could not instantiate handler '{handler_class_name}': {e}"
            )
            return None

    def _personalize_weather_content(self, text: str, user: Dict[str, Any]) -> str:
        """
        Replaces weather placeholders in the text for a specific user.

        Args:
            text (str): The content text containing placeholders.
            user (Dict[str, Any]): The user object with weather configuration.

        Returns:
            str: The text with weather placeholders replaced by actual forecasts.
        """
        final_text = text
        user_lang = user.get("language", "slovak")

        lang_code_map = {"slovak": "sk", "english": "en"}
        lang_code = lang_code_map.get(user_lang, "sk")

        weather_config = user.get("weather", {})

        if "locations" in weather_config and isinstance(
            weather_config.get("locations"), list
        ):
            for i, loc_config in enumerate(weather_config["locations"]):
                location = loc_config.get("location")
                if not location:
                    continue
                location_name = location.split(",")[0]
                forecast = weather_service.get_weather_forecast(
                    location, weather_config.get("units", "metric"), lang_code
                )
                final_text = final_text.replace(
                    f"{{USER_WEATHER_LOCATION_{i}}}", location_name
                )
                final_text = final_text.replace(
                    f"{{USER_WEATHER_FORECAST_{i}}}", forecast
                )
        elif location := weather_config.get("location"):
            location_name = location.split(",")[0]
            forecast = weather_service.get_weather_forecast(
                location, weather_config.get("units", "metric"), lang_code
            )
            final_text = final_text.replace("{USER_WEATHER_LOCATION}", location_name)
            final_text = final_text.replace("{USER_WEATHER_FORECAST}", forecast)

        return final_text

    def _distribute_content(
        self,
        users: List[Dict[str, Any]],
        theme_config: Dict[str, Any],
        text: str,
        image_url: Optional[str],
    ) -> None:
        """
        Distributes the generated content to a list of users via their
        configured channels.

        Args:
            users (List[Dict[str, Any]]): The list of user objects to send to.
            theme_config (Dict[str, Any]): The configuration of the theme.
            text (str): The message text to be sent.
            image_url (Optional[str]): The URL of an image to send, if any.
        """
        theme_name = theme_config.get("theme_name", "Unknown")
        for user in users:
            final_text = self._personalize_weather_content(text, user)
            logging.info(f"Distributing '{theme_name}' to '{user.get('description')}'.")
            for channel in user.get("channels", []):
                if channel.get("platform") == "telegram":
                    identifier = channel.get("identifier")
                    if image_url:
                        telegram_channel.send_photo(identifier, image_url, final_text)
                    else:
                        telegram_channel.send_message(identifier, final_text)

    def execute(self, context: ProcessingContext) -> bool:
        """
        Iterates through content groups and executes the appropriate
        processing strategy (e.g., "per_user" or "once_per_group").

        Args:
            context (ProcessingContext): The shared context object.

        Returns:
            bool: Always returns True as errors within are handled individually.
        """
        if not context.content_groups:
            return True

        for (theme, lang), users_in_group in context.content_groups.items():
            theme_config = context.app_config.get("themes", {}).get(theme)
            if not theme_config:
                logging.error(f"Theme '{theme}' not found in config. Skipping.")
                continue

            handler = self._instantiate_handler(theme, lang, theme_config)
            if not handler:
                continue

            strategy = theme_config.get("processing_strategy", "once_per_group")

            if strategy == "per_user":
                logging.info(f"Processing '{theme}' with per-user personalization.")
                for user in users_in_group:
                    text, image_url = handler.execute(user=user)
                    if text:
                        self._distribute_content([user], theme_config, text, image_url)
                    else:
                        logging.warning(
                            f"No content for user '{user.get('description')}' and theme '{theme}'."
                        )

            else:
                logging.info(f"Processing '{theme}' with shared content generation.")
                text, image_url = handler.execute()
                if text:
                    self._distribute_content(
                        users_in_group, theme_config, text, image_url
                    )

        return True


# ============================================================================
# Orchestrator and Public Entry Point
# ============================================================================


class JobOrchestrator:
    """Encapsulates all logic and state for a single job execution."""

    def __init__(self, time_key: str, user_filter: Optional[List[str]] = None) -> None:
        """
        Initializes the orchestrator and its processing pipeline.

        Args:
            time_key (str): The schedule key for the current job.
            user_filter (Optional[List[str]]): An optional list of users to target.
        """
        self._time_key = time_key
        self._user_filter = user_filter
        self._pipeline = [
            InitializeServices(),
            PrepareContentGroups(),
            ProcessAndDistributeGroups(),
        ]

    def _get_memory_usage(self) -> str:
        """
        Gets the current memory usage of the process.

        Returns:
            str: A string representing the memory usage in megabytes.
        """
        process = psutil.Process(os.getpid())
        return f"{process.memory_info().rss / 1024**2:.2f} MB"

    def execute(self) -> None:
        """
        Orchestrates the entire job by running the processing pipeline,
        wrapped in logging and error handling.
        """
        logging.info(
            f"--- 🟢 Starting job for '{self._time_key}'. Memory: {self._get_memory_usage()} ---"
        )
        try:
            context = ProcessingContext(self._time_key, self._user_filter)
            for step in self._pipeline:
                if not step.execute(context):
                    logging.error(f"Pipeline halted at step: {step.__class__.__name__}")
                    break
        finally:
            logging.info(
                f"--- 🏁 Job for '{self._time_key}' finished. Memory: {self._get_memory_usage()} ---"
            )


def generate_and_send(time_key: str, user_filter: Optional[List[str]] = None) -> None:
    """
    Public-facing entry point that creates and runs a JobOrchestrator.

    Args:
        time_key (str): The schedule key (e.g., 'time1') to be processed.
        user_filter (Optional[list[str]]): An optional list of user descriptions.
    """
    orchestrator = JobOrchestrator(time_key, user_filter)
    orchestrator.execute()


# End of src/core.py (v. 0042)
