--- START OF FILE 04_job_procesor_details.md ---

# Detailed Logic: Job Processor & Data Flow

This document details the internal logic of the `core.py` module, specifically the `JobOrchestrator` (formerly JobProcessor). It highlights the interactions with the new **Firestore Service** and the **Content Caching** mechanism.

---

## 1. Core Execution Sequence Diagram

This diagram shows exactly what happens when `run_once.py` calls `generate_and_send_async()`.

```mermaid
sequenceDiagram
    participant Runner as run_once.py
    participant Core as JobOrchestrator (core.py)
    participant Firestore as FirestoreService
    participant Handler as Content Handler
    participant TG as TelegramChannel

    Runner->>Core: execute_async(time_key)
    
    activate Core
    Core->>Core: Initialize Pipeline
    
    rect rgb(230, 240, 255)
        Note right of Core: Step 1: User Loading & Grouping
        Core->>Firestore: get_active_users(force_refresh=False)
        Firestore-->>Core: List[UserDict] (from DB or Snapshot)
        
        Core->>Core: Filter users by Local Time & Subscriptions
        Core->>Core: Group users by (Theme, Language)
    end

    loop For each Group (Theme T, Language L)
        Core->>Handler: Initialize Handler(T, L)
        
        rect rgb(255, 250, 230)
            Note right of Handler: Step 2: Content Generation & Caching
            
            alt Strategy == "per_user"
                 Core->>Core: (Skip shared cache, process individually)
            else Strategy == "once_per_group" (Default)
                Core->>Handler: execute()
                
                Handler->>Firestore: get_cached_content(date, theme_id)
                
                alt Cache Found
                    Firestore-->>Handler: Return Content
                else Cache Miss
                    Handler->>Handler: Generate (LLM / Sheets)
                    Handler->>Firestore: save_cached_content(date, theme_id, content)
                end
                
                Handler-->>Core: Final Content (Text, Image)
            end
        end
        
        rect rgb(230, 255, 230)
            Note right of Core: Step 3: Distribution
            loop For each User in Group
                Core->>Core: Personalize (e.g. Weather placeholders)
                Core->>TG: send_message / send_photo
                TG-->>Core: Success/Failure
            end
        end
    end
    
    Core-->>Runner: Job Finished
    deactivate Core
```

## 2. Key Logic Changes in v3.0

### A. User Loading (Hybrid Model)
Unlike v2.0, `core.py` no longer relies on `config.json` for user data.
-   It calls `firestore_service.get_active_users()`.
-   This service implements a **Daily Snapshot Strategy**: It downloads all users once per day and caches them in a special `system_cache` collection in Firestore to reduce read costs.

### B. Content Caching
To save money on LLM (Groq) and Image (Unsplash) APIs, the system now checks Firestore before generating content.
-   **Cache Key:** `YYYY-MM-DD_{theme_id}` (e.g., `2025-11-25_morning_briefing_sk`).
-   **Behavior:**
    1.  Handler checks if a document with this ID exists in the `daily_content_cache` collection.
    2.  **If yes:** Returns the stored text and image URL immediately.
    3.  **If no:** Calls LLM/Sheets/Unsplash, generates content, and **saves** it to Firestore for the next execution.

### C. Processing Strategy
Themes can now define a `processing_strategy` in `config.json`:
-   **`once_per_group` (Default):** Generates content ONCE (and caches it), then sends the same content to all subscribed users. Used for generic themes (Bible, Philosophy).
-   **`per_user`:** Generates unique content for EVERY user. Caching is usually disabled (`use_cache: false`). Used for `user_reminder` or highly personalized briefings.

--- END OF FILE 04_job_procesor_details.md ---