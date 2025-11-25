### 1. `01_run_once_flow.md`
*Zmeny: Aktualizovaný názov triedy na `JobOrchestrator`, pridané volanie `firestore_service` na získanie používateľov a ukážka, ako sa pre tému 'german_lesson' (ktorá je dynamická) preskočí globálna cache, ak je tak nastavená, alebo sa použije.*

--- START OF FILE 01_run_once_flow.md ---

### Sequence Diagram: Complete Flow of the `run_once.py` Command

This diagram illustrates in detail the calls between the main python classes during a manual CLI execution (e.g., `python run_once.py time3 users Jozef_D`).

It uses the **`german_lesson`** theme as an example to demonstrate the interaction between the Orchestrator, Firestore, and the Template Handler.

```mermaid
sequenceDiagram
    participant CLI as User (Terminal)
    participant Runner as run_once.py
    participant Core as core.py
    participant Orchestrator as JobOrchestrator
    participant Firestore as FirestoreService
    participant Handler as DynamicTemplateHandler
    participant Sheets as SheetsService
    participant Telegram as TelegramChannel

    CLI->>Runner: `python run_once.py time3 users Jozef_D`
    
    activate Runner
    Runner->>Core: generate_and_send_async('time3', ...)
    
    activate Core
    Core->>Orchestrator: __init__ (Load config.json, Initialize)
    Core->>Orchestrator: execute_async()
    
    activate Orchestrator
    Note right of Orchestrator: Pipeline Step 1: Initialization
    Orchestrator->>Sheets: initialize_sheets_service(app_config)
    
    Note right of Orchestrator: Pipeline Step 2: Get Users
    Orchestrator->>Firestore: get_active_users()
    Firestore-->>Orchestrator: Returns List[UserDict] (from Cloud DB)
    
    Orchestrator->>Orchestrator: _prepare_content_groups()
    Note right of Orchestrator: Filters users by time/name.<br>Returns group: ('german_lesson', 'slovak')

    Note right of Orchestrator: Pipeline Step 3: Process Groups
    loop For each group
        Orchestrator->>Handler: Instantiate DynamicTemplateHandler
        Orchestrator->>Handler: execute(user, force_update)
        
        activate Handler
        Note over Handler: BaseHandler Logic (Caching)
        Handler->>Firestore: get_cached_content(date, 'german_lesson')
        
        alt Cache Miss (Data not generated yet)
            Handler->>Handler: _process()
            
            Note over Handler, Sheets: Handler fetches raw data from Google Sheets
            Handler->>Sheets: get_worksheet(rotation)
            Sheets-->>Handler: Worksheet Object
            Handler->>Sheets: get_unused_item(worksheet)
            Sheets-->>Handler: Row Data (e.g. "Verbs")
            
            Handler->>Handler: Format Text & Select Image
            
            Handler->>Firestore: save_cached_content(...)
            Note right of Handler: Content saved for other users today
        else Cache Hit
             Firestore-->>Handler: Returns {text, image_url}
        end
        
        Handler-->>Orchestrator: Returns (Final Text, Image URL)
        deactivate Handler
        
        Orchestrator->>Orchestrator: _distribute_content_async(...)
        Orchestrator->>Telegram: send_photo(chat_id, url, text)
        Telegram-->>Orchestrator: Success
    end

    Orchestrator-->>Core: Job Finished
    deactivate Orchestrator
    
    Core-->>Runner: Async task complete
    deactivate Core
    
    Runner->>CLI: Exit
```
--- END OF FILE 01_run_once_flow.md ---

