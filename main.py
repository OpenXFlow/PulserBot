# The MIT License (MIT)
# Copyright (c) 2025 Jozef Darida  (LinkedIn/Xing)
# For full license text, see the project root.

# main.py
"""
The main entry point for the YourDailyPulse application when running as a
long-running web service (e.g., on Render/Heroku).

Updated Architecture (World-Ready):
1.  Web Server: Runs Flask in a background thread for health checks.
2.  Scheduler: Triggers a job EVERY HOUR (at minute 0).
3.  Execution: Calls the async core logic via `asyncio.run()`.

Core logic now handles per-user timezones dynamically.

run_once vs main
In short: the first script is stateless, while the second is a daemon.

run_once.py is designed for serverless environments (like GitHub Actions),
where the script is triggered by an external trigger (CRON),
performs a one-time user check, and then exits immediately, saving resources.

main.py is designed for persistent deployments (like Render),
where the application runs 24/7, has its own internal scheduler,
and a web server to keep it alive.

While run_once.py lets GitHub handle the timing,
main.py handles the timing itself in an infinite loop, waiting for an hour.


How main works now:
Flask runs in the background (so you can ping the service).
The scheduler waits for a full hour (e.g. 14:00, 15:00).
When the full hour strikes, it runs job_wrapper_hourly_tick.
The wrapper runs asyncio.run(generate_and_send_async(...)).
core.py (which we already modified) fetches the users, calculates their local time for each, and if it matches the full hour, sends a message.

"""

import asyncio
import logging
import os
from threading import Thread

from dotenv import load_dotenv

# --- CRITICAL: Load .env file BEFORE importing any local modules ---
load_dotenv()

import sentry_sdk  # noqa: E402
from apscheduler.schedulers.blocking import BlockingScheduler  # noqa: E402
from apscheduler.triggers.cron import CronTrigger  # noqa: E402
from flask import Flask  # noqa: E402
from sentry_sdk.integrations.flask import FlaskIntegration  # noqa: E402

from src.config import load_app_config, setup_logging  # noqa: E402
from src.core import generate_and_send_async  # noqa: E402 -- Updated async import

# --- Web Server (for Render/Heroku "keep-alive") ---
app = Flask(__name__)


@app.route("/")
def home() -> str:
    """A simple web endpoint to confirm that the application is running."""
    return "OK: YourDailyPulse Service is Active (Hourly World-Ready Mode)."


def run_web_server() -> None:
    """Runs the Flask web server in a separate thread."""
    port = int(os.environ.get("PORT", 10000))
    # Disable reloader to prevent main thread duplication
    app.run(host="0.0.0.0", port=port, use_reloader=False)


def job_wrapper_hourly_tick() -> None:
    """
    Synchronous wrapper to run the async core logic.
    This function is called by the BlockingScheduler.
    """
    logging.info("⏰ SCHEDULER: Triggering global hourly check...")
    try:
        # Create a new event loop for this run to ensure clean state
        asyncio.run(generate_and_send_async(time_key="hourly_service_tick"))
    except Exception as e:
        logging.exception(f"Critical error in hourly job wrapper: {e}")


def main() -> None:
    """
    The main function that sets up and starts the application.
    """
    # --- STEP 1: Initialize Sentry SDK ---
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    if SENTRY_DSN:
        try:
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                integrations=[FlaskIntegration()],
                enable_logs=True,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
            print("Sentry SDK initialized with FlaskIntegration.")
        except Exception as e:
            print(f"Failed to initialize Sentry: {e}")
    else:
        print("SENTRY_DSN not found. Sentry is not initialized.")

    # --- STEP 2: Configure logging ---
    setup_logging()

    # --- STEP 3: Load Config (Just for Timezone context) ---
    # We don't need the schedule from config anymore, but we need the server timezone.
    _, tz = load_app_config()

    logging.info(f"Application starting in timezone: {tz}")

    # --- STEP 4: Start Web Server ---
    flask_thread = Thread(target=run_web_server)
    flask_thread.daemon = True
    flask_thread.start()
    logging.info("Flask web server started in a background thread.")

    # --- STEP 5: Start Scheduler (World-Ready Mode) ---
    # We use BlockingScheduler because it keeps the main thread alive
    scheduler = BlockingScheduler(timezone=tz)

    # Add single job: Run every hour at minute 0
    scheduler.add_job(
        func=job_wrapper_hourly_tick,
        trigger=CronTrigger(minute=0, timezone=tz),
        id="global_hourly_job",
        name="Global Hourly User Check",
        misfire_grace_time=300,  # Allow 5 minutes delay if server is busy
    )

    logging.info("APScheduler initialized. Running in GLOBAL HOURLY MODE.")
    logging.info("Next run will check all users and their respective timezones.")

    scheduler.print_jobs()

    try:
        logging.info("Scheduler starting... Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped.")


if __name__ == "__main__":
    main()

# End of main.py (v. 0020)
