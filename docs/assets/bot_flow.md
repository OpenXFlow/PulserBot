# Architecture and Data Flow: ChronicleBot

This document describes the architecture and detailed data flow of the ChronicleBot application. The goal is to visualize how individual components and external services interact and how the application is deployed.

## Key System Components

-   **GitHub:** Source code repository and the trigger for the automated deployment and execution process.
-   **GitHub Actions:** The core automation engine that runs scheduled jobs.
-   **Application (Python Scripts):** The main Python application, which acts as an orchestrator and set of tools.
-   **Sentry.io:** An external monitoring service that collects errors, logs, and performance metrics in real-time.
-   **Google Sheets API:** An external service used as a persistent content database.
-   **LLM API (e.g., Groq):** An external LLM service that generates creative text.
-   **Telegram API:** The external service through which content is delivered to users.
-   **Image APIs (e.g., Unsplash, Cloudinary):** External services for fetching or hosting images.

---

## 1. Component Architecture Diagram

This diagram shows the main **static building blocks** of the system and their dependencies.

```mermaid
graph TD
    subgraph "Application"
        App["Python Application"]
    end

    subgraph "Local Configuration"
        direction LR
        Config["config.json"]
        Prompts["Prompt Files"]
    end

    subgraph "External Services (APIs)"
        direction LR
        GSheets["Google Sheets API"]
        LLM["LLM API (Groq)"]
        Telegram["Telegram API"]
        Sentry["Sentry API"]
        Images["Image APIs"]
    end

    App -- "Reads" --> Config
    App -- "Reads" --> Prompts
    App -- "Reads/Writes" --> GSheets
    App -- "Generates text via" --> LLM
    App -- "Sends messages via" --> Telegram
    App -- "Sends logs & errors to" --> Sentry
    App -- "Fetches images from" --> Images
```

---

## 2. Deployment Diagram

This diagram visualizes **where each software component is deployed** and how they communicate within the real-world infrastructure.

```mermaid
graph TD
    subgraph "User"
        UserDevice["User's Device (Mobile/PC)"]
        UserDevice -- "interacts with" --> TelegramApp[Telegram App]
    end

    subgraph "Cloud Infrastructure"
        GitHub["GitHub"]
        ExternalServices["External Services"]
    end
    
    subgraph GitHub
        direction LR
        Repo["Git Repository"]
        Actions["GitHub Actions (Runner)"]
    end

    subgraph Actions
        Trigger["trigger_jobs.py (Dispatcher)"]
        RunOnce["run_once.py (Worker)"]
    end
    
    subgraph ExternalServices
        LLM_API["LLM API (Groq)"]
        GSheets_API["Google Sheets API"]
        Telegram_API["Telegram API"]
        Sentry_API["Sentry API"]
        Image_APIs["Image APIs"]
    end

    Repo -- "contains code for" --> Trigger
    Repo -- "contains code for" --> RunOnce
    Trigger -- "runs" --> RunOnce
    
    TelegramApp <--> Telegram_API
    RunOnce -- "calls" --> LLM_API
    RunOnce -- "reads/writes to" --> GSheets_API
    RunOnce -- "sends via" --> Telegram_API
    RunOnce -- "reports to" --> Sentry_API
    RunOnce -- "fetches from" --> Image_APIs
    Trigger -- "reads/writes to" --> GSheets_API
    Trigger -- "reports to" --> Sentry_API
```

---

## 3. CI/CD Process Diagram (Continuous Integration / Continuous Deployment)

This diagram describes how code changes are automatically deployed and run.

```mermaid
graph LR
    subgraph "Developer (Your PC)"
        A["Code Changes"]
    end

    subgraph "Version Control & Automation"
        B["GitHub Repository"]
        C["GitHub Actions"]
    end

    A -- "1. git push" --> B
    B -- "2. Triggers Workflow on push/schedule" --> C
    C -- "3. Checks out the latest code" --> B
    C -- "4. Installs dependencies" --> C
    C -- "5. Runs the dispatcher script (trigger_jobs.py)" --> C
```

---

## 4. Sequence Diagram: Full Flow from Scheduler to User

This diagram shows the complete **communication over time** between all components of the live application.

```mermaid
sequenceDiagram
    participant GitHub Actions
    participant Dispatcher (trigger_jobs.py)
    participant Worker (run_once.py)
    participant Sentry API
    participant Google Sheets API
    participant Telegram API

    GitHub Actions->>Dispatcher: Starts script on schedule (e.g., every 30 min)
    Dispatcher->>Sentry API: Initialize Sentry SDK
    Dispatcher->>Google Sheets API: Check 'Jobs' sheet for lock key
    Google Sheets API->>Dispatcher: Return status (not found)
    
    Dispatcher->>Google Sheets API: Write new lock key to 'Jobs' sheet
    Dispatcher->>Worker: subprocess.run('python run_once.py timeX')
    
    Worker->>Sentry API: Initialize Sentry SDK
    Worker->>Worker: Prepare content groups
    
    loop For each content group
        Worker->>Worker: _process_group (call strategy)
        Note over Worker: Strategy fetches content (Sheets, APIs) & generates text (LLM)
        Worker->>Telegram API: Send Photo/Message
    end
    
    Worker->>Sentry API: Flush remaining events
    Dispatcher->>Dispatcher: Script finishes
```

---

## 5. Internal Flow Diagram of `JobProcessor`

This diagram illustrates the **logical steps and decisions** within the main `JobProcessor` class, showcasing the Strategy Pattern.

```mermaid
graph TD
    A["Start Job for 'time_key'"] --> B["_prepare_content_groups()"];
    
    subgraph "Parallel Monitoring"
        Sentry["All steps & errors are logged to Sentry"]
    end

    A -- Log --> Sentry

    B --> C{"Are there any subscribed users?"};
    C -- No --> End["End Job"];
    C -- Yes --> D["Group users by (theme, language)"];
    
    D --> E{"Loop: For each group"};
    E -- All groups processed --> End;
    
    E --> F["Get theme_config from config.json"];
    F --> G["_process_group(theme, lang, config)"];
    
    subgraph G
        direction LR
        G1["Get 'type' from config"] --> G2["Dynamically import strategy<br>from 'src/prompt_type/'"];
        G2 --> G3["Call strategy.process()"];
        G3 --> G4["Return (text, image_url)"];
    end

    G --> H{"Content generated?"};
    H -- No --> E;
    H -- Yes --> I["_distribute_content()"];
    I --> J{"Loop: For each user in group"};
    J --> K["Send message via Telegram API"];
    K --> J;
    J -- All users processed --> E;

