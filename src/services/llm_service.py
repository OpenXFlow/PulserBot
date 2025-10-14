# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/llm_service.py
"""
A service module for all interactions with LLM APIs using an OOP approach.

This module defines the LLMService class, which encapsulates the logic for
communicating with language models (currently Groq). It handles client
initialization, making API calls, and robust error handling.
"""

import logging

import httpx
from groq import Groq, GroqError

from .. import config


class LLMService:
    """
    Encapsulates all logic for interacting with a Language Model API.

    This class manages the API client and provides a consistent method for
    sending prompts and receiving text responses.

    Attributes:
        _client (Groq | None): A private attribute to hold the cached Groq client instance.
    """

    def __init__(self) -> None:
        """Initializes the LLMService."""
        self._client: Groq | None = None

    def _get_client(self) -> Groq | None:
        """
        Initializes and returns an authorized Groq client, using a cached instance.

        This method configures the client with the API key and model from the
        global configuration. It is called internally to ensure the client is
        created only once.

        Returns:
            Groq | None: An authorized Groq client instance, or None if the API
            key is not configured.
        """
        if self._client:
            return self._client

        if not config.GROQ_API_KEY:
            logging.critical(
                "GROQ_API_KEY is not set. LLM service cannot be initialized."
            )
            return None

        # Using a custom transport can help bypass SSL verification issues in some environments.
        transport = httpx.HTTPTransport(verify=False)
        self._client = Groq(
            api_key=config.GROQ_API_KEY, http_client=httpx.Client(transport=transport)
        )
        logging.info("Groq client initialized successfully.")
        return self._client

    def generate_text(self, prompt: str) -> str:
        """
        Sends a prompt to the configured LLM and returns the text response.

        Args:
            prompt (str): The complete, final prompt to be sent to the language model.

        Returns:
            str: The text content of the LLM's response as a string. Returns an
            empty string if the API call fails, returns no content, or if the
            prompt is empty.
        """
        if not prompt:
            logging.warning(
                "generate_text received an empty prompt. Returning empty string."
            )
            return ""

        client = self._get_client()
        if not client:
            return ""

        logging.info(f"Sending request to Groq API with model '{config.GROQ_MODEL}'...")
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=config.GROQ_MODEL,
                temperature=0.7,
                max_tokens=2048,  # Increased token limit for longer study texts
            )

            response_content = chat_completion.choices[0].message.content
            if response_content:
                logging.info("Successfully received a valid response from Groq API.")
                return response_content.strip()
            else:
                logging.warning("Groq API returned an empty response.")
                return ""
        except GroqError as e:
            logging.error(f"A Groq API error occurred: {e}")
        except httpx.RequestError as e:
            logging.error(f"An HTTP network error occurred while calling Groq API: {e}")
        except Exception as e:
            logging.exception("An unexpected error occurred in generate_text: %s", e)

        return ""


# --- Singleton Instance ---
# It is instantiated when the module is imported,
# and this happens only once during the lifecycle of the entire application.
_llm_service_instance = LLMService()


# --- Public-facing Functions ---
def call_llm(prompt: str) -> str:
    """
    Public-facing function to send a prompt to the LLM.

    This function delegates the call to the singleton instance of LLMService,
    providing a simple, procedural interface for other modules.

    Args:
        prompt (str): The complete prompt to be sent to the language model.

    Returns:
        str: The text content of the LLM's response, or an empty string on failure.
    """
    return _llm_service_instance.generate_text(prompt)


# End of src/services/llm_service.py (v. 0003)
