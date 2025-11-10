# Structure and Guide for `config.json`

This document provides a detailed description of all sections, keys, and values within the `config.json` configuration file. It serves as the main reference guide for managing and extending the functionality of the YourDailyPulse application.

---

## I. Root Structure

The main file has four primary sections:

-   `"schedule"`: Defines the times at which tasks should be executed.
-   `"users"`: A list of all users and their subscriptions.
-   `"themes"`: A catalog of all available themes and their technical definitions.
-   `"data_sources"`: A map of all physical data sources (Google Sheets).

---

## II. The `"schedule"` Section

Defines logical "time slots" and maps them to a specific time in `HH:MM` format.

-   **Key** (e.g., `"time1"`): A unique identifier for the time slot. It is used in the `"users"` section to assign subscriptions.
-   **Value** (e.g., `"06:00"`): The time at which tasks for that slot should run (in the timezone defined in the `.env` file).

**Example:**
```json
"schedule": {
  "time1": "06:00",
  "time2": "10:00",
  "time3": "14:00"
}
```

---

## III. The `"users"` Section

Contains an array of all user objects.

-   **`description`** (string): A human-readable name for the user (for logging and testing).
-   **`active`** (boolean): `true` if the account should be active. `false` temporarily deactivates the sending of all messages for that user.
-   **`language`** (string): The user's default language (e.g., `"slovak"`, `"english"`).
-   **`channels`** (array): A list of platforms where messages should be sent.
    -   `platform` (string): The name of the platform (currently only `"telegram"`).
    -   `identifier` (string): The unique `chat_id` for that user on the platform.
-   **`subscriptions`** (object): Maps time slots (from `schedule`) to a list of themes (from `themes`) that the user has subscribed to for that time.

**Example:**
```json
"users": [
  {
    "description": "Jozef_D",
    "active": true,
    "language": "slovak",
    "channels": [{ "platform": "telegram", "identifier": "1572391064" }],
    "subscriptions": {
      "time1": ["morning_briefing_sk", "bible_sk"],
      "time2": ["german_lesson"]
    }
  }
]
```

---

## IV. The `"themes"` Section

A catalog of all available themes. Each theme is an object whose behavior is defined by the `"handler_class"` key.

### A. Overview of Handlers and their Configurations

| `handler_class` | Description and Use Case | Required Keys | Optional Keys |
| :--- | :--- | :--- | :--- |
| **`BibleHandler`** | Spiritual reflections (LLM). | `data_source`, `prompts` | `dynamic_image` |
| **`BibleStudyHandler`**| Contextual Bible study (LLM).| `data_source`, `prompts` | `testament_name`, `dynamic_image`|
| **`PhilosophyHandler`**| Philosophical reflections (LLM). | `data_source`, `prompts` | `dynamic_image` |
| **`LLMDynamicHandler`**| Complex topics from multiple sources (LLM). | `content_rotation_source`, `prompts` | `components`, `dynamic_image` |
| **`SimpleStaticHandler`**| Displays data from a sheet using a template (no LLM). | `data_source`, `prompts` | `static_image_url` |
| **`DynamicTemplateHandler`**| Displays data with dynamic template selection (no LLM). | `content_rotation_source`, `prompts` | `static_image_url`, `static_image_*_url` |

### B. Examples of Theme Definitions

#### `handler_class: "BibleHandler"`
```json
"bible_sk": {
  "handler_class": "BibleHandler",
  "data_source": { "spreadsheet_key": "YDP_LLM_Static_Spiritual", "worksheet_key": "bible_sk" },
  "dynamic_image": { "provider": "unsplash", "query": "nature,light,hope" },
  "prompts": { "slovak": "src/resources/llm/prompt_bible_slovak.txt" }
}
```

#### `handler_class: "SimpleStaticHandler"`
```json
"european_art": {
  "handler_class": "SimpleStaticHandler",
  "data_source": { "spreadsheet_key": "YDP_Simple_Static_Art", "worksheet_key": "european_art" },
  "prompts": { "slovak": "src/resources/template/european_art_slovak.txt" }
}```

#### `handler_class: "DynamicTemplateHandler"`
*Note: `prompts` here is an object that maps keywords (`verbs`, `other`) to template paths.*
```json
"german_lesson": {
  "handler_class": "DynamicTemplateHandler",
  "static_image_url": "https://url.com/default.png",
  "static_image_verbs_regular_url": "https://url.com/verbs.png",
  "content_rotation_source": { "spreadsheet_key": "YDP_LLM_Dynamic_GermanLesson", "worksheet_key": "rotation" },
  "prompts": {
    "slovak": {
      "verbs": "src/resources/template/german_lesson_verbs_slovak.txt",
      "other": "src/resources/template/german_lesson_other_slovak.txt"
    }
  }
}
```

---

## V. The `"data_sources"` Section

Defines the physical location of all data. This hierarchical structure prevents the repetition of URLs.

-   **Main Key** (e.g., `"YDP_LLM_Static_Spiritual"`): A logical name for a group of data, usually corresponding to the name of a Google Sheet file.
-   **`spreadsheet_url`** (string): The full URL to the Google Sheet file.
-   **`worksheets`** (object): A map that translates **logical keys** (used in `themes`) to the **physical names of sheets** (tabs) within that file.
    -   **Key** (e.g., `"bible_sk"`): The logical key.
    -   **Value** (e.g., `"BibleSk"`): The physical name of the sheet. The value can also be an object for more complex definitions (e.g., with a `header`).

**Example:**
```json
"data_sources": {
  "YDP_LLM_Static_Spiritual": {
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1ZscwlvL7GkI.../edit",
    "worksheets": {
      "bible_sk": "BibleSk",
      "bible_en": "BibleEng"
    }
  },
  "YDP_LLM_Dynamic_MorningBriefing": {
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/16wNKda9RaZ.../edit",
    "worksheets": {
      "rotation": "Rotation",
      "historical_events": { "name": "HistoricalEvents", "header": "<b>🏛️ Today in History:</b>" }
    }
  }
}
