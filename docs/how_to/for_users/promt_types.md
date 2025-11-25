Tu je aktualizovaný `promt_types.md`.

**Hlavné zmeny:**
1.  Pridaný nový typ handlera: **`UserDefinedHandler`** (pre tému Užívateľská Pripomienka).
2.  Aktualizovaný popis pre `llm_dynamic` (zmena v počítaní komponentov).
3.  Jasnejšie rozdelenie podľa toho, či sa používa Cache alebo nie.

--- START OF FILE promt_types.md ---

### Theme Overview by Processing Handler

These tables provide a detailed breakdown of each theme, its processing logic (Handler), and the specific source files it uses. This document serves as a technical reference for understanding the data flow.

---

#### Handler: `LLMStaticBaseHandler` (Cached)

**Description:** These themes operate by fetching a single row of static content from a designated Google Sheet. This raw data is then combined with a set of instructions from a prompt file and sent to an **LLM** for creative text generation. Content is cached in Firestore for 24 hours to save costs.

| Theme Name | Source Spreadsheet | Source Sheet (Worksheet) | Prompt File Used |
| :--- | :--- | :--- | :--- |
| `bible_sk` | `YDP_LLM_Static_Spiritual` | `BibleSk` | `src/resources/llm/slovak/prompt_bible.txt` |
| `bible_en` | `YDP_LLM_Static_Spiritual` | `BibleEng` | `src/resources/llm/english/prompt_bible.txt` |
| `philosophy_mix`| `YDP_LLM_Static_Spiritual` | `PhilosophySk` | `src/resources/llm/slovak/prompt_philosophy_mix.txt` |
| `stary_zakon_sk`| `YDP_LLM_Static_Spiritual` | `StaryZakonSk` | `src/resources/llm/slovak/prompt_bible_study.txt` |
| `novy_zakon_sk`| `YDP_LLM_Static_Spiritual` | `NovyZakonSk` | `src/resources/llm/slovak/prompt_bible_study.txt` |

---

#### Handler: `LLMDynamicHandler` (Cached)

**Description:** A highly dynamic handler that orchestrates a pipeline to gather data from multiple sources (Name days, Weather placeholders, Rotating content). All collected data points are injected into a prompt and sent to an **LLM**. The result is cached and shared among all users in the same group.

| Theme Name | Source Spreadsheet | Source Sheets (Worksheets) | Prompt File Used |
| :--- | :--- | :--- | :--- |
| `morning_briefing_sk` | `YDP_LLM_Dynamic_MorningBriefing` | `Rotation`, `meninySk`, `DailyGreetings`, `HistoricalEvents`... | `src/resources/llm/slovak/prompt_morning_briefing.txt` |
| `morning_briefing_en` | `YDP_LLM_Dynamic_MorningBriefing` | `Rotation`, `DailyGreetings`, `HistoricalEvents`... | `src/resources/llm/english/prompt_morning_briefing.txt` |

---

#### Handler: `SimpleStaticHandler` (Cached)

**Description:** The most straightforward processing type. It loads a **single row from a single static Google Sheet** and formats the data using a simple text template file (NO LLM). Ideal for content with a fixed structure, like photos with captions.

| Theme Name | Source Spreadsheet | Source Sheet (Worksheet) | Template File Used |
| :--- | :--- | :--- | :--- |
| `family_photo` | `YDP_Simple_Static_Family` | `FamilyPhotos` | `src/resources/template/slovak/family_photo.txt` |
| `european_art` | `YDP_Simple_Static_Art` | `EuArt` | `src/resources/template/slovak/european_art.txt` |

---

#### Handler: `DynamicTemplateHandler` (Cached)

**Description:** An advanced handler for complex structured content (like language lessons). It uses a **Rotation** sheet to determine the topic (e.g., "Verbs") and then dynamically selects the appropriate template file (`verbs.txt` vs `other.txt`). Zero LLM costs, high speed.

| Theme Name | Source Spreadsheet | Source Sheets (Worksheets) | Template Files Used |
| :--- | :--- | :--- | :--- |
| `german_lesson` | `YDP_LLM_Dynamic_GermanLesson` | `Rotation`, `SlowGermanLinks`, `01_nouns_de`... | `src/resources/template/slovak/german_lesson_verbs.txt`<br>`src/resources/template/slovak/german_lesson_other.txt` |

---

#### Handler: `UserDefinedHandler` (Personalized / No Cache)

**Description:** The only handler that generates unique content for **every single user**. It reads custom text blocks and links directly from the User Profile in Firestore. It does NOT use Google Sheets for content.
*Note: The accompanying image is cached globally to save API calls.*

| Theme Name | Data Source | Processing Strategy | Template |
| :--- | :--- | :--- | :--- |
| `user_reminder` | **Firestore User Profile** | `per_user` | *Hardcoded in Handler* |

--- END OF FILE promt_types.md ---

Som pripravený generovať posledný súbor. Napíš **ok**.