import os
from pathlib import Path
from typing import Iterator

def list_directory_structure(start_path: str = ".", indent: str = "    ", file_limit: int = 100) -> None:
    """
    Prints the structure of a directory in a tree-like format.

    Args:
        start_path (str): The starting path of the directory to list.
                          Defaults to the current directory.
        indent (str): The string used for indentation of nested items.
        file_limit (int): The maximum number of files to show per directory
                          to prevent excessively long outputs.
    """
    print(f"Directory listing for: {Path(start_path).resolve()}")
    tree = _build_tree(Path(start_path), file_limit=file_limit)
    for line in tree:
        print(line)

def _build_tree(dir_path: Path, prefix: str = "", file_limit: int = 100) -> Iterator[str]:
    """
    Recursively builds the directory tree structure.

    This is a generator function that yields each line of the tree structure.

    Args:
        dir_path (Path): The current directory path object.
        prefix (str): The prefix string for the current level of the tree,
                      handling connectors like '│   ' and '    '.
        file_limit (int): The maximum number of files to show per directory.

    Yields:
        Iterator[str]: A generator that yields each formatted line of the tree.
    """
    try:
        # Get all contents, handling potential permission errors
        contents = sorted(list(dir_path.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
    except OSError as e:
        yield f"{prefix}└── [Error: Cannot access '{dir_path.name}': {e}]"
        return

    # Use pointers to determine which connector to use ('├── ' or '└── ')
    pointers = ['├── '] * (len(contents) - 1) + ['└── ']

    for pointer, path in zip(pointers, contents):
        yield f"{prefix}{pointer}{path.name}"

        if path.is_dir():
            # Determine the extension for the prefix for the next level
            extension = '│   ' if pointer == '├── ' else '    '
            # Recursively yield from the subdirectory
            yield from _build_tree(path, prefix=prefix + extension, file_limit=file_limit)

if __name__ == "__main__":
    # You can change the starting path here if needed, e.g., list_directory_structure("../")
    list_directory_structure(".")