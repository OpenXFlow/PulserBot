# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# run_once.py
"""
The main entry point for single, one-shot executions of the YourDailyPulse bot.

This script is responsible for running a scheduled job for a specific time key
(e.g., 'time1') and an optional user filter.

Usage:
    - Standard run (uses real time):
      python run_once.py

    - Manual run with filters:
      python run_once.py time6 users <email>

    - Flags:
      force        -> Ignores Content Cache (regenerates text).
      ignore_time  -> Ignores Real Time (forces the time specified in argument).

    Examples:
      python run_once.py time6 users me@test.com force ignore_time
"""

import asyncio

from dotenv import load_dotenv

# --- CRITICAL: Load .env file BEFORE importing any local modules ---
load_dotenv()

import logging  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
from typing import List, Optional  # noqa: E402

import sentry_sdk  # noqa: E402

from src.config import setup_logging  # noqa: E402
from src.core import generate_and_send_async  # noqa: E402


async def main() -> None:
    """
    The main async entry point for the script. Parses arguments and runs a job.
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
        # --- Argument Parsing ---
        args = sys.argv[1:]

        # 1. Parse Flags
        force_update = False
        ignore_time = False

        if "force" in args:
            args.remove("force")
            force_update = True
            logging.warning("⚠️ FORCE MODE: Content Cache will be ignored/overwritten.")
        elif "clean_cache" in args:
            args.remove("clean_cache")
            force_update = True
            logging.warning("⚠️ FORCE MODE: Content Cache will be ignored/overwritten.")

        if "ignore_time" in args:
            args.remove("ignore_time")
            ignore_time = True
            logging.warning(
                "⏰ IGNORE TIME: Forcing execution regardless of user's local time."
            )

        # 2. Parse Users Filter
        user_filter: Optional[List[str]] = None
        if "users" in args:
            idx = args.index("users")
            if idx + 1 < len(args):
                user_filter = args[idx + 1 :]
                # Keep only args before 'users' for time_key detection
                args = args[:idx]
            else:
                logging.error(
                    "The 'users' keyword requires at least one email address."
                )
                sys.exit(1)

        # 3. Parse Time Key
        time_key_label = "auto"
        if args:
            time_key_label = args[0]

        # --- Execution ---
        with sentry_sdk.start_transaction(op="task", name=f"run_once:{time_key_label}"):
            if user_filter:
                logging.info(f"Starting manual run for users: {user_filter}")
            else:
                logging.info(f"Starting global run (Label: {time_key_label}).")

            await generate_and_send_async(
                time_key=time_key_label,
                user_filter=user_filter,
                force_update=force_update,
                ignore_time_checks=ignore_time,
            )

            logging.info("Job execution completed.")

    except Exception as e:
        logging.exception("A critical error occurred during the script run: %s", e)
        try:
            if SENTRY_DSN:
                sentry_sdk.flush(timeout=2.0)
        except Exception:
            pass
        os._exit(1)

    finally:
        if SENTRY_DSN:
            logging.info("Flushing Sentry events before exit...")
            sentry_sdk.flush(timeout=2.0)

        logging.info("Forcing process termination.")
        os._exit(0)


if __name__ == "__main__":
    asyncio.run(main())

# End of run_once.py (v. 0024)
