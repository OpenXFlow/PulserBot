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
from typing import Any, Dict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# This is necessary because the script runs from the root directory
sys.path.append("src")

from src.config import setup_logging
from src.services import sheets_service

# --- Configuration ---
TIME_WINDOW_MINUTES = 360

setup_logging()


def get_scheduled_jobs() -> Dict[str, str]:
    """
    Loads the schedule from the main config.json file.

    Returns:
        Dict[str, str]: A dictionary mapping time keys (e.g., 'time1') to
        time strings (e.g., '06:00'). Returns an empty dict on failure.
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            app_config = json.load(f)
        schedule = app_config.get("schedule")
        return schedule if isinstance(schedule, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.critical(f"Failed to load or parse config.json: {e}")
        return {}


def check_if_job_ran(worksheet: Any, job_key: str) -> bool:
    """
    Checks the 'Jobs' sheet to see if a job has already been logged and run.

    This prevents duplicate job executions in case the workflow runs multiple
    times within the same time window.

    Args:
        worksheet (Any): The gspread.Worksheet object for the 'Jobs' log sheet.
        job_key (str): The unique key for the job run (e.g., 'time1_2025-11-05').

    Returns:
        bool: True if the job key is found in the sheet, False otherwise.
    """
    try:
        logging.info(f"Verifying lock key '{job_key}'...")
        all_job_keys_in_sheet = worksheet.col_values(1)
        if job_key in all_job_keys_in_sheet:
            logging.info(f"Lock key '{job_key}' found. Job has already run. Skipping.")
            return True
        logging.info(f"Lock key '{job_key}' not found. Job is clear to run.")
        return False
    except Exception as e:
        logging.error(f"Error checking job status for '{job_key}': {e}")
        return True  # Assume it ran to be safe


def mark_job_as_triggered(worksheet: Any, job_key: str) -> None:
    """
    Writes a new entry to the 'Jobs' sheet to log and lock the job execution.

    Args:
        worksheet (Any): The gspread.Worksheet object for the 'Jobs' log sheet.
        job_key (str): The unique key for the job run to be logged.
    """
    try:
        timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        worksheet.append_row([job_key, timestamp_utc, "TRIGGERED"])
        logging.info(f"Successfully wrote lock key '{job_key}' to Jobs sheet.")
    except Exception as e:
        logging.error(f"Failed to write job log for '{job_key}': {e}")


def main() -> None:
    """
    The main function to check schedules and trigger jobs.

    This function orchestrates the entire process from loading configurations,
    checking time windows, verifying job locks, and dispatching jobs via
    a subprocess call to `run_once.py`.
    """
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

        sheets_service.initialize_sheets_service(app_config)

        log_sheet_ref = {"spreadsheet_key": "YDP_System", "worksheet_key": "jobs"}
        log_worksheet = sheets_service.get_worksheet(log_sheet_ref)

        if not log_worksheet:
            logging.critical(
                "Dispatcher: Could not access the 'Jobs' log sheet. Aborting."
            )
            sys.exit(1)

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
        except Exception:
            logging.exception(
                f"Dispatcher: An unhandled error occurred for job {time_key}"
            )

    logging.info("--- dispatcher: Finished checking all schedules ---")


if __name__ == "__main__":
    main()

# End of trigger_jobs.py (v. 0011)
