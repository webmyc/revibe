"""Per-file analysis for Revibe scanner."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from revibe.constants import SENSITIVE_FUNCTION_PATTERNS
from revibe.scanner import SourceFile


@dataclass
class FunctionInfo:
    """Information about a function/method."""

    name: str
    start_line: int
    end_line: int
    line_count: int
    is_sensitive: bool = False

    @property
    def is_long(self) -> bool:
        """Check if function is considered long (> 80 lines)."""
        return self.line_count > 80


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    start_line: int
    end_line: int
    method_count: int


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""

    source_file: SourceFile
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    todos: List[Tuple[int, str]] = field(default_factory=list)  # (line_number, content)
    string_literals: List[str] = field(default_factory=list)
    has_error_handling: bool = False
    complexity_score: float = 0.0

    @property
    def function_count(self) -> int:
        return len(self.functions)

    @property
    def class_count(self) -> int:
        return len(self.classes)

    @property
    def import_count(self) -> int:
        return len(self.imports)

    @property
    def todo_count(self) -> int:
        return len(self.todos)

    @property
    def sensitive_functions(self) -> List[FunctionInfo]:
        """Get functions that handle sensitive operations."""
        return [f for f in self.functions if f.is_sensitive]

    @property
    def long_functions(self) -> List[FunctionInfo]:
        """Get functions that are considered too long."""
        return [f for f in self.functions if f.is_long]


# =============================================================================
# LANGUAGE-SPECIFIC PATTERNS
# =============================================================================

# Function detection patterns by language
FUNCTION_PATTERNS: Dict[str, List[re.Pattern]] = {
    "Python": [
        re.compile(r"^\s*def\s+(\w+)\s*\("),
        re.compile(r"^\s*async\s+def\s+(\w+)\s*\("),
    ],
    "JavaScript": [
        re.compile(r"^\s*function\s+(\w+)\s*\("),
        re.compile(r"^\s*async\s+function\s+(\w+)\s*\("),
        re.compile(r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\("),
        re.compile(r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function"),
        re.compile(r"^\s*(\w+)\s*:\s*(?:async\s+)?function"),
        re.compile(r"^\s*(\w+)\s*\([^)]*\)\s*{"),
    ],
    "TypeScript": [
        re.compile(r"^\s*function\s+(\w+)\s*[<(]"),
        re.compile(r"^\s*async\s+function\s+(\w+)\s*[<(]"),
        re.compile(r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\("),
        re.compile(r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function"),
        re.compile(r"^\s*(?:public|private|protected)?\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*[:{]"),
    ],
    "Go": [
        re.compile(r"^\s*func\s+(?:\([^)]+\)\s+)?(\w+)\s*\("),
    ],
    "Rust": [
        re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*[<(]"),
    ],
    "Java": [
        re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+)?\s*{"),
    ],
    "Kotlin": [
        re.compile(r"^\s*(?:fun|suspend\s+fun)\s+(\w+)\s*[<(]"),
    ],
    "Swift": [
        re.compile(r"^\s*(?:func|class\s+func|static\s+func)\s+(\w+)\s*[<(]"),
    ],
    "C#": [
        re.compile(r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?(?:async\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*{"),
    ],
    "PHP": [
        re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?function\s+(\w+)\s*\("),
    ],
    "Ruby": [
        re.compile(r"^\s*def\s+(?:self\.)?(\w+)"),
    ],
    "Dart": [
        re.compile(r"^\s*(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:async\s*)?{"),
    ],
}

# Class detection patterns by language
CLASS_PATTERNS: Dict[str, List[re.Pattern]] = {
    "Python": [re.compile(r"^\s*class\s+(\w+)")],
    "JavaScript": [re.compile(r"^\s*class\s+(\w+)")],
    "TypeScript": [re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)")],
    "Go": [re.compile(r"^\s*type\s+(\w+)\s+struct\s*{")],
    "Rust": [re.compile(r"^\s*(?:pub\s+)?struct\s+(\w+)")],
    "Java": [re.compile(r"^\s*(?:public\s+)?(?:abstract\s+)?class\s+(\w+)")],
    "Kotlin": [re.compile(r"^\s*(?:data\s+)?class\s+(\w+)")],
    "Swift": [re.compile(r"^\s*(?:class|struct)\s+(\w+)")],
    "C#": [re.compile(r"^\s*(?:public\s+)?(?:partial\s+)?class\s+(\w+)")],
    "PHP": [re.compile(r"^\s*class\s+(\w+)")],
    "Ruby": [re.compile(r"^\s*class\s+(\w+)")],
    "Dart": [re.compile(r"^\s*class\s+(\w+)")],
}

# Import patterns by language
IMPORT_PATTERNS: Dict[str, List[re.Pattern]] = {
    "Python": [
        re.compile(r"^\s*import\s+(\S+)"),
        re.compile(r"^\s*from\s+(\S+)\s+import"),
    ],
    "JavaScript": [
        re.compile(r"^\s*import\s+"),
        re.compile(r"^\s*(?:const|let|var)\s+\w+\s*=\s*require\("),
    ],
    "TypeScript": [
        re.compile(r"^\s*import\s+"),
    ],
    "Go": [re.compile(r"^\s*import\s+")],
    "Rust": [re.compile(r"^\s*use\s+")],
    "Java": [re.compile(r"^\s*import\s+")],
    "Kotlin": [re.compile(r"^\s*import\s+")],
    "Swift": [re.compile(r"^\s*import\s+")],
    "C#": [re.compile(r"^\s*using\s+")],
    "PHP": [re.compile(r"^\s*(?:use|require|include)")],
    "Ruby": [re.compile(r"^\s*require")],
    "Dart": [re.compile(r"^\s*import\s+")],
}

# Comment patterns by language
COMMENT_PATTERNS: Dict[str, Tuple[str, Optional[Tuple[str, str]]]] = {
    # (single_line_prefix, (multi_start, multi_end) or None)
    "Python": ("#", ('"""', '"""')),
    "JavaScript": ("//", ("/*", "*/")),
    "TypeScript": ("//", ("/*", "*/")),
    "Go": ("//", ("/*", "*/")),
    "Rust": ("//", ("/*", "*/")),
    "Java": ("//", ("/*", "*/")),
    "Kotlin": ("//", ("/*", "*/")),
    "Swift": ("//", ("/*", "*/")),
    "C#": ("//", ("/*", "*/")),
    "PHP": ("//", ("/*", "*/")),
    "Ruby": ("#", ("=begin", "=end")),
    "Dart": ("//", ("/*", "*/")),
    "C": ("//", ("/*", "*/")),
    "C++": ("//", ("/*", "*/")),
    "Shell": ("#", None),
}

# Error handling patterns
ERROR_HANDLING_PATTERNS: Dict[str, List[re.Pattern]] = {
    "Python": [re.compile(r"^\s*try\s*:"), re.compile(r"^\s*except\s*")],
    "JavaScript": [re.compile(r"^\s*try\s*{"), re.compile(r"\.catch\s*\(")],
    "TypeScript": [re.compile(r"^\s*try\s*{"), re.compile(r"\.catch\s*\(")],
    "Go": [re.compile(r"if\s+err\s*!=\s*nil")],
    "Rust": [re.compile(r"\?\s*;"), re.compile(r"\.unwrap_or")],
    "Java": [re.compile(r"^\s*try\s*{"), re.compile(r"^\s*catch\s*\(")],
    "Kotlin": [re.compile(r"^\s*try\s*{"), re.compile(r"^\s*catch\s*\(")],
    "Swift": [re.compile(r"^\s*do\s*{"), re.compile(r"^\s*catch\s*")],
    "C#": [re.compile(r"^\s*try\s*{"), re.compile(r"^\s*catch\s*\(")],
    "PHP": [re.compile(r"^\s*try\s*{"), re.compile(r"^\s*catch\s*\(")],
    "Ruby": [re.compile(r"^\s*begin\s*$"), re.compile(r"^\s*rescue\s*")],
    "Dart": [re.compile(r"^\s*try\s*{"), re.compile(r"^\s*catch\s*\(")],
}

# TODO/FIXME pattern
TODO_PATTERN = re.compile(r"(?:#|//|/\*|\*|<!--)\s*(?:TODO|FIXME|HACK|XXX|BUG)\s*:?\s*(.+)", re.IGNORECASE)

# String literal patterns (for copy-paste detection)
STRING_LITERAL_PATTERN = re.compile(r'["\']([^"\']{20,})["\']')


def is_sensitive_function(name: str) -> bool:
    """Check if a function name indicates it handles sensitive operations."""
    name_lower = name.lower()
    return any(pattern in name_lower for pattern in SENSITIVE_FUNCTION_PATTERNS)


def analyze_file(source_file: SourceFile) -> Optional[FileAnalysis]:
    """
    Analyze a single source file.

    Args:
        source_file: The SourceFile to analyze

    Returns:
        FileAnalysis with results, or None if file can't be read
    """
    try:
        content = source_file.path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return None

    lines = content.splitlines()
    analysis = FileAnalysis(source_file=source_file, total_lines=len(lines))

    language = source_file.language

    # Get language-specific patterns
    func_patterns = FUNCTION_PATTERNS.get(language, [])
    class_patterns = CLASS_PATTERNS.get(language, [])
    import_patterns = IMPORT_PATTERNS.get(language, [])
    comment_info = COMMENT_PATTERNS.get(language, ("#", None))
    error_patterns = ERROR_HANDLING_PATTERNS.get(language, [])

    single_comment = comment_info[0]
    multi_comment = comment_info[1]

    in_multiline_comment = False
    current_function: Optional[Tuple[str, int]] = None
    current_class: Optional[Tuple[str, int, int]] = None  # (name, start, method_count)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Count line types
        if not stripped:
            analysis.blank_lines += 1
            continue

        # Check for multi-line comment boundaries
        if multi_comment:
            if multi_comment[0] in stripped and multi_comment[1] in stripped:
                analysis.comment_lines += 1
                continue
            elif multi_comment[0] in stripped:
                in_multiline_comment = True
                analysis.comment_lines += 1
                continue
            elif multi_comment[1] in stripped:
                in_multiline_comment = False
                analysis.comment_lines += 1
                continue

        if in_multiline_comment:
            analysis.comment_lines += 1
            continue

        # Single line comments
        if stripped.startswith(single_comment):
            analysis.comment_lines += 1
        else:
            analysis.code_lines += 1

        # Check for TODOs
        todo_match = TODO_PATTERN.search(line)
        if todo_match:
            analysis.todos.append((i, todo_match.group(1).strip()))

        # Check for imports
        for pattern in import_patterns:
            if pattern.search(line):
                analysis.imports.append(stripped)
                break

        # Check for error handling
        if not analysis.has_error_handling:
            for pattern in error_patterns:
                if pattern.search(line):
                    analysis.has_error_handling = True
                    break

        # Check for functions
        for pattern in func_patterns:
            match = pattern.search(line)
            if match:
                func_name = match.group(1)

                # Close previous function if any
                if current_function:
                    prev_name, prev_start = current_function
                    analysis.functions.append(FunctionInfo(
                        name=prev_name,
                        start_line=prev_start,
                        end_line=i - 1,
                        line_count=i - prev_start,
                        is_sensitive=is_sensitive_function(prev_name),
                    ))

                current_function = (func_name, i)
                break

        # Check for classes
        for pattern in class_patterns:
            match = pattern.search(line)
            if match:
                class_name = match.group(1)

                # Close previous class if any
                if current_class:
                    prev_name, prev_start, method_count = current_class
                    analysis.classes.append(ClassInfo(
                        name=prev_name,
                        start_line=prev_start,
                        end_line=i - 1,
                        method_count=method_count,
                    ))

                current_class = (class_name, i, 0)
                break

        # Extract string literals
        string_matches = STRING_LITERAL_PATTERN.findall(line)
        analysis.string_literals.extend(string_matches)

    # Close final function/class
    if current_function:
        name, start = current_function
        analysis.functions.append(FunctionInfo(
            name=name,
            start_line=start,
            end_line=len(lines),
            line_count=len(lines) - start + 1,
            is_sensitive=is_sensitive_function(name),
        ))

    if current_class:
        name, start, method_count = current_class
        analysis.classes.append(ClassInfo(
            name=name,
            start_line=start,
            end_line=len(lines),
            method_count=method_count,
        ))

    # Calculate complexity score (simplified cyclomatic-ish metric)
    # Based on: functions, classes, nesting indicators, conditionals
    complexity_indicators = len(analysis.functions) + len(analysis.classes)

    # Count branching keywords
    branching_keywords = ["if", "else", "elif", "for", "while", "switch", "case", "match", "try", "catch"]
    for line in lines:
        stripped = line.strip().lower()
        for keyword in branching_keywords:
            if stripped.startswith(keyword + " ") or stripped.startswith(keyword + "("):
                complexity_indicators += 1
                break

    # Normalize by lines of code
    if analysis.code_lines > 0:
        analysis.complexity_score = complexity_indicators / analysis.code_lines * 100
    else:
        analysis.complexity_score = 0.0

    return analysis


def analyze_files(source_files: List[SourceFile]) -> List[FileAnalysis]:
    """
    Analyze multiple source files.

    Args:
        source_files: List of SourceFile objects to analyze

    Returns:
        List of FileAnalysis objects (excludes files that couldn't be read)
    """
    analyses = []

    for source_file in source_files:
        analysis = analyze_file(source_file)
        if analysis:
            analyses.append(analysis)

    return analyses
