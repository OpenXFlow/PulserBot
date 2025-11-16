# Test Documentation: `test_llm_dynamic_handler.py` (v2)

This document provides a detailed description and visualization of **every** test scenario for the unit tests that verify the individual logical steps within the `LLMDynamicHandler` pipeline. This handler is responsible for processing the `morning_briefing_sk` topic.

## Key Testing Tools

### 1. `pytest` Fixtures (`@pytest.fixture`)

*   **What it is:** Functions that prepare and provide data or objects for tests.
*   **How we use them:** The `handler_instance` fixture creates a new, clean instance of `LLMDynamicHandler` for each test, ensuring that the tests are mutually independent.

### 2. Mocking and Patching (`@patch`)

*   **What it is:** A technique where we temporarily **replace a real piece of code** with its **fake imitation (mock)**.
*   **Why it is important:** This allows us to test our logic without relying on the internet or files on the disk, making the tests extremely fast and reliable.

#### Detailed Overview of Patches Used in Tests:

*   **`@patch("...image_service.get_dynamic_image")`**
    *   **What it patches:** Replaces the `get_dynamic_image` function, isolating the test from calls to the Unsplash API.

*   **`@patch("...dynamic_content_service.get_all_dynamic_data")`**
    *   **What it patches:** Replaces the key function that assembles data for the morning briefing. This allows us to test the handler without relying on the complex logic in `dynamic_content_service`.

*   **`@patch("...ResourceCache.get_prompt")`**
    *   **What it patches:** Replaces the `get_prompt` method on the `ResourceCache` class, isolating the test from real file reading from the disk.

*   **`@patch("...llm_service.call_llm")`**
    *   **What it patches:** Replaces the `call_llm` function, isolating the test from calls to the LLM API (e.g., Groq).

*   **`@patch("...PromptBuilder.build")`**
    *   **What it patches:** Replaces the `build` method on the `PromptBuilder` class, which allows us to test the `LLMTextGenerator` in isolation.

*   **`@patch("...DynamicProcessingPipeline.execute")`**
    *   **What it patches:** Replaces the `execute` method on the `DynamicProcessingPipeline` class in the orchestration test, where we are only interested in verifying that it was called correctly.

---

## Test Scenarios & Diagrams

### 1. `test_step_user_validator`
**Objective:** Verify that the `UserValidator` step correctly requires the presence of the `user` object.

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_1...()
    participant Step as UserValidator
    participant Handler as LLMDynamicHandler

    PytestRunner->>TestFunc: Run test
    
    TestFunc->>Step: Call `execute(Handler, user=MOCK_USER)`
    Step-->>TestFunc: Return True
    
    TestFunc->>Step: Call `execute(Handler, user=None)`
    Step-->>TestFunc: Return False
    
    TestFunc->>TestFunc: Assert results
    TestFunc-->>PytestRunner: Return PASS
```

### 2. `test_step_static_image_loader`
**Objective:** Verify that the `StaticImageLoader` step correctly loads the static image URL from the configuration.

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_2...()
    participant Step as StaticImageLoader
    participant Handler as LLMDynamicHandler

    PytestRunner->>TestFunc: Run test
    Note right of TestFunc: Manually set `static_image_url` in Handler's config
    
    TestFunc->>Step: Call `execute(Handler, ...)`
    
    Note left of Step: Reads config from Handler
    Note left of Step: Populates `handler.image_url`
    Step-->>TestFunc: Return True
    
    TestFunc->>Handler: Assert `handler.image_url` is correct
    TestFunc-->>PytestRunner: Return PASS
```

### 3. `test_step_dynamic_image_fetcher`
**Objective:** Verify that the `DynamicImageFetcher` step correctly calls `image_service`.

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_3...()
    participant Step as DynamicImageFetcher
    participant Handler as LLMDynamicHandler
    participant MockImageService as Mock image_service

    PytestRunner->>TestFunc: Run test
    Note right of TestFunc: `@patch` replaces `image_service.get_dynamic_image`
    
    TestFunc->>Step: Call `execute(Handler, ...)`
    
    Step->>MockImageService: Call `get_dynamic_image()`
    MockImageService-->>Step: Return MOCK_IMAGE_DATA
    
    Note left of Step: Populates `handler.image_url` and `handler.image_attribution`
    Step-->>TestFunc: Return True
    
    TestFunc->>Handler: Assert attributes are correct
    TestFunc-->>PytestRunner: Return PASS
```

### 4. `test_step_dynamic_content_fetcher`
**Objective:** Verify that the `DynamicContentFetcher` step correctly creates the data model.

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_4...()
    participant Step as DynamicContentFetcher
    participant Handler as LLMDynamicHandler
    participant MockContentService as Mock dynamic_content_service

    PytestRunner->>TestFunc: Run test
    Note right of TestFunc: `@patch` replaces `get_all_dynamic_data`
    
    TestFunc->>Step: Call `execute(Handler, ...)`
    
    Step->>MockContentService: Call `get_all_dynamic_data()`
    MockContentService-->>Step: Return MOCK_DYNAMIC_CONTENT_DATA
    
    Note left of Step: Creates `MorningBriefingData` instance
    Note left of Step: Populates `handler.data_model`
    Step-->>TestFunc: Return True
    
    TestFunc->>Handler: Assert `handler.data_model` is correct
    TestFunc-->>PytestRunner: Return PASS
```

### 5. `test_step_prompt_loader`
**Objective:** Verify that the `PromptLoader` step correctly loads the prompt content.

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_5...()
    participant Step as PromptLoader
    participant Handler as LLMDynamicHandler
    participant MockResourceCache as Mock ResourceCache

    PytestRunner->>TestFunc: Run test
    Note right of TestFunc: `@patch` replaces `ResourceCache.get_prompt`
    
    TestFunc->>Step: Call `execute(Handler, ...)`
    
    Step->>MockResourceCache: Call `get_prompt(...)`
    MockResourceCache-->>Step: Return MOCK_PROMPT_CONTENT
    
    Note left of Step: Populates `handler._prompt_template`
    Step-->>TestFunc: Return True
    
    TestFunc->>Handler: Assert `handler._prompt_template` is correct
    TestFunc-->>PytestRunner: Return PASS
```

### 6. `test_step_llm_text_generator`
**Objective:** Verify that the `LLMTextGenerator` step correctly calls `llm_service`.

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_6...()
    participant Step as LLMTextGenerator
    participant Handler as LLMDynamicHandler
    participant MockPromptBuilder as Mock PromptBuilder
    participant MockLLM as Mock llm_service

    PytestRunner->>TestFunc: Run test
    Note right of TestFunc: `@patch` replaces `PromptBuilder.build` and `llm_service.call_llm`
    
    TestFunc->>Step: Call `execute(Handler, ...)`
    
    Step->>MockPromptBuilder: Call `build(Handler)`
    MockPromptBuilder-->>Step: Return "Final prompt"
    
    Step->>MockLLM: Call `call_llm("Final prompt")`
    MockLLM-->>Step: Return MOCK_LLM_RESPONSE
    
    Note left of Step: Populates `handler._final_text`
    Step-->>TestFunc: Return True
    
    TestFunc->>Handler: Assert `handler._final_text` is correct
    TestFunc-->>PytestRunner: Return PASS
```

### 7. `test_orchestration_process_method`
**Objective:** Verify that the main `_process` method correctly executes the entire pipeline.

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_7...()
    participant Handler as LLMDynamicHandler
    participant MockPipeline as Mock `DynamicProcessingPipeline.execute`

    PytestRunner->>TestFunc: Run test
    Note right of TestFunc: `@patch` replaces `DynamicProcessingPipeline.execute`
    
    TestFunc->>Handler: Call `_process()`
    
    Handler->>MockPipeline: Call `execute(Handler, ...)`
    Note left of MockPipeline: `side_effect` simulates a successful run
    Note left of MockPipeline: Modifies Handler to set `_final_text` and `image_url`
    MockPipeline-->>Handler: Return True
    
    Handler-->>TestFunc: Return ("Success", "https://success.url")
    
    TestFunc->>TestFunc: Assert return values are correct
    TestFunc-->>PytestRunner: Return PASS
```