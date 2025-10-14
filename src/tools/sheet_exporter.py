# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# src/tools/sheet_exporter.py
"""
A utility tool to download all Google Sheets specified in the config.json
file and save them as local CSV files, using an OOP approach.
"""

import csv
import json
import logging
import os
from typing import Any, Dict, List, Set, Tuple

# This script is run via tools.py which appends 'src' to the path
from src.services import sheets_service

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class SheetExporter:
    """
    Encapsulates all logic for exporting Google Sheets data to local CSV files.

    This class reads the application configuration, identifies all unique
    Google Sheets used in the project, connects to the Google API, and
    downloads the content of each sheet into a specified directory.

    Attributes:
        output_dir (str): The directory where the CSV files will be saved.
    """

    def __init__(self, output_dir: str):
        """
        Initializes the SheetExporter.

        Args:
            output_dir (str): The path to the directory where CSV files will be saved.
        """
        self.output_dir = output_dir

    def _prepare_output_directory(self) -> bool:
        """
        Ensures the output directory exists.

        Returns:
            bool: True if the directory exists or was created successfully, False otherwise.
        """
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
                logging.info(f"Created output directory: {self.output_dir}")
            except OSError as e:
                logging.error(
                    f"Failed to create output directory '{self.output_dir}': {e}"
                )
                return False
        return True

    def _collect_unique_sheets(self) -> Set[Tuple[str, str]]:
        """
        Reads the config.json and collects all unique spreadsheet URL and worksheet name pairs.

        Returns:
            Set[Tuple[str, str]]: A set of tuples, where each tuple is
            (spreadsheet_url, worksheet_name). Returns an empty set on failure.
        """
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                app_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Could not load or parse config.json: {e}")
            return set()

        sheets_to_download: Set[Tuple[str, str]] = set()

        sources_to_check: List[Dict[str, Any]] = [
            app_config.get("themes", {}),
            app_config.get("data_sources", {}),
            {"logging": app_config.get("logging_spreadsheet", {})},
        ]

        for source_dict in sources_to_check:
            for item_config in source_dict.values():
                if isinstance(item_config, dict):
                    url = item_config.get("spreadsheet_url")
                    name = item_config.get("worksheet_name") or item_config.get(
                        "jobs_worksheet_name"
                    )
                    if url and name:
                        sheets_to_download.add((url, name))

        logging.info(f"Found {len(sheets_to_download)} unique sheets to download.")
        return sheets_to_download

    def _download_and_save_sheet(self, url: str, name: str) -> bool:
        """
        Downloads a single worksheet and saves it as a CSV file.

        Args:
            url (str): The URL of the Google Sheet document.
            name (str): The name of the worksheet to download.

        Returns:
            bool: True on success, False on failure.
        """
        logging.info(f"Downloading '{name}'...")
        try:
            worksheet = sheets_service.get_worksheet(url, name)
            if not worksheet:
                logging.warning(f"Skipping '{name}' as it could not be accessed.")
                return False

            all_values = worksheet.get_all_values()

            csv_filename = os.path.join(self.output_dir, f"{name}.csv")
            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(all_values)

            logging.info(f" -> Successfully saved to '{csv_filename}'")
            return True

        except Exception as e:
            logging.error(f" -> Failed to download or save '{name}': {e}")
            return False

    def execute(self) -> None:
        """
        Orchestrates the entire export process.

        This is the main public method that runs the entire workflow.
        """
        if not self._prepare_output_directory():
            return

        unique_sheets = self._collect_unique_sheets()
        if not unique_sheets:
            logging.warning("No sheets found in config.json to download.")
            return

        success_count = 0
        for url, name in unique_sheets:
            if self._download_and_save_sheet(url, name):
                success_count += 1

        logging.info("-" * 30)
        logging.info(
            f"Export complete. Successfully downloaded {success_count}/{len(unique_sheets)} sheets."
        )


def run_exporter(output_dir: str) -> None:
    """
    Public-facing function that acts as the entry point for this tool.

    Args:
        output_dir (str): The directory where the CSV files will be saved.
    """
    exporter = SheetExporter(output_dir)
    exporter.execute()


# End of src/tools/sheet_exporter.py (v. 0003)
