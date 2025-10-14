# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# tools.py
"""
A collection of command-line utility tools for project maintenance.

This script is intended for manual use by the developer and provides tools for:
1. Generating photo links from a Cloudinary folder.
2. Downloading all Google Sheets data as local CSV files.
3. Fetching artwork data from The MET API.

Usage:
    - To generate a photo database from a Cloudinary folder:
      python tools.py generate_photo_db <folder_name> <output_file.csv>

    - To download all Google Sheets as CSVs:
      python tools.py download_sheets <output_directory>

    - To fetch artwork data from The MET API:
      python tools.py fetch_art_data <dept_id> <data_output.csv> <id_cache.csv> [max_items]
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
from src.tools import met_artwork_importer, photo_importer, sheet_exporter  # noqa: E402


class ToolDispatcher:
    """
    Parses command-line arguments and dispatches tasks to specific tool modules.

    This class provides a structured way to manage and extend the available
    developer tools. Each tool is implemented as a separate method.
    """

    def __init__(self, args: List[str]):
        """
        Initializes the dispatcher with command-line arguments.

        Args:
            args (List[str]): A list of command-line arguments, typically sys.argv.
        """
        self.args = args

    def _show_usage(self) -> None:
        """Prints the main usage information for all available tools."""
        print("Usage:")
        print("  python tools.py generate_photo_db <folder_name> <output.csv>")
        print("  python tools.py download_sheets <output_directory>")
        print(
            "  python tools.py fetch_art_data <dept_id> <data.csv> <id_cache.csv> [max_items]"
        )

    def _handle_generate_photo_db(self) -> None:
        """Handles the 'generate_photo_db' command."""
        if len(self.args) != 4:
            logging.error(
                "Usage: python tools.py generate_photo_db <folder_name> <output_file.csv>"
            )
            sys.exit(1)
        folder_name, output_file = self.args[2], self.args[3]
        logging.info(f"Starting photo DB generation for folder: {folder_name}")
        photo_importer.run_importer(folder_name, output_file)
        logging.info("Photo DB generation complete.")

    def _handle_download_sheets(self) -> None:
        """Handles the 'download_sheets' command."""
        if len(self.args) != 3:
            logging.error("Usage: python tools.py download_sheets <output_directory>")
            sys.exit(1)
        output_dir = self.args[2]
        logging.info(f"Starting download of all sheets to directory: {output_dir}")
        sheet_exporter.run_exporter(output_dir)
        logging.info("Sheet download complete.")

    def _handle_fetch_art_data(self) -> None:
        """Handles the 'fetch_art_data' command."""
        if not (5 <= len(self.args) <= 6):
            logging.error(
                "Usage: python tools.py fetch_art_data <dept_id> <data.csv> <id_cache.csv> [max_items]"
            )
            sys.exit(1)

        department_id = int(self.args[2])
        output_file = self.args[3]
        id_cache_file = self.args[4]
        max_items = int(self.args[5]) if len(self.args) == 6 else 50

        logging.info(f"Starting artwork data fetch for department: {department_id}")
        met_artwork_importer.run_importer(
            department_id, output_file, id_cache_file, max_items
        )
        logging.info("Artwork data fetch complete.")

    def execute(self) -> None:
        """
        Parses the command and executes the corresponding handler method.
        This is the main entry point for the dispatcher's logic.
        """
        if len(self.args) < 2:
            self._show_usage()
            sys.exit(1)

        command = self.args[1]

        if command == "generate_photo_db":
            self._handle_generate_photo_db()
        elif command == "download_sheets":
            self._handle_download_sheets()
        elif command == "fetch_art_data":
            self._handle_fetch_art_data()
        else:
            logging.error(f"Unknown command: '{command}'")
            self._show_usage()
            sys.exit(1)


def main() -> None:
    """
    Main function that sets up logging and runs the ToolDispatcher.
    """
    setup_logging()
    dispatcher = ToolDispatcher(sys.argv)
    dispatcher.execute()


if __name__ == "__main__":
    main()

# End of tools.py (v. 0009)
