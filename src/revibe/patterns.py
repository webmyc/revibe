"""Regex patterns for Revibe analysis."""

import re
from typing import Optional

# Function detection patterns by language
FUNCTION_PATTERNS: dict[str, list[re.Pattern]] = {
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
CLASS_PATTERNS: dict[str, list[re.Pattern]] = {
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
IMPORT_PATTERNS: dict[str, list[re.Pattern]] = {
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
# (single_line_prefix, (multi_start, multi_end) or None)
COMMENT_PATTERNS: dict[str, tuple[str, Optional[tuple[str, str]]]] = {
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
ERROR_HANDLING_PATTERNS: dict[str, list[re.Pattern]] = {
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

# Pattern for TODO/FIXME detection
TODO_PATTERN = re.compile(r"(?:#|//|/\*|\*|<!--)\s*(?:TODO|FIXME|HACK|XXX|BUG)\s*:?\s*(.+)", re.IGNORECASE)

# String literal patterns (for copy-paste detection)
STRING_LITERAL_PATTERN = re.compile(r'["\']([^"\']{20,})["\']')
