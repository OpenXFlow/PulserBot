--- START OF FILE Guide_to_Creating_and_Operating_Your_Own_Bot.md ---

# Guide to Creating and Operating Your Own Bot (v3.0 Hybrid)

This document provides a comprehensive, step-by-step guide for creating, configuring, deploying, and maintaining your own automated bot instance based on the **YourDailyPulse** project.

**Version 3.0 Update:** This guide covers the **Hybrid Architecture**, which includes setting up a **Firebase Database** and a **Frontend Web Application**.

---

## 1. Initial Environment Setup

This phase involves preparing your local machine and registering for necessary cloud services.

### 1.1. Core Prerequisites
- **GitHub Account:** Required for code hosting and automation.
- **Google Account:** Required for Firebase and Google Sheets.
- **Software:** Install **Git** and **Python** (3.11+) on your computer.
- **Editor:** Visual Studio Code is recommended.

### 1.2. Project Scaffolding
1.  **Clone the Source:**
    ```bash
    git clone https://github.com/YourUsername/YourDailyPulse.git
    cd YourDailyPulse
    ```
2.  **Private Repository:** It is highly recommended to push this code to a **Private Repository** on GitHub to protect your API keys and configuration.

---

## 2. Cloud Services Setup (The "Brain")

The bot relies on external services. You must set them up first.

### 2.1. Firebase (Database & Auth) - **CRITICAL STEP**
This is the central hub for user data.
1.  Go to [console.firebase.google.com](https://console.firebase.google.com/) and create a new project (e.g., "daily-pulse-bot").
2.  **Authentication:**
    -   Go to **Build -> Authentication -> Sign-in method**.
    -   Enable **Email/Password**.
3.  **Firestore Database:**
    -   Go to **Build -> Firestore Database**.
    -   Click **Create Database**. Start in **Production mode**.
    -   Choose a location near you (e.g., `eur3` for Europe).
    -   **Set Rules:** Go to the "Rules" tab and paste the secure rules (see `docs/firestore.rules.txt`).
4.  **Get Service Account (Backend Key):**
    -   Project Settings -> **Service accounts**.
    -   Click **Generate new private key**.
    -   Save the JSON file as **`credentials.json`** in your project root.
5.  **Get Web Config (Frontend Key):**
    -   Project Settings -> General -> **Your apps**.
    -   Click **</> (Web)** icon. Register app (e.g., "WebApp").
    -   Copy the `firebaseConfig` object (API Key, etc.). You will need this for Step 4.

### 2.2. Other API Keys
-   **Telegram:** Talk to `@BotFather` to create a bot and get the `TELEGRAM_BOT_TOKEN`.
-   **Groq:** Get an API Key for the LLM at [console.groq.com](https://console.groq.com).
-   **Sentry (Optional):** Create a project for Python/Flask to get a `DSN` for error monitoring.
-   **OpenWeatherMap / Unsplash:** Register for free API keys.

---

## 3. Local Configuration

### 3.1. `.env` File (Secrets)
Create a file named `.env` in the root directory and fill in your keys:
```ini
TELEGRAM_BOT_TOKEN=your_token_here
GROQ_API_KEY=gsk_...
OPENWEATHER_API_KEY=...
UNSPLASH_ACCESS_KEY=...
SENTRY_DSN=...
TZ=Europe/Bratislava
```

### 3.2. `config.json` (System Config)
Open `config.json`. You do **NOT** need to add users here anymore.
-   **Schedule:** Define when the global trigger runs (e.g., "07:00").
-   **Data Sources:** Update the `spreadsheet_url` for your Google Sheets (see Section 3.3).

### 3.3. Google Sheets (Content DB)
1.  Create the necessary Google Sheets (Templates are in `docs/Google_sheets_examples/`).
2.  **Share** each sheet with the `client_email` address found inside your `credentials.json` file (give "Editor" access).

---

## 4. Frontend Setup (Web App)

The Web App allows you (and others) to register, log in, and configure settings.

1.  **Update Config:** Open `webapp/assets/js/firebase-config.js`. Paste the `firebaseConfig` object you got in Step 2.1 (Web Config).
2.  **Redirect Page:** Ensure `docs/index.html` is configured to redirect to your live app URL (you will get this URL after the first deployment, or you can use the Firebase Hosting URL if you deploy there. For GitHub Pages, it's `https://yourname.github.io/YourRepo/`).

---

## 5. Deployment

### 5.1. Deploy Backend (GitHub Actions)
1.  Push your code to GitHub.
2.  Go to **Settings -> Secrets and variables -> Actions**.
3.  Add Repository Secrets:
    -   `GCP_SA_KEY`: Paste the **entire content** of `credentials.json`.
    -   Add all other keys from `.env` (`TELEGRAM_BOT_TOKEN`, `GROQ_API_KEY`, etc.).
4.  The bot will now run automatically according to the schedule in `.github/workflows/scheduler.yml`.

### 5.2. Deploy Frontend (GitHub Pages)
1.  Go to **Settings -> Pages**.
2.  Source: **Deploy from a branch**.
3.  Branch: `main`, Folder: `/docs`. (This hosts the documentation and redirect).
4.  **Alternative:** You can host the `webapp` folder directly on Firebase Hosting for better performance, or configure GitHub Pages to serve the `webapp` folder if you prefer.

---

## 6. How to Start Using the Bot

1.  **Open your Web App** (the GitHub Pages URL).
2.  **Register** a new account with your email and password.
3.  **Verify Email:** Check your inbox and click the link.
4.  **Log In:** Go back to the app.
5.  **Configure:**
    -   **Telegram Setup:** Enter the command `/start` to your bot in Telegram. Get your ID from `@userinfobot` and save it in the Web App.
    -   **Subscriptions:** Choose themes (e.g., Morning Briefing) and times.
    -   **Save.**
6.  **Done!** The backend will pick up your user profile on the next scheduled run (e.g., next hour) and send you messages if the time matches.

---

## 7. Troubleshooting & Maintenance

-   **Logs:** Check **Sentry** for errors or the **GitHub Actions** run history.
-   **Manual Run:** You can trigger a run manually via GitHub Actions "Run workflow" button to test if messages are delivered.
-   **Backups:** Use `tools.py` to backup your Firestore users regularly:
    ```bash
    python tools.py backup_firestore
    ```

--- END OF FILE Guide_to_Creating_and_Operating_Your_Own_Bot.md ---
