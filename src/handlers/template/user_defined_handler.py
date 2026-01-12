# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/handlers/template/user_defined_handler.py
"""
Handler for the 'user_reminder' theme.
This handler fetches content directly from the user's Firestore profile.

SPECIAL LOGIC:
- Text is generated per-user (never cached globally).
- Image is fetched from Unsplash but CACHED globally for the day to save API calls.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from babel.dates import format_date

from ...config import TIMEZONE_STR, ZoneInfo
from ...services import firestore_service, image_service
from .._base.base_handler import BaseHandler


class UserDefinedHandler(BaseHandler):
    """
    Handles user-defined content with shared image caching.
    Supports SK, EN, and DE localization.
    """

    TRANSLATIONS = {
        "slovak": {
            "links_header": "<b>🔗 Moje Odkazy:</b>",
            "header_prefix": "Pripomienka",
        },
        "english": {"links_header": "<b>🔗 My Links:</b>", "header_prefix": "Reminder"},
        "german": {
            "links_header": "<b>🔗 Meine Links:</b>",
            "header_prefix": "Erinnerung",
        },
    }

    def _build_html_message(self, content_data: Dict[str, Any]) -> str:
        """
        Constructs the final HTML message from user data with dynamic date header.
        """
        # Determine language key
        lang_key = self.lang if self.lang in self.TRANSLATIONS else "slovak"
        t = self.TRANSLATIONS[lang_key]

        # Dynamic Date Header
        try:
            tz = ZoneInfo(TIMEZONE_STR)
        except Exception:
            tz = ZoneInfo("UTC")

        now = datetime.now(tz)
        date_str = now.strftime("%d.%m.%Y")

        # Determine locale for day name
        if lang_key == "english":
            locale = "en_US"
        elif lang_key == "german":
            locale = "de_DE"
        else:
            locale = "sk_SK"

        day_name = format_date(now, "EEEE", locale=locale).capitalize()

        header = f"<b>🔔 {t['header_prefix']} {date_str}, {day_name}</b>"

        parts = []
        parts.append(f"{header}\n")

        # Text Blocks
        blocks = content_data.get("blocks", [])
        for block in blocks:
            if block and str(block).strip():
                parts.append(f"{str(block).strip()}\n")

        # Links
        links = content_data.get("links", [])
        valid_links = []
        for link in links:
            title = link.get("title", "").strip()
            url = link.get("url", "").strip()
            if title and url:
                valid_links.append(f'• <a href="{url}">{title}</a>')

        if valid_links:
            parts.append(t["links_header"])
            parts.extend(valid_links)

        return "\n".join(parts)

    def _get_shared_image(self) -> Tuple[Optional[str], str]:
        """
        Retrieves a shared image for the day (Cached in Firestore).
        This prevents fetching 1000 Unsplash images for 1000 users.
        """
        # 1. Calculate Cache Key
        try:
            tz = ZoneInfo(TIMEZONE_STR)
        except Exception:
            tz = ZoneInfo("UTC")
        today_str = datetime.now(tz).strftime("%Y-%m-%d")

        # We use a suffix to differentiate from full content cache
        theme_id = self.theme_config.get("theme_name", "user_reminder")
        cache_key = f"{theme_id}_SHARED_IMAGE"

        # 2. Try Load from Cache
        cached_data = firestore_service.get_cached_content(cache_key, today_str)
        if cached_data:
            return cached_data.get("image_url"), cached_data.get(
                "image_attribution", ""
            )

        # 3. Fetch from API (Cache Miss)
        image_url = None
        image_attribution = ""

        if image_config := self.theme_config.get("dynamic_image"):
            image_data = image_service.get_dynamic_image(image_config)
            if image_data:
                image_url = image_data.get("image_url")
                image_attribution = image_data.get("attribution_html", "")

        # 4. Save to Cache
        if image_url:
            cache_payload = {
                "image_url": image_url,
                "image_attribution": image_attribution,
                "text": "SHARED_IMAGE_PLACEHOLDER",  # Dummy text required by structure
            }
            firestore_service.save_cached_content(cache_key, today_str, cache_payload)

        return image_url, image_attribution

    def _process(
        self, user: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Orchestrates content generation:
        - Content: From User Data (Unique)
        - Image: From Shared Cache (Common)
        """
        if not user:
            logging.error("User object is required for UserDefinedHandler.")
            return None, None

        # 1. Get Shared Image (Cached)
        image_url, image_attribution = self._get_shared_image()

        # 2. Get User Content
        custom_content = user.get("custom_content", {})

        has_blocks = any(b.strip() for b in custom_content.get("blocks", []))
        has_links = any(l.get("url") for l in custom_content.get("links", []))  # noqa: E741

        if not has_blocks and not has_links:
            logging.warning(
                f"User {user.get('description')} has reminder active but no content."
            )
            return None, None

        # 3. Build Text
        final_text = self._build_html_message(custom_content)

        if image_attribution:
            final_text += f"\n\n<blockquote>{image_attribution}</blockquote>"

        return final_text, image_url


# End of src/handlers/template/user_defined_handler.py (v. 0005)
