# __script_project_file_version_check.py
"""A utility script to verify the consistency of the file version comments.

This script recursively scans for all '.py' files starting from the directory
it is run from. For each file, it reads the last line, expecting a version
comment in the format: '# End of path/to/file.py (v. NNNNN)'

It then compares the filename found inside the comment with the actual
filename. If they do not match, it reports an error. It also reports
a success message for each correctly verified file.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple

# ANSI color codes for better terminal output
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RESET = "\033[0m"


def find_version_comment(lines: List[str]) -> Optional[str]:
    """Finds the version comment in the last few non-empty lines of a file.

    Args:
        lines: A list of lines from the file.

    Returns:
        The content of the version comment line if found, otherwise None.
    """
    if not lines:
        return None

    # Check the last non-empty line
    for line in reversed(lines):
        stripped_line = line.strip()
        if stripped_line:
            if stripped_line.startswith("# End of"):
                return stripped_line
            # If the last non-empty line isn't a version comment, assume there isn't one.
            return None
    return None


def extract_version_info(comment: str) -> Optional[Tuple[str, str]]:
    """Extracts the filename and version number from a version comment.

    Args:
        comment: The version comment string.

    Returns:
        A tuple (filename, version_number) if successful, otherwise None.
    """
    # Regex to extract just the filename and version from the path in the comment
    # e.g., from '# End of src/adalens/cli/main.py (v. 00086)' -> ('main.py', 'v. 00086')
    match = re.search(r"# End of .*/(.*?\.py) \(v\. \d+\)", comment)
    # Fallback for paths without slashes
    if not match:
        match = re.search(r"# End of (.*?\.py) \(v\. (\d+)\)", comment)

    if match:
        # We need to find the version number separately as the first regex doesn't capture it
        version_match = re.search(r"\(v\. (\d+)\)", comment)
        if version_match:
            filename = match.group(1).strip()
            version_str = f"v. {version_match.group(1)}"
            return filename, version_str
    return None


def main() -> None:
    """Main function to execute the file version check."""
    run_directory = Path.cwd()
    error_count = 0
    checked_files_count = 0
    ok_count = 0

    print("--- Starting File Version Comment Check ---")
    print(f"Running from: {run_directory}\n")

    # Use rglob to recursively find all .py files from the run directory
    all_py_files = sorted(list(run_directory.rglob("*.py")))

    for file_path in all_py_files:
        # Ignore files within the virtual environment and the script itself
        if ".venv" in file_path.parts or file_path.name.startswith("__script"):
            continue

        checked_files_count += 1
        actual_filename = file_path.name
        relative_path_for_display = file_path.relative_to(run_directory)

        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except OSError as e:
            print(f"{COLOR_RED}ERROR:{COLOR_RESET} Could not read file {file_path}: {e}")
            error_count += 1
            continue

        version_comment = find_version_comment(lines)

        if not version_comment:
            print(f"{COLOR_YELLOW}WARNING:{COLOR_RESET} No version comment found in: {relative_path_for_display}")
            continue

        version_info = extract_version_info(version_comment)

        if not version_info:
            print(f"{COLOR_RED}ERROR:{COLOR_RESET} Malformed version comment in: {relative_path_for_display}")
            print(f"  └─ Comment: '{version_comment}'")
            error_count += 1
            continue

        comment_filename, version_str = version_info

        if comment_filename == actual_filename:
            ok_count += 1
            # New success format
            print(f"{COLOR_GREEN}OK:{COLOR_RESET} ({version_str}) :   {relative_path_for_display!s:<70}")
        else:
            error_count += 1
            # Retain the detailed error format
            print(f"\n{COLOR_RED}ERROR:{COLOR_RESET}")
            print(f"  ├─ File:     {relative_path_for_display}")
            print(f"  └─  version :  '{version_comment}'\n")

    print("\n--- Check Complete ---")
    if error_count == 0:
        print(
            f"{COLOR_GREEN}Success! All {checked_files_count} relevant files have consistent version comments.{COLOR_RESET}"
        )
    else:
        print(
            f"Found {COLOR_GREEN}{ok_count} correct files{COLOR_RESET} and "
            f"{COLOR_RED}{error_count} error(s){COLOR_RESET} in {checked_files_count} checked files."
        )
        print("Please review the errors listed above.")


if __name__ == "__main__":
    main()
