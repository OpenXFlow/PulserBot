## 1. Component Architecture Diagram

This diagram shows the main **static building blocks** of the system and their dependencies.

```mermaid
sequenceDiagram
    participant CLI
    participant run_once.py
    participant JobProcessor
    participant SheetsService
    participant DynamicTemplateHandler
    participant TelegramChannel

    CLI->>run_once.py: python run_once.py time3 users Jozef_D
    run_once.py->>JobProcessor: Creates instance: JobProcessor('time3', ['Jozef_D'])
    run_once.py->>JobProcessor: Calls processor.execute()
    JobProcessor->>SheetsService: initialize_sheets_service(app_config)
    Note over JobProcessor,SheetsService: Prepares SheetsService for work.
    JobProcessor->>JobProcessor: _prepare_content_groups()
    Note right of JobProcessor: Loads config.json, filters and groups<br/>requests. Returns group ('german_lesson', 'slovak').
    
    loop For each group
        JobProcessor->>JobProcessor: _process_group('german_lesson', 'slovak', theme_config)
        Note right of JobProcessor: Loads 'handler_class': "DynamicTemplateHandler" from config.
        
        JobProcessor->>DynamicTemplateHandler: Creates instance: DynamicTemplateHandler(theme_config, 'slovak')
        JobProcessor->>DynamicTemplateHandler: Calls handler.execute()
        
        DynamicTemplateHandler->>DynamicTemplateHandler: _process()
        
        DynamicTemplateHandler->>SheetsService: get_worksheet(rotation_ref)
        SheetsService-->>DynamicTemplateHandler: Returns rot_ws
        
        DynamicTemplateHandler->>SheetsService: get_unused_item(rot_ws)
        SheetsService-->>DynamicTemplateHandler: Returns (rot_idx, rot_data) with content_key
        
        DynamicTemplateHandler->>DynamicTemplateHandler: _get_template_path(content_key)
        
        DynamicTemplateHandler->>SheetsService: get_worksheet(lesson_ref)
        SheetsService-->>DynamicTemplateHandler: Returns lesson_ws
        
        DynamicTemplateHandler->>SheetsService: get_unused_item(lesson_ws)
        SheetsService-->>DynamicTemplateHandler: Returns (lesson_idx, lesson_data)
        
        DynamicTemplateHandler->>SheetsService: get_worksheet(slowgerman_ref)
        SheetsService-->>DynamicTemplateHandler: Returns sg_ws
        
        DynamicTemplateHandler->>SheetsService: get_unused_item(sg_ws)
        SheetsService-->>DynamicTemplateHandler: Returns (sg_idx, sg_data)
        
        Note right of DynamicTemplateHandler: Assembles the final text and gets the image URL.
        
        DynamicTemplateHandler-->>JobProcessor: Returns (final_text, image_url)
        
        JobProcessor->>JobProcessor: _distribute_content(...)
        JobProcessor->>TelegramChannel: send_photo(chat_id, url, text)
        
        TelegramChannel->>TelegramChannel: _sanitize_html(text)
        
        TelegramChannel-->>JobProcessor: Returns True/False
    end
    
    JobProcessor->>run_once.py: Finishes execute()
    run_once.py->>CLI: Prints final logs and exits.
