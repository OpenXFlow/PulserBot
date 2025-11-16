# Test Documentation: `test_llm_static_handler.py` (v4)

This document provides a detailed description and visualization of the test scenarios for **unit tests** that verify **individual logical steps within the `LLMStaticBaseHandler`**. The tests are parameterized to cover all relevant topics that inherit from this base class (`bible_sk`, `philosophy_mix`, `novy_zakon_sk`, `stary_zakon_sk`).

## Key Testing Tools

### 1. Parameterization (`@pytest.mark.parametrize`)

*   **What it is:** This `pytest` decorator allows the **same test function to be run multiple times with different input data**.
*   **How we use it:** At the level of the entire test class, we have defined a list of scenarios (`TEST_SCENARIOS`). `pytest` automatically runs all tests in the class for every single scenario, effectively testing four different topics using a single test code block.

### 2. `pytest` Fixtures (`@pytest.fixture`)

*   **What it is:** Functions that prepare and provide data or objects for tests.
*   **How we use them:**
    *   `handler_instance`: Dynamically creates an instance of the correct handler (`BibleHandler`, `PhilosophyHandler`, etc.) based on the parameters from the current scenario.
    *   `theme_config`: Prepares the minimum necessary configuration for the currently tested theme.

### 3. Mocking and Patching (`@patch`, `monkeypatch`)

*   **What it is:** A technique where we temporarily **replace a real piece of code** (e.g., an API call) with its **fake imitation (mock)**.
*   **Why it is important:** This allows us to test our logic without reliance on the internet or external files, making the tests extremely fast and reliable.

#### Detailed Overview of Patches Used in Tests:

*   **`monkeypatch.setattr("src.handlers._base.llm_static_base.image_service.get_dynamic_image", ...)`**
    *   **What it patches:** Replaces the `get_dynamic_image` function directly in the module where `LLMStaticBaseHandler` imports and uses it, isolating the test from calls to the Unsplash API.

*   **`@patch("builtins.open")`**
    *   **What it patches:** Replaces the global built-in function `open`, which is used for reading files, isolating the test from the actual file system.

*   **`@patch("src.handlers._base.llm_static_base.llm_service.call_llm")`**
    *   **What it patches:** Replaces the `call_llm` function in the module where `LLMStaticBaseHandler` uses it, isolating the test from calls to the LLM API (e.g., Groq).

*   **`@patch("src.handlers._base.llm_static_base.sheets_service")`**
    *   **What it patches:** Replaces the **entire module** `sheets_service` with a single mock object, allowing us to control the behavior of all its functions (`get_worksheet`, `get_unused_item`, `mark_item_as_used`) simultaneously.

*   **`monkeypatch.setattr(handler_instance, "_fetch_image_data", ...)`**
    *   **What it patches:** Replaces an **internal method** on the already existing `handler_instance`, which is useful in the orchestration test where we do not need to retest its detailed logic.

---

## Test Description

### Scenario 1: `test_step_1_fetch_image_data`

**Objective:** Verify that the `_fetch_image_data` method correctly calls `image_service` and correctly populates the attributes on the handler instance.
**Method:** `monkeypatch` is used to replace `image_service.get_dynamic_image` with a mock. Subsequently, the state of the handler instance is verified.

### Scenario 2: `test_step_2_generate_llm_text`

**Objective:** Verify that the `_generate_llm_text` method correctly assembles the final message text.
**Method:** The `@patch` decorator is used to replace the functions `builtins.open` and `llm_service.call_llm` with mocks. Subsequently, it is verified whether the resulting string is correctly assembled.

### Scenario 3: `test_step_3_process_orchestration`

**Objective:** Verify that the orchestration method `_process` correctly calls the individual sub-methods.
**Method:** `monkeypatch` is used to replace internal methods and the entire `sheets_service` module. The test verifies that `_process` calls them and correctly calls `sheets_service.mark_item_as_used` at the end.

---

## Sequence Diagrams (Mermaid) - Example for Scenario `philosophy_mix`

### Diagram for `test_step_1_fetch_image_data`

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_1...()
    participant Handler as PhilosophyHandler
    participant MockImageService as Mock image_service

    PytestRunner->>TestFunc: Run test (scenario: 'philosophy_mix')
    Note right of TestFunc: Fixture creates PhilosophyHandler instance
    Note right of TestFunc: Monkeypatch replaces `image_service.get_dynamic_image`
    
    TestFunc->>Handler: Call `_fetch_image_data()`
    Handler->>MockImageService: Call `get_dynamic_image()`
    MockImageService-->>Handler: Return MOCK_IMAGE_DATA
    
    Note left of Handler: Populates self.image_url & self.image_attribution
    
    TestFunc->>Handler: Assert self.image_url & self.image_attribution
    
    TestFunc-->>PytestRunner: Return PASS
```

### Diagram for `test_step_2_generate_llm_text`

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_2...()
    participant Handler as PhilosophyHandler
    participant MockLLM as Mock llm_service
    participant MockOpen as Mock builtins.open

    PytestRunner->>TestFunc: Run test (scenario: 'philosophy_mix')
    Note right of TestFunc: Fixture creates Handler instance
    Note right of TestFunc: `@patch` replaces `open` and `call_llm`
    
    TestFunc->>Handler: Call `_generate_llm_text(MOCK_DATA)`
    
    Handler->>MockOpen: Read prompt & footer files
    MockOpen-->>Handler: Return mock content
    
    Handler->>MockLLM: Call `call_llm(prompt)`
    MockLLM-->>Handler: Return MOCK_LLM_RESPONSE
    
    Handler-->>TestFunc: Return final_text
    
    TestFunc->>TestFunc: Assert final_text == MOCK_LLM_RESPONSE
    TestFunc-->>PytestRunner: Return PASS
```

### Diagram for `test_step_3_process_orchestration`

```mermaid
sequenceDiagram
    participant PytestRunner
    participant TestFunc as test_step_3...()
    participant Handler as PhilosophyHandler
    participant PatchedMethods as Patched internal methods
    participant MockSheets as Mock sheets_service

    PytestRunner->>TestFunc: Run test (scenario: 'philosophy_mix')
    Note right of TestFunc: Fixture creates Handler instance
    Note right of TestFunc: Monkeypatch replaces internal methods & sheets_service module
    
    TestFunc->>Handler: Call `_process()`
    
    Handler->>PatchedMethods: Call `_fetch_image_data()` & `_generate_llm_text()`
    
    Handler->>MockSheets: Call `get_worksheet()` & `get_unused_item()`
    MockSheets-->>Handler: Return mock data
    
    Handler->>MockSheets: Call `mark_item_as_used()`
    
    Handler-->>TestFunc: Return (final_text, final_image_url)
    
    TestFunc->>TestFunc: Assert return values
    TestFunc->>MockSheets: Assert `mark_item_as_used` was called
    TestFunc-->>PytestRunner: Return PASS
```