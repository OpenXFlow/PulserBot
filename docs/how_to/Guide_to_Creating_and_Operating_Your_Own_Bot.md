# Guide to Creating and Operating Your Own Bot

This document describes the complete process from the initial environment setup to the deployment and troubleshooting of an automated bot based on the **PulserBot** project. The guide is intended for technically proficient users (programmers) who want to create and run their own instance of the bot.

## 1. Initial Setup

### Basic Steps
- **Register on GitHub:** Create an account at [github.com](https://github.com).
- **Install Software:** You must have **Git** and **Python** (version 3.11+) installed on your PC.
- **Download/clone the Project:** Download the source project from the public repository (e.g., via a Git extension in your editor or using terminal commands: git clone https://github.com/OpenXFlow/PulserBot.git )
- **Create Your Own Project on GitHub:**
    - On GitHub, create a new, personal repository. **It is strongly recommended that the project be private**, not public, especially if you plan to use personal content like family photos.
- **Prepare the Local Project:**
    - Clone this new, empty project to your PC.
    - Copy all files and folders from the original (cloned PulserBot) project into your new project's directory. From now on, you will only work with your own project.
- **Create a Bot on Telegram:** Following the instructions in the [How to Create a Bot and Get a Token on Telegram](#how-to-create-a-bot-and-get-a-token-on-telegram) section, create your bot and obtain your Telegram UID (Chat ID) as described in the [Configuring the First User](#configuring-the-first-user) section.

### Obtaining API Keys
For full functionality, you must register and obtain API keys from all the cloud applications the tool communicates with. Store them securely; you will need them for the `.env` file.
- **Groq** (LLM for text generation)
- **Sentry** (error logging and monitoring)
- **Unsplash** (public domain photos)
- **Cloudinary** (hosting for private photos)
- **OpenWeatherMap** (weather forecasts)

---

## 2. Configuration Setup

For local debugging and later for production, you need to correctly set up the configuration files: `.env`, `credentials.json`, and `config.json`.

### `.env` - Storing API Keys
This file securely stores your secret keys. In the project root, rename `.env.example` to `.env` and fill in all the API keys you obtained in the previous step.

#### How to Create a Bot and Get a Token on Telegram
1.  **Find BotFather:**
    *   Open Telegram and type `@BotFather` into the search bar (it has a blue verification icon next to its name).
    *   Start a conversation with it.
2.  **Run the Creation Command:**
    *   Send the following command in the chat:
        ```
        /newbot
        ```
3.  **Enter a Name (Friendly Name):**
    *   BotFather will ask you for a name. This is a human-readable name that will be displayed to your users in their contact list (e.g., `Pulzer`).
    *   Type the desired name and send it.
4.  **Enter a Username (Unique Identifier):**
    *   Next, it will ask for a "username". The name must end in "bot". For example: `MyDailyPulseBot` or `PulserBot123`.
    *   Type the desired username and send it.
5.  **Done - Copy Your Token:**
    *   If the username was available, BotFather will congratulate you and display the **API Token** in the final message. It's a long string of characters.
    *   Copy this token securely. It is the key to your bot, which you will place in the `.env` file.





### `credentials.json` - Access to Google Services
This file is the key that allows your application to securely log in to your Google account and work with Google Sheets and Google Drive.

#### How to Obtain credentials.json
1.  **Create a Google Cloud Project:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project.
2.  **Enable APIs:**
    *   In the menu, find **APIs & Services -> Library**.
    *   Enable these two services: **Google Drive API** and **Google Sheets API**.
3.  **Create a Service Account:**
    *   In the menu, go to **IAM & Admin -> Service Accounts**.
    *   Click **CREATE SERVICE ACCOUNT**, name it, and click **CREATE AND CONTINUE**.
    *   Assign the **Editor** role and click **DONE**.
4.  **Generate a JSON Key:**
    *   In the list of Service Accounts, click on the email of the one you just created.
    *   Go to the **KEYS** tab.
    *   Click **ADD KEY -> Create new key**.
    *   Choose **JSON** and click **CREATE**. The browser will automatically download your `credentials.json` file.
5.  **Share the Google Sheet with the Service Account:**
    *   **Get the Email:** In the details of your Service Account (or directly in `credentials.json`), copy its email address (it looks like `...gserviceaccount.com`).
    *   **Open Your Google Sheet:** In your browser, open the document you will use as your database (e.g., `PulserBot_Content`).
    *   **Click "Share":** In the top right corner.
    *   **Paste the Email:** In the "Add people and groups" field, paste the copied service account email address.
    *   **Set Permissions:** Make sure it has the **Editor** role.
    *   **Send the Invitation:** Click **Send**. Your application now has access to this document.
    *   **Copy the Link (for config.json):** In the same "Share" window, click "Copy link". You will paste this link into `config.json` later.

### Google Sheets - The Database
You need to create and populate the database in your Google Sheets.

#### How to Create and Prepare Google Sheets:
1.  **Create the Document:**
    *   Go to [sheets.google.com](https://sheets.google.com) and create a new, blank spreadsheet (e.g., `PulserBot_Content`).
2.  **Create Individual Worksheets:**
    *   At the bottom of the screen, rename `Sheet1` to the name of your first data source (e.g., `Jobs`).
    *   Click the `+` icon (Add Sheet) to add another blank sheet and rename it (e.g., `BibleEN`).
    *   Repeat this process for all the sheets defined in your `config.json.example` (e.g., `PhilosophyEN`, `ContentRotation`, `EuArtEng`, `SlowGerman`, etc.).
3.  **Populate the Headers (Column Names):**
    *   For each sheet, click on cell A1 and type the exact column names into the first row according to the structure from the examples (e.g., in `PulserBot\docs\Google_sheets_exemples\`).
4.  **Populate the Data:**
    *   Under the headers in each sheet, insert your data. You can use the examples from `PulserBot\docs\Google_sheets_exemples\`.
    *   **Important:** Ensure that in the `used` column, all new rows have the value `FALSE`.

### Updating `config.json`
This file controls the application's behavior, data sources, and users.

**a) `spreadsheet_url`:**
- Gradually fill in all `spreadsheet_url` entries in the `logging_spreadsheet`, `themes`, and `data_sources` sections with the link to your Google Sheet document, which you copied in step 5 of the [credentials.json preparation](#how-to-obtain-credentialsjson).
- Example:
  ```json
  "logging_spreadsheet": {
      "spreadsheet_url": "https://docs.google.com/spreadsheets/d/..."
  },
  "themes": {
      "old_testament_study_en": {
          "spreadsheet_url": "https://docs.google.com/spreadsheets/d/..."
      }
  },
  "data_sources": {
      "name_days_en": {
          "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
          "worksheet_name": "NameDayEng"
      }
  }
  ```

**b) `schedule`:**
- Configure the `schedule` item. This part is related to GitHub Actions and determines when messages should be sent to users.

**c) Creating the First User (Yourself):**

#### Configuring the First User
1.  **Get Your Telegram Chat ID:**
    *   Your Chat ID is a unique number that Telegram assigns to your private conversation.
    *   Open Telegram.
    *   Type `@userinfobot` into the search field and open the chat with this bot.
    *   Click the **START** button (or send the `/start` command).
    *   The bot will immediately reply, and in the first sentence of its message will be your **Id**. It's a number, for example, `123456789`. This is your Chat ID.
2.  **Configure `channels`:** In the `config.json` file, find the `users` section and enter your Chat ID in the `identifier` field.
    ```json
    "channels": [
        {
            "platform": "telegram",
            "identifier": "YOUR_TELEGRAM_CHAT_ID"
        }
    ]
    ```
3.  **Configure `subscriptions`:** Set up which topics the application should send to the user and when.

### Setting up `..github\workflows\scheduler.yml`
This file is used by GitHub Actions to set up `cron` jobs (scheduled script execution).

---

## 3. Local Testing

Once the configuration is in order, you can test the application locally.

1.  **Activate the virtual environment and install dependencies:**
    ```bash
    # Create and activate the environment
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    
    # Install packages
    pip install -r requirements.txt
    ```

2.  **Run a test for a specific task and user:**
    ```bash
    python run_once.py time1 users user_1
    (or python run_once.py time1 users user_1 user2 )
    ```
**What happens in the background:**
- The `run_once.py` script is executed.
- It calls the function `generate_and_send(time_key="time1", user_filter=["user_x"])`.



---

## 4. Running the Application on GitHub Actions

If local testing was successful, you can deploy the application for automatic execution via GitHub Actions.

#### 1. Set GitHub Secrets (The Most Important Step):
- Go to the main page of your repository on GitHub.
- Click on **Settings** -> **Secrets and variables** -> **Actions**.
- In the **"Repository secrets"** section, click **"New repository secret"** and create the following secrets one by one. **The names must match exactly.**

| Secret Name | Secret Value (Without quotes) |
| :--- | :--- |
| `GCP_SA_KEY` | Copy the **entire content** of your `credentials.json` file here. |
| `GROQ_API_KEY` | Your API key from Groq. |
| `TELEGRAM_BOT_TOKEN` | Your token for the Telegram bot. |
| `OPENWEATHER_API_KEY` | Your API key from OpenWeatherMap. |
| `UNSPLASH_ACCESS_KEY` | Your Access Key from Unsplash. |
| `SENTRY_DSN` | Your DSN key from Sentry. |
| `CLOUDINARY_CLOUD_NAME`| Your Cloud Name from Cloudinary. |
| `CLOUDINARY_API_KEY` | Your API Key from Cloudinary. |
| `CLOUDINARY_API_SECRET`| Your API Secret from Cloudinary. |

#### 2. Other Configuration Variables
These variables are already set directly in `scheduler.yml`:
- `LOG_LEVEL: 'INFO'` (INFO is better than DEBUG for production runs)
- `TZ: 'Europe/Bratislava'`
- `GROQ_MODEL="openai/gpt-oss-120b"`

#### 3. Upload Changes to GitHub:
- Save all modified files and `git push` the changes to your `main` branch.

**Done!** From this moment on, GitHub Actions will handle the automatic execution of the script according to the set schedule (e.g., every 30 minutes).

#### Note on `run_once.py`
- The **`run_once.py`** script knows exactly which users it has sent messages to, but it runs as a separate process and cannot easily "return" this information to `trigger_jobs.py`.
- **Changes in `run_once.py`:**
    - **Removing Tools:** Tools like `generate_photo_db` or `download_sheets` are intended for manual management. They will be moved to a separate script (e.g., `tools.py`) to make `run_once.py` single-purpose.
    - **Simplifying Logic:** The script's only task will be to run `generate_and_send` with the given parameters.
    - **Updating Documentation:** The docstring will clearly state that this is a manual testing tool, not intended for automation.


---

## 5. Management and Troubleshooting

### How to Temporarily Stop GitHub Actions
If you need to temporarily disable automatic execution:
1.  Go to the main page of your repository on **GitHub**.
2.  Click on the **"Actions"** tab.
3.  In the left menu, you will see the name of your workflow (e.g., `Pulser Job Scheduler`). Click on it.
4.  Next to the workflow name, you will see a button with three dots (`...`). Click it.
5.  Select the **"Disable workflow"** option.
This will temporarily disable the entire scheduler until you manually re-enable it.

### Analysis of a Failed Application Run
#### What Do Two Records Mean?
If you see two entries in the logs, it's because the workflow was triggered in two different ways:
1.  **"Scheduled":** This is the **automatic run** executed by GitHub based on the `cron` rule. It's proof that the scheduler is active.
2.  **"Manually run by...":** This is a run that **you triggered manually** from the GitHub Actions interface for testing purposes.
**Conclusion:** Seeing two records is fine and confirms that both triggering methods are working.

#### What Does a Red Cross  Mean?
This is the most crucial piece of information. A **red cross ** next to a run means that the execution attempt **failed**. 
Although the workflow was triggered, a critical error occurred in one of its steps. A short execution time (e.g., 21s) indicates that the error happened very early.

#### Solution: How to Find the Exact Cause of Failure
Act like a detective and analyze the logs:

1.  **Click on one of the failed runs:** In the list, click on its name.
2.  **View the run details:** In the left menu, click on `run-dispatcher`.
3.  **The steps will be displayed:** You will see a list of steps as defined in `scheduler.yml`:
    - `1. Checkout repository code`
    - `2. Set up Python`
    - `3. Install dependencies`
    - `4. Configure Google Service Account`
    - `5. Run the dispatcher script`
4.  **Find the step with the red cross:** One of the steps will be marked with a red cross (most likely step **#3** or **#5**).
5.  **Expand the step details:** Click on the failed step to view its detailed logs.
6.  **Find the error message:** At the end of the expanded log, you will see the **exact error message** that caused the failure (typically red text like `ModuleNotFoundError`, `FileNotFoundError`, etc.).


---

## 6. Developer Tools (`tools.py`)

The project includes a powerful command-line script, `tools.py`, for various data management tasks. These tools are meant to be run manually on your local machine.

### `generate_photo_db`
This tool connects to your Cloudinary account, finds all images in a specified folder, and generates a CSV file with direct URLs and metadata, ready for import into your `FamilyPhotos` Google Sheet.
**Usage:**
```bash
python tools.py generate_photo_db <folder_name> <output_file.csv>
```
- **Example:** `python tools.py generate_photo_db my_family_photos family_photos.csv`

### `download_sheets`
This tool reads your `config.json`, finds all unique Google Sheets used in the project, and downloads a local backup of each one as a separate CSV file.
**Usage:**
```bash
python tools.py download_sheets <output_directory>
```
- **Example:** `python tools.py download_sheets ./my_backups`

### `fetch_art_data`
This tool fetches artwork data from The MET API for a specific department and saves it to a CSV, ready for import into your `EuArt` Google Sheet. It uses a cache file for IDs to speed up subsequent runs.
**Usage:**
```bash
python tools.py fetch_art_data <dept_id> <data_output.csv> <id_cache.csv> [max_items]
```
- **Example (to fetch 100 paintings):** `python tools.py fetch_art_data 11 met_art.csv met_art_ids.csv 100`

---