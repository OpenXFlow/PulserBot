# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/tools/sheet_exporter.py
"""
A utility tool to download all Google Sheets specified in the config.json
file and save them as local CSV files, preserving the logical structure
within a timestamped backup directory.
"""

import csv
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List

from src.services import sheets_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class SheetExporter:
    """
    Encapsulates logic for exporting Google Sheets data to a structured, timestamped directory.

    Attributes:
        output_dir (str): The root path where the timestamped directory will be created.
        app_config (Dict[str, Any]): The loaded application configuration.
    """

    def __init__(self, output_dir: str):
        """
        Initializes the SheetExporter.

        Args:
            output_dir (str): The root path where the timestamped backup directory
                will be created.
        """
        self.output_dir = output_dir
        self.app_config: Dict[str, Any] = {}

    def _prepare_output_directory(self, full_path: str) -> bool:
        """
        Ensures the specified full directory path exists.

        Args:
            full_path (str): The absolute path of the directory to create.

        Returns:
            bool: True if the directory exists or was created, False otherwise.
        """
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
                logging.info(f"Created output directory: {full_path}")
            except OSError:
                logging.exception(f"Failed to create directory '{full_path}'")
                return False
        return True

    def _collect_structured_sheets(self) -> Dict[str, Dict[str, Any]]:
        """
        Reads the config and collects all sheets, structured by their data source key.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary mapping data source names to their
            URL and list of worksheets.
        """
        sheets_to_download: Dict[str, Dict[str, Any]] = {}
        data_sources = self.app_config.get("data_sources", {})

        for source_key, source_config in data_sources.items():
            if not isinstance(source_config, dict):
                continue
            url = source_config.get("spreadsheet_url")
            worksheets = source_config.get("worksheets", {})
            if not url or not worksheets:
                continue

            worksheet_names: List[str] = []
            for ws_info in worksheets.values():
                name = ws_info.get("name") if isinstance(ws_info, dict) else ws_info
                if isinstance(name, str) and name:
                    worksheet_names.append(name)

            if worksheet_names:
                sheets_to_download[source_key] = {"url": url, "sheets": worksheet_names}

        logging.info(
            f"Found {len(sheets_to_download)} structured data sources to download."
        )
        return sheets_to_download

    def _download_and_save_sheet(
        self, spreadsheet_url: str, worksheet_name: str, target_dir: str
    ) -> bool:
        """
        Downloads a single worksheet and saves it as a CSV file.

        Args:
            spreadsheet_url (str): The URL of the Google Sheet document.
            worksheet_name (str): The name of the worksheet to download.
            target_dir (str): The directory where the CSV file will be saved.

        Returns:
            bool: True on success, False on failure.
        """
        logging.info(f"  -> Downloading '{worksheet_name}'...")
        try:
            gspread_client = sheets_service._sheets_service_instance._get_client()
            if not gspread_client:
                logging.error("Could not get gspread client.")
                return False

            spreadsheet = gspread_client.open_by_url(spreadsheet_url)
            worksheet = spreadsheet.worksheet(worksheet_name)

            all_values = worksheet.get_all_values()
            csv_filename = os.path.join(target_dir, f"{worksheet_name}.csv")
            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(all_values)
            logging.info(f"     Successfully saved to '{csv_filename}'")
            return True
        except Exception:
            logging.exception(f"     Failed to download or save '{worksheet_name}'")
            return False

    def execute(self) -> None:
        """
        Orchestrates the entire structured and timestamped export process.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root_dir = os.path.join(self.output_dir, f"backup_{timestamp}")

        if not self._prepare_output_directory(backup_root_dir):
            return

        try:
            with open("config.json", "r", encoding="utf-8") as f:
                self.app_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Could not load or parse config.json: {e}")
            return

        sheets_service.initialize_sheets_service(self.app_config)

        structured_sheets = self._collect_structured_sheets()
        if not structured_sheets:
            logging.warning("No data sources found in config.json to download.")
            return

        total_sheets = sum(len(data["sheets"]) for data in structured_sheets.values())
        success_count = 0

        for source_key, data in structured_sheets.items():
            logging.info(f"\nProcessing data source: '{source_key}'")
            target_dir = os.path.join(backup_root_dir, source_key)
            if not self._prepare_output_directory(target_dir):
                continue

            url = data["url"]
            for sheet_name in data["sheets"]:
                if self._download_and_save_sheet(url, sheet_name, target_dir):
                    success_count += 1
                time.sleep(1.5)

        logging.info("-" * 40)
        logging.info(
            f"Export complete. Successfully downloaded {success_count}/{total_sheets} sheets."
        )
        logging.info(f"Backup saved to: {backup_root_dir}")


def run_exporter(output_dir: str) -> None:
    """
    Public-facing function that acts as the entry point for this tool.

    Args:
        output_dir (str): The root directory where the new timestamped backup
            folder will be created.
    """
    exporter = SheetExporter(output_dir)
    exporter.execute()


# End of src/tools/sheet_exporter.py (v. 0011)
