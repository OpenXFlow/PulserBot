# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/channels/telegram_channel.py
"""
A channel module for handling message delivery via the Telegram Bot API.

This module defines the TelegramChannel class, which encapsulates all logic
for sending both text-only messages and messages with photos.
"""

import logging
from typing import Optional

import httpx

from .. import config


class TelegramChannel:
    """
    Encapsulates all logic for sending messages to the Telegram Bot API.

    This class manages the API token and provides consistent methods for
    sending different types of messages, complete with error handling.

    Attributes:
        _token (str): The Telegram Bot API token.
    """

    def __init__(self) -> None:
        """Initializes the TelegramChannel."""
        self._token = config.TELEGRAM_TOKEN

    def send_message(self, chat_id: str, text: str) -> bool:
        """
        Sends a text-only message to a specific Telegram user.

        Args:
            chat_id (str): The user's unique Telegram chat identifier.
            text (str): The message content to send. HTML formatting is supported.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        if not all([self._token, chat_id, text]):
            logging.warning("send_message called with missing token, chat_id, or text.")
            return False

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        cleaned_text = text.replace("<br>", "\n").replace("<br />", "\n")

        payload = {
            "chat_id": chat_id,
            "text": cleaned_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
            logging.info(
                f"Successfully sent text message to chat_id ending '...{chat_id[-4:]}'."
            )
            return True
        except httpx.HTTPStatusError as e:
            logging.error(
                f"HTTP error sending text message: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logging.error(f"Network error sending text message: {e}")
        except Exception:
            logging.exception("An unexpected error occurred in send_message.")

        return False

    def send_photo(
        self, chat_id: str, photo_url: str, caption: Optional[str] = None
    ) -> bool:
        """
        Sends a message with a photo and an optional caption to a Telegram user.

        Args:
            chat_id (str): The user's unique Telegram chat identifier.
            photo_url (str): The URL of the photo to send. Must be publicly accessible.
            caption (Optional[str]): The text to be shown under the photo.
                                     HTML formatting is supported.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        if not all([self._token, chat_id, photo_url]):
            logging.warning(
                "send_photo called with missing token, chat_id, or photo_url."
            )
            return False

        url = f"https://api.telegram.org/bot{self._token}/sendPhoto"
        cleaned_caption = (caption or "").replace("<br>", "\n").replace("<br />", "\n")

        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": cleaned_caption,
            "parse_mode": "HTML",
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
            logging.info(
                f"Successfully sent photo message to chat_id ending '...{chat_id[-4:]}'."
            )
            return True
        except httpx.HTTPStatusError as e:
            logging.error(
                f"HTTP error sending photo: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logging.error(f"Network error sending photo: {e}")
        except Exception:
            logging.exception("An unexpected error occurred in send_photo.")

        return False


# --- Singleton Instance ---
_telegram_channel_instance = TelegramChannel()


# --- Public-facing Functions ---
def send_message(chat_id: str, text: str) -> bool:
    """
    Public-facing function to send a text-only message.
    Delegates the call to the singleton instance of TelegramChannel.

    Args:
        chat_id (str): The user's Telegram chat ID.
        text (str): The message content.

    Returns:
        bool: True on success, False on failure.
    """
    return _telegram_channel_instance.send_message(chat_id, text)


def send_photo(chat_id: str, photo_url: str, caption: Optional[str] = None) -> bool:
    """
    Public-facing function to send a message with a photo.
    Delegates the call to the singleton instance of TelegramChannel.

    Args:
        chat_id (str): The user's Telegram chat ID.
        photo_url (str): The URL of the photo.
        caption (Optional[str]): The text caption for the photo.

    Returns:
        bool: True on success, False on failure.
    """
    return _telegram_channel_instance.send_photo(chat_id, photo_url, caption)


# End of src/channels/telegram_channel.py (v. 0004)
