# Architecture and Data Flow: YourDailyPulse

This document describes the architecture and detailed data flow of the YourDailyPulse application. The goal is to visualize how individual components and external services work together and how the application is deployed.

## Key System Components

-   **GitHub:** Source code repository and the trigger for the automated deployment and execution process.
-   **GitHub Actions:** The primary automation tool that runs scheduled tasks.
-   **Application (Python Scripts):** The main Python application, which acts as an orchestrator and a set of tools.
-   **Sentry.io:** An external monitoring service that collects errors, logs, and performance metrics in real time.
-   **Google Sheets API:** An external service used as a persistent database for content.
-   **LLM API (e.g., Groq):** An external LLM service that generates creative text for specific topics.
-   **Telegram API:** An external service through which content is delivered to users.
-   **Image APIs (e.g., Unsplash, Cloudinary):** External services for retrieving or hosting images.

---

## 1. Component Architecture Diagram

This diagram shows the main **static building blocks** of the system and their dependencies.

```mermaid
graph TD
    subgraph "Application (src/)"
        A[Python Application]
        A -- "Uses logic from" --> Handlers["Handlers (src/handlers/)"]
        A -- "Reads" --> Resources["Resources (src/resources/)"]
    end

    subgraph "Main Configuration"
        Config["config.json"]
    end

    subgraph "External Services (API)"
        direction LR
        GSheets["Google Sheets API"]
        LLM["LLM API (Groq)"]
        Telegram["Telegram API"]
        Sentry["Sentry API"]
        Images["Image APIs"]
    end

    A -- "Reads" --> Config
    Handlers -- "Read" --> Resources
    Handlers -- "Read/Write" --> GSheets
    Handlers -- "Call" --> LLM
    A -- "Sends messages via" --> Telegram
    A -- "Sends logs and errors to" --> Sentry
    Handlers -- "Retrieve images from" --> Images
```

---

## 2. Deployment Diagram

This diagram visualizes **where each software component is deployed** and how they communicate within the real infrastructure.

```mermaid
graph TD
    subgraph "User"
        UserDevice["User's Device (Mobile/PC)"]
        UserDevice -- "interacts with" --> TelegramApp[Telegram Application]
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
    RunOnce -- "retrieves from" --> Image_APIs
    Trigger -- "reads/writes to" --> GSheets_API
    Trigger -- "reports to" --> Sentry_API
```

---

## 3. CI/CD Process Diagram (Continuous Integration / Continuous Deployment)

This diagram describes how code changes are automatically deployed and executed.

```mermaid
graph LR
    subgraph "Developer (Your PC)"
        A["Code Changes"]
    end

    subgraph "Versioning and Automation"
        B["GitHub Repository"]
        C["GitHub Actions"]
    end

    A -- "1. git push" --> B
    B -- "2. Triggers Workflow (on push/schedule)" --> C
    C -- "3. Fetches latest code" --> B
    C -- "4. Installs dependencies" --> C
    C -- "5. Runs dispatcher script (trigger_jobs.py)" --> C
```

---

## 4. Sequence Diagram: Complete Flow from Scheduler to User

This diagram shows the complete **communication over time** between all components of the live application.

```mermaid
sequenceDiagram
    participant GitHub Actions
    participant Dispatcher (trigger_jobs.py)
    participant Worker (run_once.py)
    participant Sentry API
    participant Google Sheets API
    participant Telegram API

    GitHub Actions->>Dispatcher: Runs script on schedule (e.g., every hour)
    Dispatcher->>Sentry API: Initialize Sentry SDK
    Dispatcher->>Google Sheets API: Check for a lock in the 'Jobs' sheet
    Google Sheets API->>Dispatcher: Return status (not found)
    
    Dispatcher->>Google Sheets API: Write a new lock to the 'Jobs' sheet
    Dispatcher->>Worker: subprocess.run('python run_once.py timeX')
    
    Worker->>Sentry API: Initialize Sentry SDK
    Worker->>Worker: Prepare content groups
    
    loop For each group (theme, language)
        Worker->>Worker: _process_group (creates and runs a Handler)
        Note over Worker: Handler loads content (Sheets, API) and composes the text
        Worker->>Telegram API: Send photo/message
    end
    
    Worker->>Sentry API: Flush remaining events
    Dispatcher->>Dispatcher: Script ends
```

---

## 5. Internal Flow Diagram of `JobProcessor` (Handler Pattern)

This diagram illustrates the **logical steps and decisions** within the main `JobProcessor` class, highlighting the use of the new "Handler" design pattern.

```mermaid
graph TD
    A["Start job for 'time_key'"] --> B["_prepare_content_groups()"];
    
    subgraph "Parallel Monitoring"
        Sentry["All steps and errors are logged to Sentry"]
    end

    A -- Log --> Sentry

    B --> C{"Are there any subscribed users?"};
    C -- No --> End["End job"];
    C -- Yes --> D["Group users by (theme, language)"];
    
    D --> E{"Loop: For each group"};
    E -- All groups processed --> End;
    
    E --> F["Get theme_config from config.json"];
    F --> G["_process_group(theme, language, config)"];
    
    subgraph G [Processing via Handler]
        direction LR
        G1["Get 'handler_class' from config"] --> G2["Dynamically import and<br>create Handler instance<br>(e.g., BibleHandler)"];
        G2 --> G3["Call handler.execute()"];
        G3 --> G4["Return (text, image_url)"];
    end

    G --> H{"Content generated?"};
    H -- No --> E;
    H -- Yes --> I["_distribute_content()"];
    I --> J{"Loop: For each user in the group"};
    J --> K["Send message via Telegram API"];
    K --> J;
    J -- All users served --> E;
```