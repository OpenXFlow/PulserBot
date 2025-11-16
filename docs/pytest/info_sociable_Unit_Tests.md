# Detailed Explanation: Unit vs. Integration Tests in Our Context

The distinction between a unit test and an integration test is not always sharp, but the primary criterion is: **"What exactly am I testing?"**

*   **Pure Unit Test (Solitary Unit Test):** Tests **one thing in absolute isolation**. Most often, this involves a single function or a single method. All its dependencies (other classes, modules, services) are completely mocked. The goal is to verify that this one function performs its job correctly, regardless of the surrounding world.
    *   *Example:* Testing the `_normalize_key` function in isolation.

*   **Integration Test:** Tests the **cooperation and interaction between multiple components** (modules, classes). The goal is to verify that the "parts" fit together correctly and pass data to each other as expected.

**Let's apply this to our three new tests:**

1.  **`test_step_1_fetch_image_data`:**
    *   **What it tests:** It doesn't just test *what* `_fetch_image_data` does. It tests the **integration** between `LLMStaticBaseHandler` and the `image_service` module. It verifies that the `handler` correctly calls the `image_service` and correctly processes its response (stores it in `self.image_url`). We are therefore testing **communication between two modules**. That is a core characteristic of an integration test.

2.  **`test_step_2_generate_llm_text`:**
    *   **What it tests:** It tests the cooperation of several components at once:
        1.  The core logic within `_generate_llm_text`.
        2.  Its interaction with `builtins.open` to read files.
        3.  Its interaction with `llm_service.call_llm`.
        4.  The correct assembly of the final string from multiple sources.
    *   Again, this is not a test of one thing in absolute isolation. It is a test of the **integration** of multiple parts that must work together to produce the correct result.

3.  **`test_step_3_process_orchestration`:**
    *   **What it tests:** This is the clearest example of an integration test. Its sole purpose is to verify that the `_process` method correctly **orchestrates** and calls the other (patched) methods and services in the correct order. It fundamentally tests the "glue" that holds the process together.

### Technical Term: "Sociable Unit Tests"

In modern testing theory, the term **"Sociable Unit Tests"** is sometimes used for this type of test, in contrast to **"Solitary Unit Tests"**.

*   **Solitary:** A pure unit test where everything else is mocked (including direct dependencies).
*   **Sociable:** A test that primarily focuses on one class but allows it to genuinely communicate with other classes and modules (which are part of our application's codebase, not necessarily external APIs).

Our tests are clearly "sociable." And because they test the interaction between modules, their inclusion under `integration_tests` is entirely legitimate and correct.

**Conclusion:**

Your approach and file placement are therefore completely correct. Even though we have divided the tests into smaller, more targeted parts, their essence remains integration-focused – they verify that the components of our application cooperate correctly.