# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/sheets_service.py
"""
A service module for all interactions with the Google Sheets API.
"""

import logging
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gspread

from ..config import TIMEZONE_STR, ZoneInfo


class SheetsService:
    """
    Encapsulates all interactions with the Google Sheets API.

    This class manages the gspread client instance and provides methods
    to interact with worksheets, ensuring that the client is initialized only
    once (singleton pattern).

    Attributes:
        _client (gspread.Client | None): A private attribute to hold the cached client.
        app_config (Dict[str, Any]): The loaded application configuration.
    """

    def __init__(self) -> None:
        """Initializes the SheetsService."""
        self._client: gspread.Client | None = None
        self.app_config: Dict[str, Any] = {}

    def set_app_config(self, app_config: Dict[str, Any]) -> None:
        """
        Sets the application configuration for the service instance.

        Args:
            app_config (Dict[str, Any]): The loaded application configuration.
        """
        self.app_config = app_config

    def _get_client(self) -> gspread.Client | None:
        """
        Initializes and returns the gspread client using a cached instance.

        This method robustly handles authentication by first checking for the
        `GOOGLE_APPLICATION_CREDENTIALS` environment variable (used in cloud/CI environments)
        and falling back to a local `credentials.json` file for development.

        Returns:
            gspread.Client | None: An authorized client, or None on failure.
        """
        if self._client:
            return self._client
        try:
            logging.info("Initializing Google Sheets client...")
            credentials_path = os.environ.get(
                "GOOGLE_APPLICATION_CREDENTIALS", "credentials.json"
            )

            if not os.path.exists(credentials_path):
                logging.critical(
                    f"CRITICAL: Credentials file not found at '{credentials_path}'."
                )
                return None

            self._client = gspread.service_account(filename=credentials_path)
            logging.info(
                f"Successfully authorized with Google API using '{credentials_path}'."
            )
            return self._client
        except Exception as e:
            logging.critical(f"Google API Authentication failed: {e}", exc_info=True)
            return None

    def _resolve_data_source(
        self, data_source_ref: Dict[str, str]
    ) -> Optional[Tuple[str, str]]:
        """
        Translates a data source reference from config into a URL and worksheet name.

        Args:
            data_source_ref (Dict[str, str]): A dictionary from a theme's config.

        Returns:
            Optional[Tuple[str, str]]: A tuple (spreadsheet_url, worksheet_name), or None if invalid.
        """
        if not self.app_config:
            logging.error("Cannot resolve data source: app_config is not set.")
            return None
        try:
            spreadsheet_key = data_source_ref["spreadsheet_key"]
            worksheet_key = data_source_ref["worksheet_key"]
            spreadsheet_config = self.app_config["data_sources"][spreadsheet_key]
            spreadsheet_url = spreadsheet_config["spreadsheet_url"]
            worksheet_info = spreadsheet_config["worksheets"][worksheet_key]
            worksheet_name = (
                worksheet_info.get("name")
                if isinstance(worksheet_info, dict)
                else worksheet_info
            )
            if not worksheet_name:
                raise KeyError(f"Worksheet name for key '{worksheet_key}' is empty.")
            return spreadsheet_url, worksheet_name
        except KeyError as e:
            logging.error(f"Invalid data source reference: Missing key {e}")
            return None
        except TypeError:
            logging.error(f"Malformed data_source_ref: {data_source_ref}")
            return None

    def get_worksheet_by_ref(
        self, data_source_ref: Dict[str, str]
    ) -> gspread.Worksheet | None:
        """
        Opens a specific worksheet using a hierarchical data source reference.

        Args:
            data_source_ref (Dict[str, str]): A dictionary from a theme's config.

        Returns:
            gspread.Worksheet | None: A worksheet object, or None if it cannot be opened.
        """
        resolved_source = self._resolve_data_source(data_source_ref)
        if not resolved_source:
            return None
        spreadsheet_url, worksheet_name = resolved_source
        client = self._get_client()
        if not client:
            return None
        try:
            spreadsheet = client.open_by_url(spreadsheet_url)
            return spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.GSpreadException as e:
            logging.error(f"Error opening worksheet '{worksheet_name}': {e}")
            return None
        except Exception as e:
            logging.error(
                f"An unexpected error occurred opening worksheet '{worksheet_name}': {e}"
            )
            return None

    def get_unused_item(
        self, worksheet: gspread.Worksheet, language: str | None
    ) -> Tuple[int | None, Dict[str, Any] | None]:
        """
        Retrieves a random, unused row from the worksheet, with auto-reset.

        Args:
            worksheet (gspread.Worksheet): The worksheet object to search in.
            language (str | None): The language to filter by.

        Returns:
            Tuple[int | None, Dict[str, Any] | None]: A tuple (row index, row data), or (None, None).
        """
        try:
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                logging.warning(f"Worksheet '{worksheet.title}' is empty.")
                return None, None
            header = all_values[0]
            all_records = [dict(zip(header, row)) for row in all_values[1:]]
            unused_items = self._filter_unused_items(all_records, language)
            if not unused_items:
                logging.warning(
                    f"No unused content found in '{worksheet.title}'. Triggering auto-reset."
                )
                if self._reset_used_flags(worksheet, language):
                    all_values = worksheet.get_all_values()
                    all_records = [dict(zip(header, row)) for row in all_values[1:]]
                    unused_items = self._filter_unused_items(all_records, language)
                else:
                    logging.error(f"Auto-reset failed for '{worksheet.title}'.")
                    return None, None
            if not unused_items:
                logging.error(
                    f"Still no unused content in '{worksheet.title}' after reset attempt."
                )
                return None, None
            return random.choice(unused_items)
        except Exception:
            logging.exception(f"Error getting an unused item from '{worksheet.title}'.")
            return None, None

    def mark_item_as_used(self, worksheet: gspread.Worksheet, row_index: int) -> None:
        """
        Marks a specific row in a worksheet as used.

        Args:
            worksheet (gspread.Worksheet): The worksheet object to update.
            row_index (int): The 1-based row index of the item to mark.
        """
        try:
            now_str = datetime.now(ZoneInfo(TIMEZONE_STR)).strftime("%Y-%m-%d %H:%M:%S")
            header = worksheet.row_values(1)
            used_col = header.index("used") + 1
            date_used_col = header.index("date_used") + 1
            updates = [
                gspread.Cell(row=row_index, col=used_col, value="TRUE"),
                gspread.Cell(row=row_index, col=date_used_col, value=now_str),
            ]
            worksheet.update_cells(updates, value_input_option="USER_ENTERED")
            logging.info(
                f"Successfully marked row {row_index} as used in '{worksheet.title}'."
            )
        except (ValueError, IndexError):
            logging.warning(
                f"Could not find 'used'/'date_used' columns in '{worksheet.title}'."
            )
        except Exception as e:
            logging.warning(f"Could not mark row {row_index} as used: {e}")

    def _filter_unused_items(
        self, records: List[Dict[str, Any]], language: str | None
    ) -> List[Tuple[int, Dict[str, Any]]]:
        """
        Helper to filter a list of records for unused items.

        Args:
            records (List[Dict[str, Any]]): A list of dictionaries representing sheet rows.
            language (str | None): The language to filter by.

        Returns:
            List[Tuple[int, Dict[str, Any]]]: A list of tuples, each containing the
            row index and the row data for an unused item.
        """
        filtered = []
        for i, row in enumerate(records):
            is_unused = str(row.get("used", "")).upper() == "FALSE"
            if language:
                if is_unused and str(row.get("language", "")).lower() == language:
                    filtered.append((i + 2, row))
            elif is_unused:
                filtered.append((i + 2, row))
        return filtered

    def _reset_used_flags(
        self, worksheet: gspread.Worksheet, language: str | None
    ) -> bool:
        """
        Helper to reset 'used' flags to 'FALSE'.

        Args:
            worksheet (gspread.Worksheet): The worksheet where flags will be reset.
            language (str | None): The language for which to reset flags.

        Returns:
            bool: True if the reset was successful, False otherwise.
        """
        log_lang = f"for language '{language}'" if language else "for all rows"
        logging.warning(f"Resetting 'used' flags {log_lang} in '{worksheet.title}'...")
        try:
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                return False
            header = all_values[0]
            used_col_index = header.index("used") + 1
            updates = []
            for i, row_values in enumerate(all_values[1:]):
                if not any(row_values):
                    continue

                row_dict = dict(zip(header, row_values))
                if language:
                    if str(row_dict.get("language", "")).lower() == language:
                        updates.append(
                            gspread.Cell(row=i + 2, col=used_col_index, value="FALSE")
                        )
                else:
                    updates.append(
                        gspread.Cell(row=i + 2, col=used_col_index, value="FALSE")
                    )
            if updates:
                worksheet.update_cells(updates, value_input_option="USER_ENTERED")
                logging.info(f"Successfully reset {len(updates)} rows.")
                return True
            logging.warning("No rows found to reset.")
            return False
        except ValueError:
            logging.error(
                f"Header 'used' not found in '{worksheet.title}'. Cannot reset."
            )
            return False
        except Exception:
            logging.exception(f"Failed to reset 'used' flags in '{worksheet.title}'.")
            return False


_sheets_service_instance = SheetsService()


def initialize_sheets_service(app_config: Dict[str, Any]) -> None:
    """
    Public-facing function to initialize the service with the global app config.

    Args:
        app_config (Dict[str, Any]): The complete, loaded application configuration.
    """
    _sheets_service_instance.set_app_config(app_config)


def get_worksheet(data_source_ref: Dict[str, str]) -> gspread.Worksheet | None:
    """
    Public-facing function to open a worksheet using a data source reference.

    Args:
        data_source_ref (Dict[str, str]): A reference dictionary from a theme's config.

    Returns:
        gspread.Worksheet | None: A worksheet object, or None on failure.
    """
    return _sheets_service_instance.get_worksheet_by_ref(data_source_ref)


def get_unused_item(
    worksheet: gspread.Worksheet, language: str | None
) -> Tuple[int | None, Dict[str, Any] | None]:
    """
    Public-facing function to retrieve a random, unused row from a worksheet.

    Args:
        worksheet (gspread.Worksheet): The worksheet object to search in.
        language (str | None): The language of the content to find.

    Returns:
        Tuple[int | None, Dict[str, Any] | None]: A tuple (row index, row data), or (None, None).
    """
    return _sheets_service_instance.get_unused_item(worksheet, language)


def mark_item_as_used(worksheet: gspread.Worksheet, row_index: int) -> None:
    """
    Public-facing function to mark an item in a worksheet as used.

    Args:
        worksheet (gspread.Worksheet): The worksheet object to update.
        row_index (int): The 1-based row index of the item to mark.
    """
    _sheets_service_instance.mark_item_as_used(worksheet, row_index)


# End of src/services/sheets_service.py (v. 0046)
