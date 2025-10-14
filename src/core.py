# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/core.py
"""
The core orchestration module for the YourDailyPulse application.

This module defines the JobProcessor class, which encapsulates all the logic
for processing a single job run, and a simple entry point function
'generate_and_send' that utilizes this class.
"""

import importlib
import logging
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple, cast

import psutil

from . import config
from .channels import telegram_channel


class JobProcessor:
    """
    Encapsulates all logic and state for a single job execution.

    This class is responsible for preparing user groups, processing each group
    by dispatching to the correct strategy, and distributing the final content.

    Attributes:
        time_key (str): The schedule key for the current job.
        user_filter (list[str] | None): An optional filter for specific users.
        app_config (Dict[str, Any]): The loaded application configuration.
        tz (ZoneInfo): The active timezone for the application.
    """

    def __init__(self, time_key: str, user_filter: list[str] | None = None) -> None:
        """
        Initializes the JobProcessor.

        Args:
            time_key (str): The schedule key (e.g., 'time1') to be processed.
            user_filter (list[str] | None): Optional list of user descriptions to filter for.
        """
        self.time_key = time_key
        self.user_filter = user_filter
        self.app_config, self.tz = config.load_app_config()

    def _get_memory_usage(self) -> str:
        """
        Gets the current memory usage of the process in a readable format.

        Returns:
            str: A string representing the memory usage in megabytes (e.g., "50.12 MB").
        """
        process = psutil.Process(os.getpid())
        return f"{process.memory_info().rss / 1024**2:.2f} MB"

    def _prepare_content_groups(
        self,
    ) -> defaultdict[Tuple[str, str], List[Dict[str, Any]]] | None:
        """
        Filters users and groups them by (theme, language).

        This method prepares the main workload by identifying which users are active,
        subscribed to the current time slot, and then groups them to ensure that
        content is generated only once per unique (theme, language) combination.

        Returns:
            defaultdict[Tuple[str, str], List[Dict[str, Any]]] | None: A dictionary where keys
            are (theme, language) tuples and values are lists of user objects, or None if
            no users are subscribed for this run.
        """
        active_users = [
            u for u in self.app_config.get("users", []) if u.get("active", True)
        ]
        target_users = active_users

        if self.user_filter:
            logging.info(
                f"Applying user filter for: {self.user_filter}",
                extra={"filter": self.user_filter},
            )
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

        content_groups = defaultdict(list)
        for user in subscribed_users:
            themes = user["subscriptions"].get(self.time_key, [])
            lang = user.get("language", "slovak")
            for theme in themes:
                content_groups[(theme, lang)].append(user)

        group_keys = [f"{theme}/{lang}" for theme, lang in content_groups.keys()]
        logging.info(
            f"Found {len(group_keys)} content groups.", extra={"groups": group_keys}
        )
        return content_groups

    def _process_group(
        self, theme: str, lang: str, theme_config: Dict[str, Any]
    ) -> Tuple[str | None, str | None]:
        """
        Dispatches processing to the correct strategy module.

        This function dynamically imports the appropriate strategy module from the
        'src/prompt_type/' package based on the theme's 'type' and calls its
        'process' function.

        Args:
            theme (str): The name of the theme being processed.
            lang (str): The language key for the content.
            theme_config (Dict[str, Any]): The configuration dictionary for the theme.

        Returns:
            Tuple[str | None, str | None]: A tuple containing the generated
            reflection text and an image URL, or (None, None) if processing fails.
        """
        theme_type = theme_config.get("type", "llm_static")
        log_context = {"theme": theme, "language": lang, "type": theme_type}

        theme_config["theme_name"] = theme

        try:
            strategy_module = importlib.import_module(
                f".prompt_type.{theme_type}", package="src"
            )

            if not hasattr(strategy_module, "process") or not callable(
                getattr(strategy_module, "process")
            ):
                logging.error(
                    f"Strategy module '{theme_type}' is missing a callable 'process' function.",
                    extra=log_context,
                )
                return None, None

            result = strategy_module.process(theme_config, lang)
            return cast(Tuple[str | None, str | None], result)

        except ImportError:
            logging.error(
                f"Strategy module for type '{theme_type}' not found. Skipping.",
                extra=log_context,
            )
            return None, None

    def _distribute_content(
        self, users: List[Dict[str, Any]], theme: str, text: str, image_url: str | None
    ) -> None:
        """
        Distributes the generated content to all users in a group via Telegram.

        Args:
            users (List[Dict[str, Any]]): A list of user objects to send the content to.
            theme (str): The name of the theme being distributed.
            text (str): The final, formatted message text.
            image_url (str | None): The URL of an image to send, if available.
        """
        cleaned_text = text.strip().replace("</b><br>", "</b>")
        for user in users:
            logging.info(
                f"Distributing content for '{theme}' to '{user.get('description')}'.",
                extra={"user": user.get("description")},
            )
            for channel in user.get("channels", []):
                if channel.get("platform") == "telegram":
                    if image_url:
                        telegram_channel.send_photo(
                            channel.get("identifier"), image_url, cleaned_text
                        )
                    else:
                        telegram_channel.send_message(
                            channel.get("identifier"), cleaned_text
                        )

    def _log_job_completion(self) -> None:
        """Logs the final message indicating the job has finished."""
        logging.info(
            f"--- 🏁 Job for '{self.time_key}' finished. Memory: {self._get_memory_usage()} ---",
            extra={"time_key": self.time_key},
        )

    def execute(self) -> None:
        """
        Orchestrates the entire job execution from preparation to distribution.

        This is the main public method of the class that should be called to run the job.
        It handles the complete workflow and ensures proper logging at the end.
        """
        logging.info(
            f"--- 🟢 Starting job for '{self.time_key}'. Memory: {self._get_memory_usage()} ---",
            extra={"time_key": self.time_key},
        )

        try:
            if not self.app_config:
                logging.error("Aborting job: missing application configuration.")
                return

            content_groups = self._prepare_content_groups()
            if not content_groups:
                return

            for (theme, lang), users_in_group in content_groups.items():
                log_context = {
                    "theme": theme,
                    "language": lang,
                    "users": [u["description"] for u in users_in_group],
                }
                try:
                    logging.info(
                        f"--- Processing group: '{theme}' in '{lang}' ---",
                        extra=log_context,
                    )
                    theme_config = self.app_config.get("themes", {}).get(theme)
                    if not theme_config:
                        logging.error(
                            "Theme config not found. Skipping.", extra=log_context
                        )
                        continue

                    reflection_text, image_url = self._process_group(
                        theme, lang, theme_config
                    )

                    if reflection_text:
                        self._distribute_content(
                            users_in_group, theme, reflection_text, image_url
                        )

                except Exception as e:
                    logging.exception(
                        f"Critical error processing group '{theme}/{lang}': %s",
                        e,
                        extra=log_context,
                    )
        finally:
            self._log_job_completion()


def generate_and_send(time_key: str, user_filter: list[str] | None = None) -> None:
    """
    Public-facing entry point that creates and runs a JobProcessor.

    Args:
        time_key (str): The schedule key (e.g., 'time1') to be processed.
        user_filter (list[str] | None): An optional list of user descriptions to filter for.
    """
    processor = JobProcessor(time_key, user_filter)
    processor.execute()


# End of src/core.py (v. 0025)
