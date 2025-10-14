# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/image_service.py
"""
Service module for fetching dynamic images from various external providers.

This module defines the ImageService class, which acts as a dispatcher to
different image fetching implementations (e.g., Unsplash). It is designed
to be easily extensible with new providers.
"""

import logging
from typing import Any, Dict, cast

import httpx

from .. import config


class ImageService:
    """
    Encapsulates all logic for fetching dynamic images from various providers.

    This class provides a single entry point (`get_dynamic_image`) that dispatches
    the request to the appropriate private method based on the configured provider.
    """

    def _get_random_unsplash_image(self, query: str) -> Dict[str, str] | None:
        """
        Fetches a random image from Unsplash API and triggers the download endpoint.

        This method is compliant with the Unsplash API terms.

        Args:
            query (str): A string of comma-separated keywords for the image search.

        Returns:
            Dict[str, str] | None: A dictionary containing the 'image_url' and
            'attribution_html', or None on failure.
        """
        if not config.UNSPLASH_ACCESS_KEY:
            logging.warning("UNSPLASH_ACCESS_KEY is not set. Skipping Unsplash image.")
            return None

        logging.info(f"Fetching random image from Unsplash for query: '{query}'")
        base_url = "https://api.unsplash.com/photos/random"
        headers = {"Authorization": f"Client-ID {config.UNSPLASH_ACCESS_KEY}"}
        params = {"query": query, "orientation": "landscape"}

        try:
            with httpx.Client(timeout=20.0, headers=headers) as client:
                response = client.get(base_url, params=params)
                response.raise_for_status()
                data = cast(Dict[str, Any], response.json())

                image_url = data.get("urls", {}).get("regular")
                user_name = data.get("user", {}).get("name")
                user_link = data.get("user", {}).get("links", {}).get("html")
                download_trigger_url = data.get("links", {}).get("download_location")

                if not all([image_url, user_name, user_link, download_trigger_url]):
                    logging.error("Unsplash API response is missing required fields.")
                    return None

                client.get(download_trigger_url)
                logging.info(
                    f"Triggered Unsplash download for image ID {data.get('id')}."
                )

                attribution_html = f'<i><a href="{user_link}?utm_source=yourdaily_pulse&utm_medium=referral">Photo by {user_name} on Unsplash</a></i>'

                return {"image_url": image_url, "attribution_html": attribution_html}

        except httpx.HTTPStatusError as e:
            logging.error(
                f"HTTP error from Unsplash: {e.response.status_code} - {e.response.text}"
            )
        except Exception:
            logging.exception("Unexpected error fetching from Unsplash.")

        return None

    def get_dynamic_image(self, image_config: Dict[str, str]) -> Dict[str, str] | None:
        """
        Fetches a dynamic image based on the provider specified in the configuration.

        This method acts as a dispatcher to the appropriate image fetching function.

        Args:
            image_config (Dict[str, str]): The 'dynamic_image' dictionary from a theme's config.

        Returns:
            Dict[str, str] | None: A dictionary with 'image_url' and 'attribution_html', or None.
        """
        provider = image_config.get("provider")
        query = image_config.get("query", "")

        if provider == "unsplash":
            return self._get_random_unsplash_image(query)

        logging.warning(f"Unknown or unsupported image provider: '{provider}'")
        return None


# --- Singleton Instance ---
_image_service_instance = ImageService()


# --- Public-facing Functions ---
def get_dynamic_image(image_config: Dict[str, str]) -> Dict[str, str] | None:
    """
    Public-facing function to fetch a dynamic image.

    This function delegates the call to the singleton instance of ImageService.

    Args:
        image_config (Dict[str, str]): The 'dynamic_image' configuration dictionary.

    Returns:
        Dict[str, str] | None: A dictionary containing 'image_url' and 'attribution_html',
        or None on failure.
    """
    return _image_service_instance.get_dynamic_image(image_config)


# End of src/services/image_service.py (v. 0002)
