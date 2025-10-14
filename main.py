# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the LICENSE file in the project root.

# main.py
"""
The main entry point for the YourDailyPulse application when running as a
long-running web service (e.g., on Render).

This script is responsible for:
1.  Initializing external monitoring services like Sentry.
2.  Starting a lightweight Flask web server in a background thread to serve
    health checks and prevent the service from sleeping on free hosting tiers.
3.  Initializing and starting the APScheduler, which triggers the core
    application logic at the times defined in `config.json`.
"""

from dotenv import load_dotenv

# --- CRITICAL: Load .env file BEFORE importing any local modules ---
load_dotenv()

import logging  # noqa: E402
import os  # noqa: E402
from collections import defaultdict  # noqa: E402
from threading import Thread  # noqa: E402
from typing import Any, Dict, List  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

import sentry_sdk  # noqa: E402
from apscheduler.schedulers.blocking import BlockingScheduler  # noqa: E402
from apscheduler.triggers.cron import CronTrigger  # noqa: E402
from flask import Flask  # noqa: E402
from sentry_sdk.integrations.flask import FlaskIntegration  # noqa: E402

from src.config import load_app_config, setup_logging  # noqa: E402
from src.core import generate_and_send  # noqa: E402

# --- Web Server (for Render "keep-alive") ---
app = Flask(__name__)


@app.route("/")
def home() -> str:
    """A simple web endpoint to confirm that the application is running."""
    return "OK: The scheduler is active."


def run_web_server() -> None:
    """Runs the Flask web server in a separate thread."""
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def log_configuration_summary(config: Dict[str, Any], tz: ZoneInfo) -> None:
    """
    Logs a detailed summary of the loaded configuration at DEBUG level.
    """
    logging.debug("--- 🚀 Configuration & Schedule Summary ---")
    logging.debug(f"Timezone: {tz}")
    themes = config.get("themes", {})
    if themes:
        logging.debug("Detected Themes:")
        for name, details in themes.items():
            theme_type = details.get("type", "static")
            logging.debug(f"  - '{name}' (type: {theme_type})")
    else:
        logging.warning("No themes found in configuration.")

    users = config.get("users", [])
    schedule_times = config.get("schedule", {})
    if users and schedule_times:
        logging.debug("User Subscription Plan:")
        plan: defaultdict[str, defaultdict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for user in users:
            user_desc = user.get("description", "Unknown User")
            subscriptions = user.get("subscriptions", {})
            for time_key, themes_list in subscriptions.items():
                for theme in themes_list:
                    plan[time_key][theme].append(user_desc)

        for time_key, time_str in schedule_times.items():
            logging.debug(f"  Schedule for {time_key} ({time_str}):")
            if time_key in plan:
                for theme, subscribed_users in plan[time_key].items():
                    logging.debug(
                        f"    - Theme: '{theme}' -> Users: [{', '.join(subscribed_users)}]"
                    )
            else:
                logging.debug("    - No subscriptions for this time slot.")
    else:
        logging.warning("No users or schedules found to create a subscription plan.")

    logging.debug("------------------------------------------")


def main() -> None:
    """
    The main function that sets up and starts the application.
    """
    # --- STEP 1: Initialize Sentry SDK (before logging setup) ---
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    if SENTRY_DSN:
        try:
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                # Use the official Flask integration for rich web context
                integrations=[FlaskIntegration()],
                # Also explicitly enable the modern Logs feature
                enable_logs=True,
                # Keep tracing enabled for performance monitoring
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
            # This uses print() because logging is not yet configured
            print("Sentry SDK initialized with FlaskIntegration and Logs enabled.")
        except Exception as e:
            print(f"Failed to initialize Sentry: {e}")
    else:
        print("SENTRY_DSN not found. Sentry is not initialized.")

    # --- STEP 2: Configure logging (now that Sentry is ready) ---
    setup_logging()

    logging.info(f"SENTRY_DSN found: {SENTRY_DSN is not None}")

    # --- STEP 3: Continue with the rest of the application setup ---
    flask_thread = Thread(target=run_web_server)
    flask_thread.daemon = True
    flask_thread.start()
    logging.info("Flask web server started in a background thread.")

    config, tz = load_app_config()
    if not config:
        logging.critical("Application cannot start due to missing or invalid config.")
        return

    log_configuration_summary(config, tz)

    schedule_times = config.get("schedule", {})
    if not schedule_times:
        logging.warning("No schedules found in 'config.json'. Scheduler not started.")
        flask_thread.join()
        return

    scheduler = BlockingScheduler(timezone=tz)
    for time_key, time_str in schedule_times.items():
        try:
            hour, minute = map(int, time_str.split(":"))
            scheduler.add_job(
                func=generate_and_send,
                args=[time_key],
                trigger=CronTrigger(hour=hour, minute=minute, timezone=tz),
                id=f"job_{time_key}",
                name=f"Task for {time_key} at {time_str}",
            )
        except (ValueError, AttributeError) as e:
            logging.error(
                f"Invalid time format '{time_str}' for key '{time_key}'. Error: {e}"
            )

    logging.info("APScheduler initialized. Final job list from scheduler:")
    scheduler.print_jobs()

    try:
        logging.info("Scheduler starting... Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped.")


if __name__ == "__main__":
    main()

# End of main.py (v. 0018)
