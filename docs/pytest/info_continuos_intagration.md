--- START OF FILE info_continuos_intagration.md ---


### Continuous Integration automated

When you want your tests to run automatically (which is the goal), we will do the following:

1.  **Create a New Workflow File:** We will create a second file in `.github/workflows/`, for example, `ci.yml` (Continuous Integration).
2.  **Configure the Trigger:** This new workflow will be set up not to run on a time schedule, but to run **on every `push` or `pull request`** to the `main` (or another) branch.
3.  **Define the Steps:** In this `ci.yml` file, the steps will include:
    *   Checkout of the code.
    *   Setting up Python.
    *   Installation of **all** dependencies (from `requirements.txt` **and** `requirements-dev.txt`).
    *   Execution of the command `uv run pytest`.
    *   (Optional) If tests fail, the workflow fails and, for example, prevents the code from being merged.

This way, we will have two completely separate and independent workflows:
*   **`scheduler.yml`:** Handles the production execution of tasks.
*   **`ci.yml`:** Handles the automated testing of code quality with every change.



### Summary of Steps for Setting up and Running `pytest`
**1. Creating the Directory Structure:**
First, we had to create the standard directory structure for tests that `pytest` automatically recognizes:
*   We created the main `tests/` directory.
*   Inside it, we created the `integration_tests/` subdirectory to separate this type of test.
**2. Defining and Installing Development Dependencies:**
Testing tools are not part of the production code, so we separated them.
*   We created the file `requirements-dev.txt`.
*   We added two key packages to it:
    *   `pytest`: The tool itself for running tests.
    *   `pytest-dotenv`: An essential plugin that allows `pytest` to automatically load environment variables from your `.env` file (e.g., `GROQ_API_KEY`).
*   We installed these dependencies using the command:
    ``` uv pip install -r requirements-dev.txt    ```
**3. Creating Central Test Configuration (`conftest.py`):**
To avoid code repetition and ensure that no test accidentally sends a real message, we created a central configuration file `tests/conftest.py`.
*   **Its main task is "mocking" (substituting) the Telegram API.**
*   It contains a `pytest` fixture named `telegram_mocker` that runs **automatically before every test**.
*   This fixture temporarily replaces the real `send_message` and `send_photo` functions with fake versions that merely record the data they were called with into the `captured_telegram_calls` list.
**4. Writing the Test Files Themselves:**
We created the individual `test_*.py` files (`test_llm_static_handler.py`, etc.). Each of them contains:
*   **Mocking Dependencies:** Use of `@patch` and `monkeypatch` to replace all external services (Google Sheets, LLM, Unsplash) and file reading. This ensured that the tests are fast and independent of the internet.
*   **Test Scenarios:** Defining mocked data and expected results.
*   **`assert` Statements:** The actual logic that verifies whether the tested code behaved exactly as expected.
**5. Running the Tests with the Correct Command:**
Finally, we used the final command to run them.
*   We used `uv run pytest` to ensure that `pytest` runs in the correct, isolated environment.
*   We added the `-s` switch to see our diagnostic `print()` statements if needed.
    ```bash
    uv run pytest -s tests/integration_tests/
    ```


### Summary of Prerequisites for uv
**1. Python Installed:**
*   **Prerequisite:** The Python interpreter must be installed on your system (Windows, macOS, Linux). Although `uv` is written in Rust, its main purpose is to manage Python projects, so it would have nothing to manage without Python itself.
**2. `uv` Installed:**
*   **Prerequisite:** You must have the `uv` tool itself installed. `uv` is not a standard part of Python. It is installed separately, usually by one of the commands recommended in its official documentation (e.g., via `pip`, `pipx`, `curl`, or `PowerShell`).
    *   Installation Example:
	``` pip install uv```
**3. Existing Virtual Environment (`.venv`):**
*   **Prerequisite:** A virtual environment must exist in the root directory of your project (`C:\_jd_programming\python\13_daily-reflection-bot`) that `uv` could activate and use.
*   This environment was likely created either directly using `uv` (e.g., `uv venv`) or the older way (`python -m venv .venv`). `uv` is smart enough to automatically find and use the existing `.venv` directory.
**4. Activated Virtual Environment (Good habit, not necessity for `uv run`):**
*   **Prerequisite (recommended):** Although the `uv run` command can work even without explicit environment activation, it is standard and good practice to have the environment activated in the terminal (e.g., with the command `.venv\Scripts\activate`). The fact that we see `(.venv)` in your command line confirms that this prerequisite was met.
**Brief Summary:**
To run `uv run ...`, you needed to have **Python and `uv` installed** on your computer and a **prepared virtual environment** in the project. Everything else (installing `pytest`, etc.) happened *using* `uv`.



### Summary of Prerequisites for (`.venv`)
To create, activate, and populate the `.venv` virtual environment, we need to meet the following prerequisites and perform these steps:
**Prerequisite: Python Installed**
*   Python (version 3.3+) must be installed on your system because it contains the built-in `venv` module. You can verify this with the command `python --version` or `py --version`.

**Step 1: Creating the Virtual Environment**
This is a one-time step at the beginning of the project.
*   **Command:**
	`python -m venv .venv`
*   **What happens:**
    *   A new directory named `.venv` is created in the root directory of your project.
    *   Python copies or creates links to the basic Python interpreter and tools (like `pip`) into this directory.
    *   A `Lib/site-packages` subdirectory is created, which is currently empty. All project-specific dependencies will be installed here.
**Step 2: Activating the Virtual Environment**
This is the step you must take **every time you open a new terminal** and want to work on the project.
*   **Command (for Windows):**
	`.venv\Scripts\activate`
*   **What happens:**
    *   This script modifies the settings of your current terminal.
    *   **The most important change:** It changes the system variable `PATH` so that when you enter the command `python` or `pip`, the system first searches for these commands inside the `.venv/Scripts/` directory.
    *   **Visual Indicator:** Your command line changes, and `(.venv)` appears at the beginning, clearly signaling that you are working in an isolated environment. From this moment on, all `pip` commands will install packages only into this `.venv` and not into the global system.
**Step 3: Installing Dependencies**
When the environment is active, we can install all the libraries our project needs into it.
*   **Prerequisite:** A `requirements.txt` file must exist in the project, containing a list of necessary libraries (e.g., `pytest`, `httpx`, `gspread`).
*   **Command:**
	`pip install -r requirements.txt`
*   **What happens:**
    *   `pip` (now the one from our `.venv`) reads the `requirements.txt` file line by line.
    *   For each library, it downloads its code from the PyPI (Python Package Index) repository on the internet.
    *   It installs this code into the `.venv/Lib/site-packages` directory.
    *   These libraries are now available for your project but remain completely separate from other projects or the global Python installation.
**Summary:**
These three commands form the basic workflow for any modern Python project. They ensure that your project is **isolated, reproducible, and conflict-free**. Tools like `uv` only speed up and simplify this process, but the fundamental principles remain the same.
