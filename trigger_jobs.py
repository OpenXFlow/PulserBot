# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# trigger_jobs.py
"""
A dispatcher script designed to be run periodically by GitHub Actions.

It checks the current time against the schedules defined in config.json,
respecting the specified timezone, and triggers the appropriate jobs via
run_once.py. It uses a Google Sheet as a distributed lock.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

sys.path.append("src")

from src.config import setup_logging
from src.services import sheets_service

# --- Configuration ---
TIME_WINDOW_MINUTES = 29

setup_logging()


def get_scheduled_jobs() -> dict[str, str]:
    """Loads the schedule from config.json."""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            app_config = json.load(f)

        schedule = app_config.get("schedule")
        if isinstance(schedule, dict):
            return schedule
        else:
            logging.error(
                "'schedule' key not found or is not a dictionary in config.json."
            )
            return {}

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.critical(f"Failed to load or parse config.json: {e}")
        return {}


def check_if_job_ran(worksheet: Any, job_key: str) -> bool:
    """
    Checks the 'Jobs' sheet to see if a job with the given key has already run.
    This version is more robust as it checks the entire column instead of relying on find().
    """
    try:
        logging.info(f"Verifying lock key '{job_key}'...")
        all_job_keys_in_sheet = worksheet.col_values(1)

        if job_key in all_job_keys_in_sheet:
            logging.info(
                f"Lock key '{job_key}' found in column A. Job has already run. Skipping."
            )
            return True
        else:
            logging.info(f"Lock key '{job_key}' not found. Job is clear to run.")
            return False

    except Exception as e:
        logging.error(f"Error checking job status for '{job_key}': {e}")
        return True  # Assume it ran to be safe


def mark_job_as_triggered(worksheet: Any, job_key: str) -> None:
    """Writes a new entry to the 'Jobs' sheet to log and lock the job."""
    try:
        timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        status = "TRIGGERED"
        worksheet.append_row([job_key, timestamp_utc, status])
        logging.info(f"Successfully wrote lock key '{job_key}' to Jobs sheet.")
    except Exception as e:
        logging.error(f"Failed to write job log for '{job_key}': {e}")


def main() -> None:
    """Main function to check schedules and trigger jobs."""
    logging.info("---  dispatcher: Starting job dispatcher ---")

    scheduled_jobs = get_scheduled_jobs()
    if not scheduled_jobs:
        logging.info("Dispatcher: No schedules found. Exiting.")
        return

    try:
        tz_str = os.environ.get("TZ", "Europe/Bratislava")
        target_tz = ZoneInfo(tz_str)
    except ZoneInfoNotFoundError:
        logging.critical(f"Timezone '{tz_str}' is invalid. Aborting.")
        sys.exit(1)

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            app_config = json.load(f)

        logging_config = app_config.get("logging_spreadsheet")
        if not logging_config or not logging_config.get("spreadsheet_url"):
            logging.critical(
                "Dispatcher: 'logging_spreadsheet' section with 'spreadsheet_url' not found. Aborting."
            )
            sys.exit(1)

        spreadsheet_url = logging_config["spreadsheet_url"]
        log_sheet_name = logging_config.get("jobs_worksheet_name", "Jobs")

        # --- FIX: Use the public function from the refactored sheets_service ---
        log_worksheet = sheets_service.get_worksheet(spreadsheet_url, log_sheet_name)
        if not log_worksheet:
            # get_worksheet already logs its own errors.
            logging.critical(
                f"Dispatcher: Could not access log sheet '{log_sheet_name}'. Aborting."
            )
            sys.exit(1)

        headers = log_worksheet.row_values(1)
        if not all(
            h in headers for h in ["job_key", "trigger_timestamp_utc", "status"]
        ):
            logging.critical(
                f"Log sheet '{log_sheet_name}' is missing required headers. Aborting."
            )
            sys.exit(1)
        logging.info(f"Log sheet headers validated successfully: {headers}")

    except Exception as e:
        logging.critical(f"Dispatcher: Failed to access or validate the log sheet: {e}")
        sys.exit(1)

    now_utc = datetime.now(timezone.utc)
    today_local = datetime.now(target_tz).strftime("%Y-%m-%d")

    for time_key, scheduled_time_str in scheduled_jobs.items():
        try:
            hour, minute = map(int, scheduled_time_str.split(":"))

            scheduled_dt_local = datetime.now(target_tz).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            scheduled_dt_utc = scheduled_dt_local.astimezone(timezone.utc)

            time_diff_minutes = (now_utc - scheduled_dt_utc).total_seconds() / 60

            if 0 <= time_diff_minutes <= TIME_WINDOW_MINUTES:
                job_key = f"{time_key}_{today_local}"

                if not check_if_job_ran(log_worksheet, job_key):
                    mark_job_as_triggered(log_worksheet, job_key)
                    logging.info(
                        f"--> Dispatcher: Triggering command: python run_once.py {time_key}"
                    )
                    subprocess.run(["python", "run_once.py", time_key], check=True)
                    logging.info(f"--> Dispatcher: Finished triggering for {time_key}.")

        except Exception as e:
            logging.critical(
                f"Dispatcher: An unhandled error occurred for job {time_key}: {e}",
                exc_info=True,
            )

    logging.info("--- dispatcher: Finished checking all schedules ---")


if __name__ == "__main__":
    main()

# End of trigger_jobs.py (v. 0009)
