# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/core.py
"""
The core orchestration module for the YourDailyPulse application.
Updated to support:
- AsyncIO distribution
- Per-user Timezone calculations (World-Ready)
- Day-of-week filtering
- Mixed data structure support (Legacy Strings vs New Objects)
- DETAILED DEBUG LOGGING for troubleshooting
- IGNORE TIME flag for testing
- FIXED: Type annotations for inner async functions
"""

import asyncio
import importlib
import logging
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Type

import psutil

from . import config
from .channels import telegram_channel
from .config import ZoneInfo
from .handlers._base.base_handler import BaseHandler
from .services import firestore_service, sheets_service, weather_service

# A map to resolve handler class names to their module paths
HANDLER_MAP = {
    "BibleHandler": "src.handlers.llm.bible_handler",
    "BibleStudyHandler": "src.handlers.llm.bible_study_handler",
    "PhilosophyHandler": "src.handlers.llm.philosophy_handler",
    "LLMDynamicHandler": "src.handlers.llm.llm_dynamic_handler",
    "SimpleStaticHandler": "src.handlers.template.simple_static_handler",
    "DynamicTemplateHandler": "src.handlers.template.dynamic_template_handler",
    "UserDefinedHandler": "src.handlers.template.user_defined_handler",
}

# ============================================================================
# Processing Context and Pipeline Steps
# ============================================================================


class ProcessingContext:
    """A state container that holds data across the job processing pipeline."""

    def __init__(
        self,
        time_key_label: str,
        user_filter: Optional[List[str]] = None,
        force_update: bool = False,
        ignore_time_checks: bool = False,
    ) -> None:
        """
        Initializes the context.

        Args:
            time_key_label (str): Label for logging (e.g. 'time6' or 'auto').
            user_filter (Optional[List[str]]): List of emails to process.
            force_update (bool): If True, ignores cache.
            ignore_time_checks (bool): If True, forces execution of time_key_label regardless of real time.
        """
        self.time_key_label = time_key_label
        self.user_filter = user_filter
        self.force_update = force_update
        self.ignore_time_checks = ignore_time_checks
        self.app_config, self.tz = config.load_app_config()

        # Global UTC reference time for this run
        self.now_utc = datetime.now(timezone.utc)

        # --- HYBRID CONFIGURATION LOADING ---
        # Pass force_update to refresh user cache if needed
        firestore_users = firestore_service.get_active_users(
            force_refresh=self.force_update
        )

        if firestore_users:
            self.app_config["users"] = firestore_users
            logging.info(
                f"Context: Injected {len(firestore_users)} users from Firestore."
            )
        else:
            logging.warning(
                "Context: Firestore returned no users. Using fallback from config.json (if any)."
            )
        # ------------------------------------

        self.content_groups: Optional[
            defaultdict[Tuple[str, str], List[Dict[str, Any]]]
        ] = None


class ProcessingStep(ABC):
    """An abstract base class for a single step in the job processing pipeline."""

    @abstractmethod
    async def execute(self, context: ProcessingContext) -> bool:
        pass


class InitializeServices(ProcessingStep):
    """Pipeline step to initialize necessary external services."""

    async def execute(self, context: ProcessingContext) -> bool:
        if not context.app_config:
            logging.error("Aborting job: missing application configuration.")
            return False
        sheets_service.initialize_sheets_service(context.app_config)
        return True


class PrepareContentGroups(ProcessingStep):
    """
    Pipeline step to filter users and group them by content needs.
    """

    async def execute(self, context: ProcessingContext) -> bool:
        active_users = [
            u for u in context.app_config.get("users", []) if u.get("active", True)
        ]
        target_users = active_users

        if context.user_filter:
            target_users = [
                u for u in active_users if u.get("description") in context.user_filter
            ]
            if not target_users:
                available = [u.get("description") for u in active_users]
                logging.warning(
                    f"No active users found for filter '{context.user_filter}'. Available: {available}"
                )
                return False

        groups: defaultdict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
        processed_count = 0

        days_map = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thu",
            4: "Fri",
            5: "Sat",
            6: "Sun",
        }

        for user in target_users:
            user_email = user.get("description", "Unknown")

            # 1. Determine User's Local Time
            user_tz_str = user.get("timezone", "Europe/Bratislava")
            try:
                user_tz = ZoneInfo(user_tz_str)
            except Exception:
                logging.warning(
                    f"Invalid timezone '{user_tz_str}' for {user_email}. Defaulting to Bratislava."
                )
                user_tz = ZoneInfo("Europe/Bratislava")

            user_local_time = context.now_utc.astimezone(user_tz)
            current_hour = user_local_time.hour
            current_weekday = user_local_time.weekday()

            # --- LOGIC: Time Selection ---
            # If ignore_time_checks is True AND we have a valid time label (e.g., 'time6'), use it.
            # Otherwise, calculate from real time.
            if context.ignore_time_checks and context.time_key_label.startswith("time"):
                target_time_key = context.time_key_label
                logging.debug(
                    f"OVERRIDE: Forcing '{target_time_key}' for {user_email} (Ignoring real time {current_hour}:00)."
                )
            else:
                target_time_key = f"time{current_hour}"

            # DEBUG LOG
            if not context.ignore_time_checks:
                logging.debug(
                    f"User: {user_email} | TZ: {user_tz_str} | "
                    f"Local Time: {user_local_time.strftime('%H:%M')} ({days_map[current_weekday]}) | "
                    f"Target Key: {target_time_key}"
                )

            subscriptions = user.get("subscriptions", {})

            # Check subscriptions
            if target_time_key in subscriptions:
                theme_list = subscriptions[target_time_key]

                if isinstance(theme_list, list):
                    for item in theme_list:
                        theme_id = ""
                        allowed_days = []

                        if isinstance(item, dict):
                            theme_id = item.get("theme", "")
                            allowed_days = item.get("days", [])

                            # --- DAY FILTER LOGIC ---
                            # Even with ignore_time, we usually respect days (unless we want 'ignore_all').
                            # Let's respect days for now, as 'ignore_time' implies correcting the hour, not the day.
                            if allowed_days and current_weekday not in allowed_days:
                                logging.debug(
                                    f"  -> SKIPPING '{theme_id}': Today is {days_map[current_weekday]}, "
                                    f"but allowed days are {allowed_days}."
                                )
                                continue

                        elif isinstance(item, str):
                            theme_id = item

                        if not theme_id:
                            continue

                        # Determine Language
                        if theme_id.endswith("_en") or theme_id.endswith("_english"):
                            item_lang = "english"
                        elif theme_id.endswith("_sk") or theme_id.endswith("_slovak"):
                            item_lang = "slovak"
                        elif theme_id.endswith("_de") or theme_id.endswith(
                            "_german"
                        ):  # <--- PRIDANÉ
                            item_lang = "german"
                        else:
                            item_lang = user.get("language", "slovak")

                        groups[(theme_id, item_lang)].append(user)
                        processed_count += 1
                        logging.debug(
                            f"  -> MATCH: Scheduled '{theme_id}' ({item_lang})."
                        )

            else:
                if context.user_filter:
                    logging.debug(
                        f"  -> No subscription found for key '{target_time_key}'."
                    )

        logging.info(
            f"Scheduled {processed_count} messages across {len(groups)} unique content groups."
        )
        context.content_groups = groups
        return True


class ProcessAndDistributeGroups(ProcessingStep):
    """
    The main pipeline step that processes each content group and distributes asynchronously.
    """

    def _instantiate_handler(
        self, theme: str, lang: str, theme_config: Dict[str, Any]
    ) -> Optional[BaseHandler]:
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

    async def _personalize_weather_content(
        self, text: str, user: Dict[str, Any], theme_lang: str
    ) -> str:
        """Replaces weather placeholders asynchronously."""
        final_text = text
        lang_code = "en" if theme_lang == "english" else "sk"

        weather_config = user.get("weather", {})

        async def get_forecast_safe(loc_str: str) -> str:
            return await weather_service.get_weather_forecast(
                loc_str, weather_config.get("units", "metric"), lang_code
            )

        if "locations" in weather_config and isinstance(
            weather_config.get("locations"), list
        ):
            for i, loc_config in enumerate(weather_config["locations"]):
                location = loc_config.get("location")
                if not location:
                    continue
                location_name = location.split(",")[0]

                forecast = await get_forecast_safe(location)

                final_text = final_text.replace(
                    f"{{USER_WEATHER_LOCATION_{i}}}", location_name
                )
                final_text = final_text.replace(
                    f"{{USER_WEATHER_FORECAST_{i}}}", forecast
                )

                if i == 0:
                    final_text = final_text.replace(
                        "{USER_WEATHER_LOCATION}", location_name
                    )
                    final_text = final_text.replace("{USER_WEATHER_FORECAST}", forecast)

        elif location := weather_config.get("location"):
            location_name = location.split(",")[0]
            forecast = await get_forecast_safe(location)
            final_text = final_text.replace("{USER_WEATHER_LOCATION}", location_name)
            final_text = final_text.replace("{USER_WEATHER_FORECAST}", forecast)

        return final_text

    async def _send_to_single_user(
        self,
        user: Dict[str, Any],
        text: str,
        image_url: Optional[str],
        theme_name: str,
        theme_lang: str,
        semaphore: asyncio.Semaphore,
    ) -> None:
        async with semaphore:
            final_text = await self._personalize_weather_content(text, user, theme_lang)

            logging.info(f"Distributing '{theme_name}' to '{user.get('description')}'.")

            for channel in user.get("channels", []):
                if channel.get("platform") == "telegram":
                    identifier = channel.get("identifier")
                    if image_url:
                        await telegram_channel.send_photo(
                            identifier, image_url, final_text
                        )
                    else:
                        await telegram_channel.send_message(identifier, final_text)

    async def _distribute_content_async(
        self,
        users: List[Dict[str, Any]],
        theme_config: Dict[str, Any],
        text: str,
        image_url: Optional[str],
        theme_lang: str,
    ) -> None:
        theme_name = theme_config.get("theme_name", "Unknown")
        semaphore = asyncio.Semaphore(20)

        tasks = []
        for user in users:
            tasks.append(
                self._send_to_single_user(
                    user, text, image_url, theme_name, theme_lang, semaphore
                )
            )

        if tasks:
            await asyncio.gather(*tasks)

    async def execute(self, context: ProcessingContext) -> bool:
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
                logging.info(f"Processing '{theme}' with per-user generation.")

                semaphore = asyncio.Semaphore(20)
                tasks = []

                for user in users_in_group:
                    # --- FIX: Added type annotations for inner function 'u' ---
                    async def process_single(u: Dict[str, Any]) -> None:
                        async with semaphore:
                            # Run handler for specific user (synchronous part wrapped if needed)
                            text, image_url = handler.execute(
                                user=u, force_update=context.force_update
                            )

                            if text:
                                # Personalize and Send
                                final_text = await self._personalize_weather_content(
                                    text, u, lang
                                )
                                logging.info(
                                    f"Distributing '{theme}' to '{u.get('description')}'."
                                )

                                for channel in u.get("channels", []):
                                    if channel.get("platform") == "telegram":
                                        identifier = channel.get("identifier")
                                        if image_url:
                                            await telegram_channel.send_photo(
                                                identifier, image_url, final_text
                                            )
                                        else:
                                            await telegram_channel.send_message(
                                                identifier, final_text
                                            )

                    tasks.append(process_single(user))

                if tasks:
                    await asyncio.gather(*tasks)

            else:
                # Shared Content (Standard Strategy)
                logging.info(f"Processing '{theme}' with shared content generation.")
                # Execute once (cached)
                text, image_url = handler.execute(force_update=context.force_update)

                if text:
                    logging.info(
                        f"Starting async distribution for '{theme}' to {len(users_in_group)} users."
                    )
                    await self._distribute_content_async(
                        users_in_group, theme_config, text, image_url, lang
                    )
                else:
                    logging.warning(
                        f"No content generated for theme '{theme}'. Skipping distribution."
                    )

        return True


# ============================================================================
# Orchestrator and Public Entry Point
# ============================================================================


class JobOrchestrator:
    """Encapsulates all logic and state for a single job execution."""

    def __init__(
        self,
        time_key_label: str,
        user_filter: Optional[List[str]] = None,
        force_update: bool = False,
        ignore_time_checks: bool = False,
    ) -> None:
        self._time_key_label = time_key_label
        self._user_filter = user_filter
        self._force_update = force_update
        self._ignore_time_checks = ignore_time_checks
        self._pipeline = [
            InitializeServices(),
            PrepareContentGroups(),
            ProcessAndDistributeGroups(),
        ]

    def _get_memory_usage(self) -> str:
        process = psutil.Process(os.getpid())
        return f"{process.memory_info().rss / 1024**2:.2f} MB"

    async def execute_async(self) -> None:
        mode_str = ""
        if self._force_update:
            mode_str += " [FORCE CACHE]"
        if self._ignore_time_checks:
            mode_str += " [IGNORE TIME]"

        logging.info(
            f"--- 🟢 Starting Job ({self._time_key_label}){mode_str}. Memory: {self._get_memory_usage()} ---"
        )
        try:
            context = ProcessingContext(
                self._time_key_label,
                self._user_filter,
                self._force_update,
                self._ignore_time_checks,
            )
            for step in self._pipeline:
                if not await step.execute(context):
                    break
        except Exception as e:
            logging.exception(f"Critical error in JobOrchestrator: {e}")
        finally:
            logging.info(f"--- 🏁 Job Finished. Memory: {self._get_memory_usage()} ---")


async def generate_and_send_async(
    time_key: str = "auto",
    user_filter: Optional[List[str]] = None,
    force_update: bool = False,
    ignore_time_checks: bool = False,
) -> None:
    """
    Public-facing async entry point.
    """
    orchestrator = JobOrchestrator(
        time_key, user_filter, force_update, ignore_time_checks
    )
    await orchestrator.execute_async()


# End of src/core.py (v. 0056)
