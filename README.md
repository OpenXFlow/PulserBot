# PulserBot: A Modular Content Delivery Bot for Telegram

<p align="center">
  <img src="docs/assets/PulserBotLogo.gif" alt="PulserBot Logo" width="300">
</p>

**PulserBot** is a open-source platform for creating personalized, multi-theme, and multi-language content bots. It is designed for maximum flexibility, scalability, and easy content management.

This repository serves as a template. You can use it to build your own bot that delivers curated daily content—from philosophical quotes and art history to language lessons and tech news etc. — directly to users on Telegram.

### Key Features:
-   **Modular OOP Architecture:** Built on a clean Strategy design pattern, making it easy to add new content types without modifying the core logic.
-   **Multi-Language Support:** Each user can choose their preferred language for the content they receive.
-   **Data-Driven Configuration:** Everything from schedules to users and content sources is managed in external files (`config.json`, Google Sheets), not in the code.
-   **Fully Automated:** Uses GitHub Actions for reliable, scheduled job execution, eliminating the need for a continuously running server.
-   **Monitoring:** Integrated with Sentry.io for real-time error, performance, and log tracking.
-   **Extensible:** Easily connect to any API (e.g., Unsplash, MET Museum, NewsAPI) or use Google Sheets as a database.
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
| **How to get API keys** | [→ Required Setup](https://openxflow.github.io/PulserBot/#setup-reqs) |
| **An explanation of `config.json`** | [→ Project Configuration](https://openxflow.github.io/PulserBot/#config-project) |
| **How to deploy the bot** | [→ Deployment Guide](https://openxflow.github.io/PulserBot/#deployment) |
| **The project's architecture** | [→ Architecture Overview](https://openxflow.github.io/PulserBot/#overview) |
| **Architecture Diagrams** | [→ Diagrams and Data Flow](docs/assets/bot_flow.md) |
| **How to for users** | [→ Create your own Bot](docs/how_to/Guide_to_Creating_and_Operating_Your_Own_Bot.md) |


## Contributing

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.```