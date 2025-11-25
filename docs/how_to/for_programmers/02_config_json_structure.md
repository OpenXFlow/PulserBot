--- START OF FILE 02_config_json_structure.md ---

# Structure and Guide for `config.json` (v3.0 Hybrid)

In the Hybrid Architecture, `config.json` defines the **System Configuration** (static behavior, available themes, data sources), while **User Configuration** (subscriptions, preferences) lives dynamically in the Cloud Firestore database.

---

## I. Root Structure

The main file has four primary sections:

-   `"schedule"`: Defines the global trigger times for the backend.
-   `"users"`: **DEPRECATED/EMPTY.** User data is now fetched from Firestore.
-   `"themes"`: A catalog of all available themes and their technical definitions.
-   `"data_sources"`: A map of all physical data sources (Google Sheets).

---

## II. The `"schedule"` Section

Defines logical "time slots" when the bot should wake up and check users.

-   **Key** (e.g., `"time07"`): A unique identifier for the time slot. Matches the keys stored in the user's `subscriptions` map in Firestore.
-   **Value** (e.g., `"07:00"`): The global trigger time.

**Example:**
```json
"schedule": {
  "time06": "06:00",
  "time07": "07:00",
  "time08": "08:00"
}
```

---

## III. The `"users"` Section

In version 3.0+, this section is usually empty: `"users": []`.
The bot loads user profiles directly from the `users` collection in Firestore via `src/services/firestore_service.py`.

### **Firestore User Document Structure**
For reference, each document in the Firestore `users` collection has this structure:

```json
{
  "email": "user@example.com",
  "active": true,
  "language": "slovak",
  "timezone": "Europe/Bratislava",
  "channels": [
    { "platform": "telegram", "identifier": "123456789" }
  ],
  "subscriptions": {
    "time07": [
      { "theme": "morning_briefing_sk", "days": [0, 1, 2, 3, 4, 5, 6] }
    ],
    "time08": [
       { "theme": "bible_sk", "days": [0, 6] }
    ]
  },
  "weather": {
    "locations": [{ "location": "Bratislava,SK" }]
  },
  "custom_content": {
      "blocks": ["Goal 1", "Goal 2"],
      "links": [{ "title": "Menu", "url": "..." }]
  }
}
```

---

## IV. The `"themes"` Section

A catalog of all available themes. Each theme is an object whose behavior is defined by the `"handler_class"` key.

### New Feature: Caching Control
In v3.0, themes can explicitly disable caching. This is essential for user-defined content (like reminders) which changes frequently and is unique per user.

| Key | Type | Description |
| :--- | :--- | :--- |
| `use_cache` | boolean | (Optional) Default `true`. If `false`, content is regenerated on every run. |
| `processing_strategy` | string | (Optional) `"once_per_group"` (default) or `"per_user"` (for personalized content). |

**Example - User Reminder (No Cache, Per User):**
```json
"user_reminder": {
  "handler_class": "UserDefinedHandler",
  "processing_strategy": "per_user",
  "use_cache": false,
  "dynamic_image": { "provider": "unsplash", "query": "coffee,planning" },
  "prompts": {} 
}
```

**Example - Standard Theme (Cached):**
```json
"bible_sk": {
  "handler_class": "BibleHandler",
  "data_source": { "spreadsheet_key": "YDP_LLM_Static_Spiritual", "worksheet_key": "bible_sk" },
  "dynamic_image": { "provider": "unsplash", "query": "nature,light" },
  "prompts": { "slovak": "src/resources/llm/slovak/prompt_bible.txt" }
}
```

---

## V. The `"data_sources"` Section

Defines the physical location of Google Sheets. (Unchanged from previous versions).

**Example:**
```json
"data_sources": {
  "YDP_LLM_Static_Spiritual": {
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
    "worksheets": {
      "bible_sk": "BibleSk",
      "bible_en": "BibleEng"
    }
  }
}
```

--- END OF FILE 02_config_json_structure.md ---
