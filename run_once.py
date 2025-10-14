# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# run_once.py
"""
The main entry point for single, one-shot executions of the YourDailyPulse bot
and related utility tools.

This script acts as a command-line interface for various purposes:
1.  Running a scheduled job for a specific time key (e.g., 'time1').
2.  Generating photo links from a Cloudinary folder.
3.  Downloading all Google Sheets data as local CSV files.

Usage:
    - To run a scheduled job:
      python run_once.py <time_key> [users <user_desc_1> <user_desc_2> ...]

    - To generate a photo database from a Cloudinary folder:
      python run_once.py generate_photo_db <folder_name> <output_file.csv>

    - To download all Google Sheets as CSVs:
      python run_once.py download_sheets <output_directory>
"""

from dotenv import load_dotenv

# --- CRITICAL: Load .env file BEFORE importing any local modules ---
load_dotenv()

import logging  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
from typing import List, Optional  # noqa: E402

import sentry_sdk  # noqa: E402

from src.config import setup_logging  # noqa: E402
from src.core import generate_and_send  # noqa: E402

# The tools module is imported dynamically when needed to keep job runs clean.


def main() -> None:
    """
    The main entry point for the script. Parses arguments and dispatches
    to the correct function (either a job or a tool).
    """
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    if SENTRY_DSN:
        try:
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                enable_logs=True,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
            print("Sentry SDK initialized.")
        except Exception as e:
            print(f"Failed to initialize Sentry: {e}")
    else:
        print("SENTRY_DSN not found. Sentry is not initialized.")

    setup_logging()
    logging.info(f"SENTRY_DSN found: {SENTRY_DSN is not None}")

    try:
        if len(sys.argv) < 2:
            logging.error(
                "Execution failed: A command is required.\n"
                "Usage for jobs: python run_once.py <time_key> [users ...]\n"
                "Usage for tools: python run_once.py generate_photo_db <folder_name> <output.csv>\n"
                "Usage for export: python run_once.py download_sheets <output_directory>"
            )
            sys.exit(1)

        command = sys.argv[1]

        # --- COMMAND 1: Generate Photo DB ---
        if command == "generate_photo_db":
            if len(sys.argv) != 4:
                logging.error(
                    "Usage: python run_once.py generate_photo_db <folder_name> <output_file.csv>"
                )
                sys.exit(1)

            from src.tools import photo_importer  # noqa: E402

            folder_name = sys.argv[2]
            output_file = sys.argv[3]
            logging.info(f"Starting photo DB generation for folder: {folder_name}")
            photo_importer.run_importer(folder_name, output_file)
            logging.info("Photo DB generation complete.")

        # --- COMMAND 2: Download Sheets ---
        elif command == "download_sheets":
            if len(sys.argv) != 3:
                logging.error(
                    "Usage: python run_once.py download_sheets <output_directory>"
                )
                sys.exit(1)

            from src.tools import sheet_exporter  # noqa: E402

            output_dir = sys.argv[2]
            logging.info(f"Starting download of all sheets to directory: {output_dir}")
            sheet_exporter.run_exporter(output_dir)
            logging.info("Sheet download complete.")

        # --- COMMAND 3: Run Scheduled Job ---
        else:
            time_key: str = command
            user_filter: Optional[List[str]] = None

            if len(sys.argv) > 2:
                if sys.argv[2].lower() == "users":
                    if len(sys.argv) > 3:
                        user_filter = sys.argv[3:]
                    else:
                        logging.error(
                            "The 'users' keyword requires at least one user description."
                        )
                        sys.exit(1)
                else:
                    logging.error(
                        f"Invalid argument '{sys.argv[2]}'. Expected 'users' or nothing."
                    )
                    sys.exit(1)

            with sentry_sdk.start_transaction(op="task", name=f"run_once:{time_key}"):
                if user_filter is not None:
                    logging.info(
                        f"Starting job for '{time_key}' with filter: {user_filter}"
                    )
                else:
                    logging.info(f"Starting job for '{time_key}' for all users.")

                generate_and_send(time_key, user_filter=user_filter)
                logging.info(f"Job for '{time_key}' completed successfully.")

    except Exception as e:
        logging.exception("A critical error occurred during the script run: %s", e)
        sys.exit(1)

    finally:
        if SENTRY_DSN:
            logging.info("Flushing Sentry events before exit...")
            sentry_sdk.flush()


if __name__ == "__main__":
    main()

# End of run_once.py (v. 0016)
