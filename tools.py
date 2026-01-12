# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# tools.py
"""
The single, authoritative entry point for all project maintenance utilities.

Usage:
    - Generate photo DB:
      python tools.py generate_photo_db <folder_name> <output_file.csv>

    - Backup Google Sheets (CSV):
      python tools.py download_sheets <output_directory>

    - Import Art from MET:
      python tools.py fetch_art_data <dept_id> <data.csv> <id_cache.csv> [max_items]

    - Backup Firestore Users (JSON):
      python tools.py backup_firestore

    - Restore Firestore Users:
      python tools.py restore_firestore <path_to_backup_file.json>
"""

import logging
import sys
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file BEFORE any other local imports
load_dotenv()

# Add 'src' to path to be able to import our modules
sys.path.append("src")

# Now it's safe to import our own modules
from src.config import setup_logging  # noqa: E402
from src.tools import met_artwork_importer, photo_importer, sheet_exporter, firestore_manager  # noqa: E402


class ToolDispatcher:
    """
    Parses command-line arguments and dispatches tasks to specific tool modules.
    """

    def __init__(self, args: List[str]):
        self.args = args

    def _show_usage(self) -> None:
        """Prints the main usage information for all available tools."""
        print("Usage:")
        print("  python tools.py generate_photo_db <folder_name> <output.csv>")
        print("  python tools.py download_sheets <output_directory>")
        print("  python tools.py fetch_art_data <dept_id> <data.csv> <id_cache.csv> [max_items]")
        print("  python tools.py backup_firestore")
        print("  python tools.py restore_firestore <backup_file.json>")

    def _handle_generate_photo_db(self) -> None:
        if len(self.args) != 4:
            logging.error("Usage: python tools.py generate_photo_db <folder_name> <output_file.csv>")
            sys.exit(1)
        folder_name, output_file = self.args[2], self.args[3]
        logging.info(f"Starting photo DB generation for folder: {folder_name}")
        photo_importer.run_importer(folder_name, output_file)

    def _handle_download_sheets(self) -> None:
        if len(self.args) != 3:
            logging.error("Usage: python tools.py download_sheets <output_directory>")
            sys.exit(1)
        output_dir = self.args[2]
        logging.info(f"Starting download of all sheets to directory: {output_dir}")
        sheet_exporter.run_exporter(output_dir)

    def _handle_fetch_art_data(self) -> None:
        if not (5 <= len(self.args) <= 6):
            logging.error("Usage: python tools.py fetch_art_data <dept_id> <data.csv> <id_cache.csv> [max_items]")
            sys.exit(1)
        department_id = int(self.args[2])
        output_file = self.args[3]
        id_cache_file = self.args[4]
        max_items = int(self.args[5]) if len(self.args) == 6 else 50
        logging.info(f"Starting artwork data fetch for department: {department_id}")
        met_artwork_importer.run_importer(department_id, output_file, id_cache_file, max_items)

    def _handle_backup_firestore(self) -> None:
        logging.info("Starting Firestore backup...")
        firestore_manager.run_backup()

    def _handle_restore_firestore(self) -> None:
        if len(self.args) != 3:
            logging.error("Usage: python tools.py restore_firestore <path_to_backup_file.json>")
            sys.exit(1)
        backup_file = self.args[2]
        logging.info(f"Starting Firestore restore from: {backup_file}")
        firestore_manager.run_restore(backup_file)

    def execute(self) -> None:
        """Parses the command and executes the corresponding handler."""
        if len(self.args) < 2:
            self._show_usage()
            sys.exit(1)

        command = self.args[1]

        match command:
            case "generate_photo_db":
                self._handle_generate_photo_db()
            case "download_sheets":
                self._handle_download_sheets()
            case "fetch_art_data":
                self._handle_fetch_art_data()
            case "backup_firestore":
                self._handle_backup_firestore()
            case "restore_firestore":
                self._handle_restore_firestore()
            case _:
                logging.error(f"Unknown command: '{command}'")
                self._show_usage()
                sys.exit(1)


def main() -> None:
    setup_logging()
    dispatcher = ToolDispatcher(sys.argv)
    dispatcher.execute()


if __name__ == "__main__":
    main()

# End of tools.py (v. 0013)