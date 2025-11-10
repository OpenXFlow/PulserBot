# Guide to Creating and Operating Your Own Bot

This document provides a comprehensive, step-by-step guide for creating, configuring, deploying, and maintaining your own automated bot instance based on the **YourDailyPulse** project. This guide is intended for technically proficient users (e.g., developers) who are comfortable with Git, Python, and cloud service APIs.

## 1. Initial Environment Setup

This phase involves preparing your local and cloud environments.

### 1.1. Core Prerequisites
- **GitHub Account:** If you don't have one, register at [github.com](https://github.com).
- **Software Installation:** Ensure you have **Git** and **Python** (version 3.11 or newer) installed on your local machine.
- **Code Editor:** A modern code editor like Visual Studio Code is highly recommended.

### 1.2. Project Scaffolding
1.  **Clone the Source Project:** Download the original public project from its repository.
    ```bash
    git clone https://github.com/your-username/YourDailyPulse.git
    ```
2.  **Create Your Private Repository:**
    - On GitHub, create a **new, personal repository**.
    - **Crucially, set this repository to `Private`**. This is essential to protect your personal content, API keys, and configuration files from public exposure.
3.  **Prepare Your Local Project:**
    - Clone your new, empty private repository to your local machine.
    - Copy all files and folders from the original `YourDailyPulse` project into your new private project's directory.
    - From now on, you will work exclusively within your own private repository.

### 1.3. Obtaining API Keys & Credentials
For the bot to function, you must register with several cloud services and obtain API keys. Store these keys securely, as you will need them for the `.env` file.

| Service | Purpose |
| :--- | :--- |
| **Telegram** | To create the bot itself and get a token for sending messages. |
| **Google Cloud** | To get `credentials.json` for accessing Google Sheets API and Google Drive API. |
| **Groq** | Provides the LLM for creative text generation. |
| **Sentry** | For professional error logging and application monitoring. |
| **Unsplash** | Provides high-quality, public-domain photos. |
| **Cloudinary** | (Optional) For hosting your own private photos (e.g., family pictures). |
| **OpenWeatherMap**| Provides real-time weather forecasts. |

---

## 2. Comprehensive Configuration

This is the most critical phase. The bot's behavior is entirely controlled by three main configuration entities: `.env`, `credentials.json`, and `config.json`.

### 2.1. `.env` File - Storing Secrets
This file stores all your secret API keys and tokens, keeping them out of your main configuration. In the project root, rename the example file `.env.example` to **`.env`** and carefully fill in all the API keys you obtained.

#### How to Create a Bot and Get a Token on Telegram
1.  **Find BotFather:** In the Telegram app, search for `@BotFather` (it has a blue verification checkmark).
2.  **Create a New Bot:** Send the command `/newbot`.
3.  **Set a Name:** Provide a friendly, human-readable name (e.g., `My Daily Companion`).
4.  **Set a Username:** Provide a unique username that must end in "bot" (e.g., `MyDailyCompanion123Bot`).
5.  **Copy the Token:** BotFather will provide a long API token. Copy this token and paste it into your `.env` file under the `TELEGRAM_BOT_TOKEN` variable.

### 2.2. `credentials.json` File - Access to Google Services
This file acts as a private key, allowing your application to authenticate with your Google account as a service.

#### How to Obtain `credentials.json`
1.  **Go to Google Cloud Console:** Navigate to [console.cloud.google.com](https://console.cloud.google.com/) and select your project (or create a new one).
2.  **Enable APIs:** In the sidebar menu, go to **APIs & Services -> Library**. Search for and **enable** both of these APIs:
    - **Google Drive API** (essential for discovering files)
    - **Google Sheets API** (essential for reading/writing data)
3.  **Create a Service Account:**
    - Go to **IAM & Admin -> Service Accounts**.
    - Click **+ CREATE SERVICE ACCOUNT**.
    - Give it a name (e.g., `yourdailypulse-bot`) and click **CREATE AND CONTINUE**.
    - In the "Grant this service account access to project" step, assign the **Editor** role to give it sufficient permissions within the project. Click **CONTINUE**, then **DONE**.
4.  **Generate a JSON Key:**
    - Find your newly created service account in the list. Click the three dots at the end of its row and select **Manage keys**.
    - Click **ADD KEY -> Create new key**.
    - Select **JSON** as the key type and click **CREATE**.
    - Your browser will automatically download a JSON file. Rename this file to **`credentials.json`** and place it in the root directory of your project.

### 2.3. Google Sheets - The Content Database
Your content lives in Google Sheets. Our new architecture uses multiple, logically separated spreadsheets for better organization and security.

#### How to Prepare Your Google Sheets
1.  **Create the Spreadsheets:**
    - Go to [sheets.google.com](https://sheets.google.com) and create the six required spreadsheets with these exact names:
        1.  `YDP_System`
        2.  `YDP_LLM_Static_Spiritual`
        3.  `YDP_Simple_Static_Family`
        4.  `YDP_Simple_Static_Art`
        5.  `YDP_LLM_Dynamic_MorningBriefing`
        6.  `YDP_LLM_Dynamic_GermanLesson`
2.  **Create and Populate Worksheets:**
    - For each spreadsheet, create the necessary worksheets (tabs) as defined in `config.json`.
    - **Crucially, copy the exact column headers** for each sheet from the project's documentation (e.g., from `docs/Google_sheets_examples/`).
    - Populate the sheets with your own data. For all new content rows, ensure the `used` column is set to `FALSE`.
3.  **Share All Spreadsheets with the Service Account:**
    - Open your `credentials.json` file and copy the `client_email` address (e.g., `yourdailypulse-bot@...gserviceaccount.com`).
    - For **each of your six spreadsheets**, click the "Share" button, paste the service account's email, assign it the **Editor** role, and save.

### 2.4. `config.json` - The Brain of the Application
This file orchestrates everything. You must carefully update it to point to your new resources.

1.  **Update `spreadsheet_url`:**
    - For each of the six main entries in the `data_sources` section (`YDP_System`, `YDP_LLM_Static_Spiritual`, etc.), paste the corresponding spreadsheet URL you get from the "Share" dialog in Google Sheets.
2.  **Configure Users and Subscriptions:**
    - **Get Your Chat ID:** On Telegram, find `@userinfobot`, send it the `/start` command, and it will reply with your unique Chat ID (a number).
    - **Add Yourself as a User:** In the `users` section, create an entry for yourself. Set `description`, `language`, and paste your Chat ID into the `identifier` field.
    - **Set Subscriptions:** In the `subscriptions` block for your user, define which themes (`bible_sk`, `german_lesson`, etc.) you want to receive at which scheduled time (`time1`, `time2`, etc.).

---

## 3. Local Testing

Before deploying, always test your setup locally.

1.  **Install Dependencies:**
    - It is highly recommended to use a virtual environment.
    ```bash
    # Create and activate the environment
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On macOS/Linux:
    # source .venv/bin/activate
    
    # Install required packages
    pip install -r requirements.txt
    ```
2.  **Run a Test:**
    - Use the `run_once.py` script to trigger a specific job for a specific user. This allows for isolated and repeatable testing.
    ```bash
    # Example: Run the 'time3' job for user 'Jozef_D'
    python run_once.py time3 users Jozef_D
    ```
    - Check your Telegram for the message and review the console output for any `ERROR` or `WARNING` logs.

---

## 4. Deployment to GitHub Actions

Once local testing is successful, you can deploy the bot for fully automated, scheduled execution.

### 4.1. Set GitHub Secrets
This is the most critical step for security.
1.  Go to your private repository on GitHub.
2.  Navigate to **Settings -> Secrets and variables -> Actions**.
3.  Under **Repository secrets**, click **New repository secret** for each of the following, ensuring the names match exactly.

| Secret Name | Secret Value (Copied from your local files) |
| :--- | :--- |
| `GCP_SA_KEY` | The **entire content** of your `credentials.json` file. |
| `GROQ_API_KEY` | Your API key from the `.env` file. |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from the `.env` file. |
| `OPENWEATHER_API_KEY`| Your OpenWeatherMap key from the `.env` file. |
| `UNSPLASH_ACCESS_KEY` | Your Unsplash key from the `.env` file. |
| `SENTRY_DSN` | Your Sentry DSN from the `.env` file. |
| `CLOUDINARY_CLOUD_NAME`| Your Cloudinary name from the `.env` file. |
| `CLOUDINARY_API_KEY` | Your Cloudinary API key from the `.env` file. |
| `CLOUDINARY_API_SECRET`| Your Cloudinary API secret from the `.env` file. |

### 4.2. Push Your Code
- Commit all your configured files (`config.json`, etc.) and push them to the `main` branch of your private repository.
- **NEVER commit your `.env` or `credentials.json` files.** The `.gitignore` file should already be configured to prevent this.

**Deployment is complete!** GitHub Actions will now automatically run your `trigger_jobs.py` script based on the `cron` schedule defined in `.github/workflows/scheduler.yml` (e.g., every hour).

---

## 5. Management and Troubleshooting

### Temporarily Disabling the Bot
1.  Go to the **Actions** tab in your GitHub repository.
2.  Select the workflow (e.g., `YourDailyPulse Job Scheduler`) from the left sidebar.
3.  Click the three-dots menu (`...`) and choose **Disable workflow**.

### Analyzing a Failed Run
If you see a **red cross (❌)** next to a workflow run, it has failed.
1.  Click on the name of the failed run.
2.  In the left summary, click on the job name (e.g., `run-dispatcher`).
3.  Find the step with the red cross (usually `Run the dispatcher script`).
4.  Expand its details to view the full log output. The error message will be at the bottom, typically highlighted in red.

---

## 6. Developer Tools (`tools.py`)

The project includes `tools.py`, a powerful command-line script for manual data management.

### `generate_photo_db`
Connects to Cloudinary and generates a CSV file of your photos, ready for import into your `FamilyPhotos` Google Sheet.
```bash
python tools.py generate_photo_db <cloudinary_folder_name> <output_file.csv>
```

### `download_sheets`
Reads your `config.json` and downloads a local backup of every worksheet from every configured spreadsheet into a structured directory. This is essential for backups and version control.
```bash
python tools.py download_sheets <output_directory>```

### `fetch_art_data`
Fetches artwork data from The MET API for a specified department and saves it to a CSV, ready for import into your `EuArt` Google Sheet.
```bash
python tools.py fetch_art_data <department_id> <data_output.csv> <id_cache.csv> [max_items]
```