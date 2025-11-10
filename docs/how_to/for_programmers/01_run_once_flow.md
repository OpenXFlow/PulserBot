### Sequence Diagram: Complete Flow of the `run_once.py time3 users Jozef_D` Command

This diagram illustrates in detail the calls between the main files and classes, using the `german_lesson` theme as an example to demonstrate the most interesting logic.

```mermaid
sequenceDiagram
    participant CLI as User (Terminal)
    participant run_once.py
    participant core.py
    participant JobProcessor
    participant config.py
    participant SheetsService
    participant DynamicTemplateHandler
    participant TelegramChannel

    CLI->>run_once.py: `python run_once.py time3 users Jozef_D`
    
    activate run_once.py
    run_once.py->>run_once.py: main()
    Note right of run_once.py: Loads arguments from `sys.argv`
    run_once.py->>core.py: generate_and_send('time3', ['Jozef_D'])
    
    activate core.py
    core.py->>JobProcessor: Creates an instance: processor = JobProcessor(...)
    
    activate JobProcessor
    JobProcessor->>config.py: load_app_config()
    
    activate config.py
    config.py->>config.py: Opens and loads 'config.json'
    config.py-->>JobProcessor: Returns (app_config, tz)
    deactivate config.py
    
    JobProcessor-->>core.py: `processor` instance is created
    
    core.py->>JobProcessor: processor.execute()
    
    JobProcessor->>SheetsService: initialize_sheets_service(self.app_config)
    
    JobProcessor->>JobProcessor: _prepare_content_groups()
    Note right of JobProcessor: Loads `users` and `subscriptions` from `self.app_config`,<br>returns the group ('german_lesson', 'slovak').

    loop For each group
        JobProcessor->>JobProcessor: _process_group('german_lesson', 'slovak', theme_config)
        Note right of JobProcessor: Loads `handler_class` from `theme_config`:<br>"DynamicTemplateHandler"
        
        JobProcessor->>DynamicTemplateHandler: Creates a handler instance
        JobProcessor->>DynamicTemplateHandler: Calls handler.execute()
        
        activate DynamicTemplateHandler
        DynamicTemplateHandler->>DynamicTemplateHandler: _process()
        
        Note over DynamicTemplateHandler, SheetsService: Inside _process(), multiple calls<br>are made to SheetsService:<br>1. get_worksheet(rotation_ref)<br>2. get_unused_item(rot_ws)<br>3. get_worksheet(lesson_ref)<br>4. get_unused_item(lesson_ws)<br>5. get_worksheet(sg_ref)<br>6. get_unused_item(sg_ws)
        
        DynamicTemplateHandler-->>JobProcessor: Returns (final_text, image_url)
        deactivate DynamicTemplateHandler
        
        JobProcessor->>JobProcessor: _distribute_content(...)
        JobProcessor->>TelegramChannel: send_photo(chat_id, url, text)
        
        activate TelegramChannel
        TelegramChannel->>TelegramChannel: _sanitize_html(text)
        Note right of TelegramChannel: Sends a request to the Telegram API
        TelegramChannel-->>JobProcessor: Returns True/False
        deactivate TelegramChannel
    end

    JobProcessor-->>core.py: Finishes execute()
    deactivate JobProcessor
    
    core.py-->>run_once.py: Finishes generate_and_send()
    deactivate core.py
    
    run_once.py->>CLI: Prints final logs and exits
```