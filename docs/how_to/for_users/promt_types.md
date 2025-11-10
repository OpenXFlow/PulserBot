### Theme Overview by Processing Type (`type`)

These tables provide a detailed breakdown of each theme, its processing type, the specific source files it uses, and the Google Spreadsheets it connects to for its data. This document serves as a technical reference for understanding the data flow and logic of the application.

---

#### Type: `llm_static`

**Description:** These themes operate by fetching a single row of static content from a designated Google Sheet. This raw data is then combined with a set of instructions from a prompt file and sent to an **LLM (Large Language Model)** for creative text generation. These themes may also be configured to fetch a dynamic image from an external provider like Unsplash to accompany the text.

| Theme Name | Source Spreadsheet | Source Sheet (Worksheet) | Prompt File Used |
| :--- | :--- | :--- | :--- |
| `bible_sk` | `YDP_LLM_Static_Spiritual` | `BibleSk` | `src/rsc_llm_prompts/prompt_bible_slovak.txt` |
| `bible_en` | `YDP_LLM_Static_Spiritual` | `BibleEng` | `src/rsc_llm_prompts/prompt_bible_english.txt` |
| `philosophy_mix`| `YDP_LLM_Static_Spiritual` | `PhilosophySk` | `src/rsc_llm_prompts/prompt_philosophy_mix_slovak.txt` |
| `stary_zakon_sk`| `YDP_LLM_Static_Spiritual` | `StaryZakonSk` | `src/rsc_llm_prompts/prompt_bible_study_slovak.txt` |
| `novy_zakon_sk`| `YDP_LLM_Static_Spiritual` | `NovyZakonSk` | `src/rsc_llm_prompts/prompt_bible_study_slovak.txt` |

---

#### Type: `llm_dynamic`

**Description:** This is a highly dynamic theme type that gathers data in real-time from **multiple, often rotating, sources**. It is orchestrated by the `dynamic_content_service`, which can fetch data such as weather from an API, name days from a sheet, and a rotating piece of content determined by a `Rotation` sheet. All collected data points are then injected into a prompt and sent to an **LLM**, which composes them into a single, coherent, and well-formatted message.

| Theme Name | Source Spreadsheet | Source Sheets (Worksheets) | Prompt File Used |
| :--- | :--- | :--- | :--- |
| `morning_briefing_sk` | `YDP_LLM_Dynamic_MorningBriefing` | `Rotation`, `meninySk`, `DailyGreetings`, `HistoricalEvents`, `FunFacts`, `Quotes`, `Reflections`, `Challenges`, `Perspectives`, `WordOfTheDay` | `src/rsc_llm_prompts/prompt_morning_briefing_slovak.txt` |

---

#### Type: `simple_static`

**Description:** This is the most straightforward processing type. It loads a **single row from a single static Google Sheet** and formats the data using a simple text template file. It **does not use an LLM**, instead performing a direct find-and-replace on placeholders within the template. This type is ideal for content with a fixed and unchanging structure, such as private photo captions or simple data displays.

| Theme Name | Source Spreadsheet | Source Sheet (Worksheet) | Template File Used |
| :--- | :--- | :--- | :--- |
| `family_photo` | `YDP_Simple_Static_Family` | `FamilyPhotos` | `src/rsc_templates/family_photo_slovak.txt` |
| `european_art` | `YDP_Simple_Static_Art` | `EuArt` | `src/rsc_templates/european_art_slovak.txt` |

---

#### Type: `dynamic_template`

**Description:** This is an advanced, highly efficient theme type designed for complex but structured content. It dynamically assembles data from multiple sources based on a rotation mechanism, similar to `llm_dynamic`. However, it **does not use an LLM** for the final output. Instead, it **dynamically selects the appropriate text template** based on the type of content for the day (e.g., choosing a "verbs" template or an "other" template) and directly substitutes the fetched data into the placeholders. This provides dynamic content with zero LLM-related costs and maximum speed.

| Theme Name | Source Spreadsheet | Source Sheets (Worksheets) | Template Files Used |
| :--- | :--- | :--- | :--- |
| `german_lesson` | `YDP_LLM_Dynamic_GermanLesson` | `Rotation`, `SlowGermanLinks`, `01_nouns_de`, `02_verbs_irregular_de`, etc. | `src/rsc_templates/german_lesson_verbs_slovak.txt`<br>`src/rsc_templates/german_lesson_other_slovak.txt` |