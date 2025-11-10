# PulserBot: A Modular Content Delivery Bot for Telegram

<p align="center">
  <a href="https://openxflow.github.io/PulserBot/">
    <img src="docs/assets/PulserBotLogo.gif" alt="PulserBot Logo" width="300">
  </a>
</p>


<p align="left">
  <strong>Build your own Telegram bot to deliver personalized, multi-theme, and multi-language content on a schedule.</strong>
  <br>
  PulserBot is a flexible, open-source platform designed for easy content management and powerful automation.
  <br>
  PulserBot is Your Personal Content Delivery Engine.
</p>

This repository is a ready-to-use template. Clone it to create a bot that delivers anything you can imagine—from daily philosophical quotes and art history to language lessons and tech news—directly to your friends, family, or community on Telegram. You control the content, the schedule, and the audience.

### Key Features

-   ✨ **Highly Customizable:** Define your own content themes, from LLM-powered spiritual reflections to data-driven language lessons.
-   ✨ **Modular Architecture:** Built on a clean Handler (Strategy) pattern, allowing you to add new content types without touching the core logic.
-   ✨ **Multi-Language Support:** Deliver content in each user's preferred language.
-   ✨ **Data-Driven:** Manage everything—schedules, users, themes, and content—in external `config.json` and Google Sheets, not hard-coded.
-   ✨ **Serverless Automation:** Runs entirely on **GitHub Actions** for reliable, scheduled execution. No server costs, no maintenance.
-   ✨ **Real-Time Monitoring:** Integrated with **Sentry.io** out-of-the-box for powerful error tracking, performance monitoring, and logging.
-   ✨ **Extensible by Design:** Easily connect to any API (e.g., Unsplash for images, NewsAPI for articles) or use Google Sheets as a simple, effective database.


### PulserBot delivery :
-   **A moment for yourself, every day.**  PulserBot delivers a daily, thought-provoking message combining art, philosophy, and knowledge to inspire a mindful pause in your routine.
- The content of the message is automated but is fully under your control.
- You can share it with your family and friends, but only you decide what content, when and to whom you send it ...
  
<p align="center">
  <img src="docs/assets/promts.gif" alt="Pulser" width="300">
</p>

### Quick Start for Developers

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/OpenXFlow/PulserBot.git
    cd PulserBot
    ```
2.  **Set up the Environment:**
    *   Create a virtual environment: `python -m venv .venv`
    *   Activate it: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
    *   Install dependencies: `pip install -r requirements.txt`

3.  **Configure the Bot:**
    *   **API Keys:** Rename `.env.example` to `.env` and fill in all your API keys (Telegram, Groq, Sentry, etc.).
    *   **Google Sheets Data:** Create a Google Sheet document and populate it with your content. You will need worksheets for your themes (e.g., `BibleEN`, `PhilosophyEN`) and a `Jobs` sheet for the scheduler. See the full documentation for details and docs\Google_sheets_exemples\
    *   **Main Config:** Rename `config.json.example` to `config.json`. Customize it with your users, and update the `spreadsheet_url` for all themes and data sources to point to your new Google Sheet.
    *   **Google Credentials:** Create a `credentials.json` file for Google API access and place it in the root directory.

4.  **Run a Test Job:**
    *   Execute a job for a specific time key defined in your `config.json`:
        ```bash
        python run_once.py time1
        ```


## Full Documentation

All detailed technical information, step-by-step setup guides, and architectural explanations are available at our **[Main Documentation Portal](https://openxflow.github.io/PulserBot/)**.

| I'm looking for... | Link to Documentation |
| :--- | :--- |
| **A detailed setup guide** | [→ Local Environment Setup](https://openxflow.github.io/PulserBot/#local-setup) |
| **Architecture Diagrams** | [→ Diagrams and Data Flow](docs/assets/bot_flow.md) |
| **How to for users** | [→ Create your own Bot, promt types ](docs/how_to/for_users/) |
| **How to for dev** | [→ Flows, Congig, etc.](docs/how_to/for_programmers/) |


## Contributing

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.```