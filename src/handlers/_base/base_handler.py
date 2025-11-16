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
from typing import Any, Dict, Optional, Tuple


class BaseHandler(ABC):
    """
    An abstract base class for all theme processing handlers.

    This class defines the common constructor and the main `execute` method,
    which includes universal error handling. Each concrete handler must
    implement the `_process` method, which contains the specific logic
    for that theme type.

    Attributes:
        theme_config (Dict[str, Any]): The configuration for the specific theme.
        lang (str): The language key for the content.
        app_config (Dict[str, Any]): The global application configuration, loaded
            within the handler if needed.
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

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing the final
            formatted text and an optional image URL. Should return (None, None)
            on failure.
        """
        raise NotImplementedError

    def execute(
        self, user: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Executes the handler's logic with centralized error handling.

        This is the public entry point for all handlers. It calls the specific
        `_process` method, passing along any keyword arguments, and wraps it
        in a try-except block to catch unexpected errors.

        Args:
            user (Optional[Dict[str, Any]]): An optional user object for personalization.
            **kwargs: Additional keyword arguments for specific handlers.

        Returns:
            Tuple[Optional[str], Optional[str]]: The result from the `_process`
            method, or (None, None) if a critical error occurs.
        """
        try:
            # Prepare arguments for the _process method.
            process_kwargs = kwargs
            if user is not None:
                process_kwargs["user"] = user
            # Pass arguments down to the process method.
            return self._process(**process_kwargs)
        except Exception:
            theme_name = self.theme_config.get("theme_name", "Unknown Theme")
            logging.exception(
                f"A critical, unhandled error occurred in the handler for theme '{theme_name}'."
            )
            return None, None


# End of src/handlers/_base/base_handler.py (v. 0003)
