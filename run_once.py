# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# run_once.py
"""
The main entry point for single, one-shot executions of the YourDailyPulse bot.

This script is responsible for running a scheduled job for a specific time key
(e.g., 'time1') and an optional user filter.

All other maintenance and utility tasks (e.g., data export, photo import)
must be executed via the dedicated 'tools.py' script.

Usage:
    - To run a scheduled job for all subscribed users:
      python run_once.py <time_key>

    - To run a job for specific users only:
      python run_once.py <time_key> users <user_desc_1> <user_desc_2> ...
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


def main() -> None:
    """
    The main entry point for the script. Parses arguments and runs a job.
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
        # Initialize variables before the match block
        time_key: Optional[str] = None
        user_filter: Optional[List[str]] = None

        # Use structural pattern matching to parse command-line arguments
        match sys.argv:
            # Case 1: No arguments provided (only script name)
            case [_]:
                logging.error(
                    "Execution failed: A time_key is required.\n"
                    "Usage: python run_once.py <time_key> [users ...]\n"
                    "For utility tools, please use 'python tools.py'."
                )
                sys.exit(1)

            # Case 2: Only a time_key is provided
            case [_, tk]:
                time_key = tk
                user_filter = None

            # Case 3: A time_key and 'users' keyword with at least one user
            case [_, tk, "users", *users] if users:
                time_key = tk
                user_filter = users

            # Case 4: A time_key and 'users' keyword but no users listed
            case [_, _, "users"]:
                logging.error(
                    "The 'users' keyword requires at least one user description."
                )
                sys.exit(1)

            # Default case for any other invalid argument structure
            case _:
                logging.error(
                    f"Invalid arguments: {' '.join(sys.argv[1:])}\n"
                    "Did you mean to use 'tools.py'?"
                )
                sys.exit(1)

        # The rest of the logic remains the same
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

# End of run_once.py (v. 0018)
