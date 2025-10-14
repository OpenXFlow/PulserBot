# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/services/sheets_service.py
"""
A service module for all interactions with the Google Sheets API using an OOP approach.

This module defines the SheetsService class, which encapsulates the logic for
connecting to Google Sheets, retrieving data, marking items as used, and
automatically resetting content. It uses a singleton pattern for the client
to ensure a single, persistent connection.
"""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Tuple

import google.auth
import gspread

from ..config import TIMEZONE_STR, ZoneInfo


class SheetsService:
    """
    Encapsulates all interactions with the Google Sheets API.

    This class manages the gspread client instance and provides methods
    to interact with worksheets, ensuring that the client is initialized only
    once (singleton pattern).

    Attributes:
        _client (gspread.Client | None): A private attribute to hold the cached gspread client.
    """

    def __init__(self) -> None:
        """Initializes the SheetsService."""
        self._client: gspread.Client | None = None

    def _get_client(self) -> gspread.Client | None:
        """
        Initializes and returns the gspread client, using a cached instance.

        Returns:
            gspread.Client | None: An authorized client or None on failure.
        """
        if self._client:
            return self._client

        try:
            logging.info(
                "Initializing Google Sheets client (v2 - using google.auth.default)..."
            )
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds, _ = google.auth.default(scopes=scopes)

            self._client = gspread.authorize(creds)
            logging.info("Successfully connected and authorized with Google API.")
            return self._client
        except Exception as e:
            logging.critical(f"Google API Authentication failed: {e}")
            return None

    def get_worksheet(
        self, spreadsheet_url: str, worksheet_name: str
    ) -> gspread.Worksheet | None:
        """
        Opens a specific worksheet within a Google Sheet document.

        Args:
            spreadsheet_url (str): The full URL of the Google Sheet document.
            worksheet_name (str): The name of the worksheet to open.

        Returns:
            gspread.Worksheet | None: A worksheet object or None if it cannot be opened.
        """
        client = self._get_client()
        if not client:
            return None
        try:
            spreadsheet = client.open_by_url(spreadsheet_url)
            return spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"Spreadsheet not found at URL: {spreadsheet_url}")
        except gspread.exceptions.WorksheetNotFound:
            logging.error(f"Worksheet '{worksheet_name}' not found.")
        except Exception as e:
            logging.error(f"Error opening worksheet '{worksheet_name}': {e}")
        return None

    def get_unused_item(
        self, worksheet: gspread.Worksheet, language: str | None
    ) -> Tuple[int | None, Dict[str, Any] | None]:
        """
        Retrieves a random, unused row from the worksheet.

        Args:
            worksheet (gspread.Worksheet): The worksheet object to search in.
            language (str | None): The language to filter by, or None to ignore.

        Returns:
            Tuple[int | None, Dict[str, Any] | None]: A tuple with the row index
            and row data, or (None, None) on failure.
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
                logging.warning("No unused content found. Triggering auto-reset.")
                if self._reset_used_flags(worksheet, language):
                    all_values = worksheet.get_all_values()
                    all_records = [dict(zip(header, row)) for row in all_values[1:]]
                    unused_items = self._filter_unused_items(all_records, language)
                else:
                    logging.error("Auto-reset failed.")
                    return None, None

            if not unused_items:
                logging.error("Still no unused content after reset attempt.")
                return None, None

            return random.choice(unused_items)
        except Exception as e:
            logging.error(f"Error getting an unused item: {e}")
            return None, None

    def mark_item_as_used(self, worksheet: gspread.Worksheet, row_index: int) -> None:
        """
        Marks an item as used by dynamically finding the correct columns.

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
            logging.info(f"Successfully marked row {row_index} as used.")
        except ValueError as e:
            logging.warning(
                f"Could not find required columns in sheet '{worksheet.title}': {e}"
            )
        except Exception as e:
            logging.warning(f"Could not mark row {row_index} as used: {e}")

    def _filter_unused_items(
        self, records: List[Dict[str, Any]], language: str | None
    ) -> List[Tuple[int, Dict[str, Any]]]:
        """
        A helper method to filter a list of records for unused items.

        Args:
            records (List[Dict[str, Any]]): A list of dictionaries representing sheet rows.
            language (str | None): The language to filter by, or None.

        Returns:
            List[Tuple[int, Dict[str, Any]]]: A list of tuples, each containing the
            row index and the row data for an unused item.
        """
        filtered = []
        for i, row in enumerate(records):
            is_unused = str(row.get("used", "")).upper() == "FALSE"
            if language is not None:
                lang_match = str(row.get("language", "")).lower() == language
                if is_unused and lang_match:
                    filtered.append((i + 2, row))
            else:
                if is_unused:
                    filtered.append((i + 2, row))
        return filtered

    def _reset_used_flags(
        self, worksheet: gspread.Worksheet, language: str | None
    ) -> bool:
        """A helper method to reset 'used' flags."""
        log_lang = f"language '{language}'" if language is not None else "all rows"
        logging.warning(
            f"Resetting 'used' flags for {log_lang} in '{worksheet.title}'..."
        )
        try:
            all_values = worksheet.get_all_values()
            if len(all_values) < 2:
                return False
            header = all_values[0]
            records = [dict(zip(header, row)) for row in all_values[1:]]

            used_col_index = header.index("used") + 1

            updates = []
            for i, row in enumerate(records):
                if language is not None:
                    if str(row.get("language", "")).lower() == language:
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
            logging.info("No rows found to reset.")
            return False
        except ValueError:
            logging.error(f"Header 'used' not found in '{worksheet.title}'.")
            return False
        except Exception as e:
            logging.error(f"Failed to reset 'used' flags: {e}")
            return False


_sheets_service_instance = SheetsService()


def get_worksheet(
    spreadsheet_url: str, worksheet_name: str
) -> gspread.Worksheet | None:
    """
    Public-facing function to open a specific worksheet.

    This function delegates the call to the singleton instance of SheetsService,
    providing a simple, procedural interface for other modules.

    Args:
        spreadsheet_url (str): The full URL of the Google Sheet document.
        worksheet_name (str): The name of the worksheet to open.

    Returns:
        gspread.Worksheet | None: A gspread.Worksheet object, or None if it cannot be opened.
    """
    return _sheets_service_instance.get_worksheet(spreadsheet_url, worksheet_name)


def get_unused_item(
    worksheet: gspread.Worksheet, language: str | None
) -> Tuple[int | None, Dict[str, Any] | None]:
    """
    Public-facing function to retrieve a random, unused row from a worksheet.

    This function delegates the call to the singleton instance of SheetsService.

    Args:
        worksheet (gspread.Worksheet): The worksheet object to search in.
        language (str | None): The language of the content to find, or None to ignore language.

    Returns:
        Tuple[int | None, Dict[str, Any] | None]: A tuple containing the 1-based row index
        and a dictionary of the row data, or (None, None) if no content is found.
    """
    return _sheets_service_instance.get_unused_item(worksheet, language)


def mark_item_as_used(worksheet: gspread.Worksheet, row_index: int) -> None:
    """
    Public-facing function to mark an item in a worksheet as used.

    This function delegates the call to the singleton instance of SheetsService.

    Args:
        worksheet (gspread.Worksheet): The worksheet object to update.
        row_index (int): The absolute, 1-based row index of the item to mark.
    """
    _sheets_service_instance.mark_item_as_used(worksheet, row_index)


# End of src/services/sheets_service.py (v. 0010)
