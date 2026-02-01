"""File discovery and language detection for Revibe scanner."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Set

from revibe.constants import (
    IGNORE_DIRECTORIES,
    IGNORE_FILE_PATTERNS,
    LANGUAGE_EXTENSIONS,
    TEST_DIRECTORIES,
    TEST_FILE_PATTERNS,
)


@dataclass
class SourceFile:
    """Represents a discovered source file."""

    path: Path
    relative_path: str
    language: str
    is_test: bool
    size_bytes: int

    @property
    def extension(self) -> str:
        """Get the file extension."""
        return self.path.suffix.lower()


def detect_language(path: Path) -> Optional[str]:
    """Detect the programming language from file extension."""
    ext = path.suffix.lower()
    return LANGUAGE_EXTENSIONS.get(ext)


def is_test_file(path: Path, relative_path: str) -> bool:
    """Determine if a file is a test file based on path and name."""
    path_lower = relative_path.lower()
    name_lower = path.name.lower()

    # Check if any part of the path is a test directory
    parts = Path(relative_path).parts
    for part in parts:
        if part.lower() in TEST_DIRECTORIES:
            return True

    # Check file name patterns
    for pattern in TEST_FILE_PATTERNS:
        if pattern in name_lower:
            return True

    return False


def should_ignore_directory(name: str) -> bool:
    """Check if a directory should be ignored."""
    name_lower = name.lower()
    return name_lower in IGNORE_DIRECTORIES or name.startswith(".")


def should_ignore_file(path: Path) -> bool:
    """Check if a file should be ignored based on patterns."""
    name = path.name.lower()
    path_str = str(path).lower()

    # Check ignore patterns
    for pattern in IGNORE_FILE_PATTERNS:
        if pattern in path_str:
            return True

    # Ignore hidden files
    if name.startswith("."):
        return True

    return False


def scan_directory(
    root_path: Path,
    additional_ignores: Optional[Set[str]] = None,
) -> Iterator[SourceFile]:
    """
    Scan a directory tree and yield discovered source files.

    Args:
        root_path: The root directory to scan
        additional_ignores: Optional set of additional directory names to ignore

    Yields:
        SourceFile objects for each discovered source file
    """
    root_path = root_path.resolve()
    ignores = IGNORE_DIRECTORIES.copy()

    if additional_ignores:
        ignores = ignores | additional_ignores

    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        current_dir = Path(dirpath)

        # Filter out ignored directories (modifying in-place for efficiency)
        dirnames[:] = [
            d for d in dirnames
            if not should_ignore_directory(d) and d.lower() not in ignores
        ]

        for filename in filenames:
            file_path = current_dir / filename

            # Check if file should be ignored
            if should_ignore_file(file_path):
                continue

            # Detect language
            language = detect_language(file_path)
            if language is None:
                continue

            # Calculate relative path
            try:
                relative_path = str(file_path.relative_to(root_path))
            except ValueError:
                relative_path = str(file_path)

            # Get file size
            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0

            # Determine if it's a test file
            is_test = is_test_file(file_path, relative_path)

            yield SourceFile(
                path=file_path,
                relative_path=relative_path,
                language=language,
                is_test=is_test,
                size_bytes=size_bytes,
            )


def scan_codebase(
    path: str,
    additional_ignores: Optional[List[str]] = None,
) -> List[SourceFile]:
    """
    Scan a codebase and return all discovered source files.

    Args:
        path: Path to the codebase directory
        additional_ignores: Optional list of additional directories to ignore

    Returns:
        List of SourceFile objects

    Raises:
        ValueError: If the path doesn't exist or isn't a directory
    """
    root_path = Path(path).resolve()

    if not root_path.exists():
        raise ValueError(f"Path does not exist: {root_path}")

    if not root_path.is_dir():
        raise ValueError(f"Path is not a directory: {root_path}")

    ignore_set = set(additional_ignores) if additional_ignores else None

    files = list(scan_directory(root_path, ignore_set))

    # Sort by relative path for consistent ordering
    files.sort(key=lambda f: f.relative_path)

    return files


def get_language_breakdown(files: List[SourceFile]) -> dict:
    """
    Get a breakdown of source files by language.

    Args:
        files: List of SourceFile objects

    Returns:
        Dictionary mapping language names to file counts and line counts
    """
    breakdown = {}

    for file in files:
        if file.language not in breakdown:
            breakdown[file.language] = {
                "files": 0,
                "test_files": 0,
                "total_bytes": 0,
            }

        breakdown[file.language]["files"] += 1
        breakdown[file.language]["total_bytes"] += file.size_bytes

        if file.is_test:
            breakdown[file.language]["test_files"] += 1

    return breakdown
