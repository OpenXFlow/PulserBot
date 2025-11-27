# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/_base/base_handler.py
"""
Defines the abstract base class for all content handling strategies.

This module provides the `BaseHandler` class, which serves as a common
interface for all specific handler implementations. It ensures that every
handler has a consistent structure and entry point.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ...config import TIMEZONE_STR, ZoneInfo
from ...services import firestore_service


class BaseHandler(ABC):
    """
    An abstract base class for all theme processing handlers.

    This class defines the common constructor and the main `execute` method,
    which includes universal error handling and caching logic. Each concrete
    handler must implement the `_process` method.

    Attributes:
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        lang (str): The language key for the content.
    """

    def __init__(self, theme_config: Dict[str, Any], lang: str) -> None:
        """
        Initializes the base handler.

        Args:
            theme_config (Dict[str, Any]): The configuration dictionary for the
                specific theme being processed.
            lang (str): The language key for the content (e.g., 'slovak').
        """
        self.theme_config = theme_config
        self.lang = lang
        # app_config is loaded on demand by child classes if they need it.

    @abstractmethod
    def _process(self, **kwargs: Any) -> Tuple[Optional[str], Optional[str]]:
        """
        The core logic for the specific handler. Must be implemented by subclasses.

        This method is responsible for fetching data, processing it, and generating
        the final content.

        Args:
            **kwargs: Arbitrary keyword arguments passed from execute().

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing the final
            formatted text and an optional image URL. Should return (None, None)
            on failure.
        """
        raise NotImplementedError

    def execute(
        self,
        user: Optional[Dict[str, Any]] = None,
        force_update: bool = False,
        **kwargs: Any,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Executes the handler's logic with centralized error handling AND caching.

        This is the public entry point for all handlers. It manages the flow:
        1. Check Cache (if enabled).
        2. If miss, call `_process`.
        3. Save to Cache (if enabled).

        Args:
            user (Optional[Dict[str, Any]]): An optional user object for personalization.
            force_update (bool): If True, ignores existing cache and forces regeneration.
            **kwargs: Additional keyword arguments for specific handlers.

        Returns:
            Tuple[Optional[str], Optional[str]]: The result (text, image_url),
            or (None, None) if a critical error occurs.
        """

        # --- CACHING LOGIC START ---
        theme_id = self.theme_config.get("theme_name")

        # Validate theme_id
        if not theme_id or not isinstance(theme_id, str):
            logging.error(
                "Critical: 'theme_name' is missing or invalid in handler config."
            )
            return None, None

        # Determine today's date in the correct timezone
        try:
            tz = ZoneInfo(TIMEZONE_STR)
        except Exception:
            logging.warning(f"Invalid timezone '{TIMEZONE_STR}', defaulting to UTC.")
            tz = ZoneInfo("UTC")

        today_str = datetime.now(tz).strftime("%Y-%m-%d")

        # --- NEW: Check if caching is enabled for this theme ---
        # Default is True. We disable it for highly personalized content (like user_reminder).
        use_cache = self.theme_config.get("use_cache", True)

        # 1. Try to get from Cache (ONLY if allowed and not forced)
        if use_cache and not force_update:
            cached_data = firestore_service.get_cached_content(theme_id, today_str)

            if cached_data:
                # CACHE HIT: Return stored data
                return cached_data.get("text"), cached_data.get("image_url")
        # ---------------------------

        try:
            # Prepare arguments for the _process method.
            process_kwargs = kwargs
            if user is not None:
                process_kwargs["user"] = user

            # 2. CACHE MISS (or Forced, or Cache Disabled): Run generation
            text, image_url = self._process(**process_kwargs)

            # 3. Save to Cache (only if successful AND caching is enabled)
            if text and use_cache:
                cache_payload = {"text": text, "image_url": image_url}
                firestore_service.save_cached_content(
                    theme_id, today_str, cache_payload
                )

            return text, image_url

        except Exception:
            logging.exception(
                f"A critical, unhandled error occurred in the handler for theme '{theme_id}'."
            )
            return None, None


# End of src/handlers/_base/base_handler.py (v. 0007)
