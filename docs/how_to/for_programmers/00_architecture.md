--- START OF FILE 00_architecture.md ---

# Architecture and Data Flow: YourDailyPulse (Hybrid Firebase Edition)

This document describes the architecture of the YourDailyPulse application in its version 3.x. This version introduces a **Hybrid Architecture** that decouples the user interface (Frontend) from the processing logic (Backend) using cloud infrastructure.

## Key System Components

-   **Frontend (Web App):** A static HTML/JS application hosted on **GitHub Pages**. It serves as the control panel where users register, log in, and configure their subscriptions.
-   **Cloud Infrastructure (Firebase):**
    -   **Authentication:** Handles user sign-up, login, and email verification securely.
    -   **Firestore Database:** The central source of truth. It stores user profiles, subscriptions, settings, and the daily content cache.
-   **Backend (Python Core):** The logic engine responsible for generating and delivering content. It supports two runtime modes:
    -   **Serverless (GitHub Actions):** Runs periodically via `run_once.py` (triggered by CRON) to minimize costs.
    -   **Service (Render):** Runs continuously via `main.py` with an internal scheduler.
-   **External APIs:** Telegram (delivery), Groq (LLM generation), Google Sheets (static content source), Unsplash (images).

---

## 1. High-Level Component Architecture

This diagram illustrates how the Frontend and Backend are decoupled and communicate solely through the Cloud Database.

```mermaid
graph TD
    subgraph "Frontend (User Control)"
        WebApp["Web Application<br>(HTML/JS on GitHub Pages)"]
        AuthConfig["firebase-config.js"]
    end

    subgraph "Cloud Infrastructure"
        Auth["Firebase Authentication"]
        DB[("Firestore Database<br>(Users + Cache)")]
    end

    subgraph "Backend (Content Worker)"
        Orchestrator["Job Orchestrator<br>(core.py)"]
        Handlers["Content Handlers<br>(src/handlers/)"]
        Config["System Config<br>(config.json)"]
    end

    subgraph "External Services"
        direction LR
        Telegram["Telegram API"]
        LLM["LLM API (Groq)"]
        Sheets["Google Sheets"]
        Images["Image APIs"]
    end

    %% Flows
    WebApp -- "Authenticates via" --> Auth
    WebApp -- "Reads/Writes User Settings" --> DB
    
    Orchestrator -- "Reads System Settings" --> Config
    Orchestrator -- "Fetches Active Users" --> DB
    Orchestrator -- "Checks/Saves Content Cache" --> DB
    
    Orchestrator -- "Dispatches to" --> Handlers
    Handlers -- "Fetches Raw Content" --> Sheets
    Handlers -- "Generates Text" --> LLM
    Handlers -- "Fetches Images" --> Images
    
    Orchestrator -- "Delivers Message" --> Telegram
```

---

## 2. Execution Flow: Backend (Serverless / GitHub Actions)

This is the standard execution mode triggered by a CRON schedule (e.g., every hour).

```mermaid
sequenceDiagram
    participant GA as GitHub Actions
    participant Trigger as Trigger Script (trigger_jobs.py)
    participant Core as Core Logic (run_once.py)
    participant DB as Firestore
    participant Handler as Content Handler
    participant TG as Telegram
    
    Note over GA: Scheduled Trigger (e.g. every 60 mins)
    GA->>Trigger: Execute trigger_jobs.py
    Trigger->>Trigger: Load config.json
    Trigger->>Trigger: Check Current Time vs Schedule
    
    opt Schedule Match (e.g., "time07" at 07:00)
        Trigger->>Core: Subprocess: "python run_once.py time07"
        
        rect rgb(240, 248, 255)
            note right of Core: Initialization
            Core->>DB: Fetch Active Users (Snapshot)
            DB-->>Core: User List (Timezones, Subs)
        end
        
        loop For Each User
            Core->>Core: Calculate User's LOCAL Time
            
            opt Local Time == Trigger Time
                note right of Core: Processing
                Core->>Handler: Execute Handler (e.g. Morning Briefing)
                
                alt Cache Enabled?
                    Handler->>DB: Get Cached Content?
                end
                
                alt Cache Hit
                    DB-->>Handler: Return Cached Text/Image
                else Cache Miss
                    Handler->>Handler: Call LLM / Sheets / Images
                    Handler->>DB: Save to Cache
                end
                
                Handler-->>Core: Final Content
                Core->>TG: Send Message (Text/Photo)
            end
        end
        Core-->>Trigger: Job Complete
    end
    Trigger-->>GA: Exit
```

---

## 3. Execution Flow: Backend (Service / Render)

This mode uses `main.py` as a persistent service.

```mermaid
sequenceDiagram
    participant Render as Render.com
    participant Main as main.py
    participant Scheduler as APScheduler
    participant Web as Flask Server
    participant Core as Core Logic
    
    Render->>Main: Start Application
    Main->>Web: Start Background Thread (Port 10000)
    Note right of Web: Responds "OK" to Ping
    
    Main->>Scheduler: Start BlockingScheduler
    Note right of Scheduler: Configured to tick at minute 0
    
    loop Every Hour (XX:00)
        Scheduler->>Core: Job: hourly_service_tick
        Core->>Core: (Same logic as run_once)
        Core->>Firestore: Fetch Users
        Core->>Telegram: Send Messages
    end
```
--- END OF FILE 00_architecture.md ---
