# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/channels/telegram_channel.py
"""
A channel module for handling message delivery via the Telegram Bot API.
Updated to support asynchronous I/O for high-performance batch sending.
Includes automatic footer with configuration link and robust HTML sanitization.
"""

import logging
import re
from typing import Optional

import httpx

from .. import config

# Constant for the configuration link appended to every message
# Updated: Only one newline character as requested.
CONFIG_LINK_HTML = (
    '\n🌻 <a href="https://key-perigee-474220-u3.web.app/login.html">YDP</a>'
)


class TelegramChannel:
    """
    Encapsulates all logic for sending messages to the Telegram Bot API asynchronously.
    """

    def __init__(self) -> None:
        """
        Initializes the TelegramChannel.
        """
        self._token = config.TELEGRAM_TOKEN

    def _sanitize_html(self, text: str) -> str:
        """
        Removes unsupported HTML tags and cleans up whitespace for Telegram.
        This remains synchronous as it is a CPU-bound string operation.
        """
        # 1. Remove tags that Telegram strictly forbids and cause Error 400
        # The LLM sometimes generates <footer> or <header> tags which break delivery.
        cleaned_text = (
            text.replace("<footer>", "")
            .replace("</footer>", "")
            .replace("<header>", "")
            .replace("</header>", "")
            .replace("<ul>", "")
            .replace("</ul>", "")
            .replace("<ol>", "")
            .replace("</ol>", "")
            .replace("<li>", "\n• ")
            .replace("</li>", "")
            .replace("<p>", "")
            .replace("</p>", "\n")
            .replace("<br>", "\n")
            .replace("<br />", "\n")
        )

        # 2. Remove blank lines after bold headers to save space
        cleaned_text = re.sub(r"(</b>\n)\n+", r"\1", cleaned_text)

        # 3. Collapse multiple newlines into max two
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        return cleaned_text.strip()

    async def send_message(self, chat_id: str, text: str) -> bool:
        """
        Sends a text-only message to a specific Telegram user asynchronously.
        Automatically appends the configuration link.
        """
        if not all([self._token, chat_id, text]):
            logging.warning("send_message called with missing token, chat_id, or text.")
            return False

        # Append footer and sanitize
        text_with_footer = text + CONFIG_LINK_HTML
        cleaned_text = self._sanitize_html(text_with_footer)

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": cleaned_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
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

    async def send_photo(
        self, chat_id: str, photo_url: str, caption: Optional[str] = None
    ) -> bool:
        """
        Sends a message with a photo asynchronously.
        Automatically handles captions longer than 1024 characters by splitting.
        """
        if not all([self._token, chat_id, photo_url]):
            logging.warning(
                "send_photo called with missing token, chat_id, or photo_url."
            )
            return False

        raw_caption = caption or ""

        # Prepare the caption with footer to check length
        caption_with_footer = raw_caption + CONFIG_LINK_HTML
        cleaned_caption_with_footer = self._sanitize_html(caption_with_footer)

        # --- INTELLIGENT SPLIT LOGIC ---
        # Telegram caption limit is 1024 chars. We use 1000 for safety.
        if len(cleaned_caption_with_footer) > 1000:
            logging.info(
                "Caption (with footer) too long for photo (>1000 chars). Splitting message."
            )

            # 1. Send Photo ONLY (await)
            photo_sent = await self._send_photo_only(chat_id, photo_url)
            if not photo_sent:
                return False

            # 2. Send Text (await)
            # We pass the ORIGINAL raw_caption.
            # The send_message method will append the footer and sanitize it automatically.
            return await self.send_message(chat_id, raw_caption)

        # --- STANDARD SEND (Photo + Caption) ---
        # Use the pre-calculated cleaned caption that includes the footer
        url = f"https://api.telegram.org/bot{self._token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": cleaned_caption_with_footer,
            "parse_mode": "HTML",
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, json=payload)
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

    async def _send_photo_only(self, chat_id: str, photo_url: str) -> bool:
        """Helper to send just the photo asynchronously."""
        url = f"https://api.telegram.org/bot{self._token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Error sending standalone photo: {e}")
            return False


_telegram_channel_instance = TelegramChannel()


# Public wrappers must now be async too
async def send_message(chat_id: str, text: str) -> bool:
    return await _telegram_channel_instance.send_message(chat_id, text)


async def send_photo(
    chat_id: str, photo_url: str, caption: Optional[str] = None
) -> bool:
    return await _telegram_channel_instance.send_photo(chat_id, photo_url, caption)


# End of src/channels/telegram_channel.py (v. 0018)
