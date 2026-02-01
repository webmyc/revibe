"""Constants and configuration for Revibe scanner."""

from typing import Dict, FrozenSet, List, Set

# =============================================================================
# LANGUAGE EXTENSION MAP
# =============================================================================

LANGUAGE_EXTENSIONS: Dict[str, str] = {
    # Python
    ".py": "Python",
    ".pyw": "Python",
    ".pyi": "Python",
    # JavaScript
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    # TypeScript
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    # Go
    ".go": "Go",
    # Rust
    ".rs": "Rust",
    # Java
    ".java": "Java",
    # Kotlin
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    # Swift
    ".swift": "Swift",
    # C#
    ".cs": "C#",
    # PHP
    ".php": "PHP",
    # Ruby
    ".rb": "Ruby",
    ".rake": "Ruby",
    # Dart
    ".dart": "Dart",
    # C/C++
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    # Scala
    ".scala": "Scala",
    ".sc": "Scala",
    # Elixir
    ".ex": "Elixir",
    ".exs": "Elixir",
    # Lua
    ".lua": "Lua",
    # Perl
    ".pl": "Perl",
    ".pm": "Perl",
    # R
    ".r": "R",
    ".R": "R",
    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    # Vue/Svelte
    ".vue": "Vue",
    ".svelte": "Svelte",
    # SQL
    ".sql": "SQL",
    # Haskell
    ".hs": "Haskell",
    # OCaml
    ".ml": "OCaml",
    ".mli": "OCaml",
    # F#
    ".fs": "F#",
    ".fsx": "F#",
    # Clojure
    ".clj": "Clojure",
    ".cljs": "Clojure",
    ".cljc": "Clojure",
    # Erlang
    ".erl": "Erlang",
    ".hrl": "Erlang",
    # Zig
    ".zig": "Zig",
    # Nim
    ".nim": "Nim",
    # Crystal
    ".cr": "Crystal",
    # Groovy
    ".groovy": "Groovy",
    ".gvy": "Groovy",
}

# =============================================================================
# TEST FILE PATTERNS
# =============================================================================

# Directories that typically contain tests
TEST_DIRECTORIES: FrozenSet[str] = frozenset({
    "test",
    "tests",
    "spec",
    "specs",
    "__tests__",
    "__test__",
    "test_",
    "_test",
    "testing",
})

# File name patterns that indicate test files
TEST_FILE_PATTERNS: List[str] = [
    "test_",
    "_test.",
    ".test.",
    ".spec.",
    "_spec.",
    "spec_",
    "tests.",
    "test.",
    "_tests.",
]

# =============================================================================
# IGNORE PATTERNS
# =============================================================================

# Directories to ignore during scanning
IGNORE_DIRECTORIES: FrozenSet[str] = frozenset({
    # Version control
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    # Dependencies
    "node_modules",
    "vendor",
    "vendors",
    ".vendor",
    "bower_components",
    "jspm_packages",
    # Python
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "site-packages",
    "dist-packages",
    ".eggs",
    "*.egg-info",
    ".tox",
    ".nox",
    # Build outputs
    "build",
    "dist",
    "out",
    "output",
    "target",
    "bin",
    ".build",
    "_build",
    # IDE/Editor
    ".idea",
    ".vscode",
    ".vs",
    ".eclipse",
    ".settings",
    # Coverage
    "coverage",
    ".coverage",
    "htmlcov",
    ".nyc_output",
    # Misc
    ".cache",
    ".tmp",
    "tmp",
    "temp",
    ".temp",
    "logs",
    ".next",
    ".nuxt",
    ".output",
    ".vercel",
    ".netlify",
    ".serverless",
    ".terraform",
    "Pods",
    "DerivedData",
    ".gradle",
    ".m2",
    ".cargo",
    "pkg",
})

# File patterns to ignore
IGNORE_FILE_PATTERNS: FrozenSet[str] = frozenset({
    ".min.js",
    ".min.css",
    ".bundle.js",
    ".chunk.js",
    "-lock.json",
    ".lock",
    ".map",
})

# =============================================================================
# DEFECT DENSITY CONSTANTS
# =============================================================================

# Research-based defect density estimates (defects per 1000 lines of code)
DEFECT_DENSITY_HUMAN_LOW = 15.0  # Well-tested, mature codebase
DEFECT_DENSITY_HUMAN_MID = 25.0  # Average codebase
DEFECT_DENSITY_HUMAN_HIGH = 50.0  # Rushed or legacy codebase

# AI-generated code multiplier (based on Stanford/UIUC research)
AI_DEFECT_MULTIPLIER = 1.7

# Combined estimate for vibe-coded projects
DEFECT_DENSITY_VIBE_CODED = DEFECT_DENSITY_HUMAN_MID * AI_DEFECT_MULTIPLIER  # ~42.5/KLOC

# =============================================================================
# HEALTH SCORE THRESHOLDS
# =============================================================================

# Test-to-code ratio targets
TEST_RATIO_EXCELLENT = 0.80  # 80% or higher
TEST_RATIO_GOOD = 0.50  # 50-80%
TEST_RATIO_POOR = 0.20  # 20-50%
TEST_RATIO_CRITICAL = 0.10  # Below 10% is critical

# AI smell score thresholds
SMELL_THRESHOLD_HIGH = 0.7
SMELL_THRESHOLD_MEDIUM = 0.4
SMELL_THRESHOLD_LOW = 0.2

# Health score risk levels
RISK_LEVEL_LOW = 80  # Health score >= 80
RISK_LEVEL_MODERATE = 60  # Health score 60-79
RISK_LEVEL_ELEVATED = 40  # Health score 40-59
RISK_LEVEL_HIGH = 20  # Health score 20-39
# Below 20 is CRITICAL

# =============================================================================
# CODE SMELL THRESHOLDS
# =============================================================================

# Excessive comments threshold (comment lines / code lines)
EXCESSIVE_COMMENT_RATIO = 0.5

# Verbose naming threshold (characters)
VERBOSE_NAME_LENGTH = 35

# Boilerplate heavy (imports / functions)
BOILERPLATE_IMPORT_RATIO = 3.0

# Long function threshold (lines)
LONG_FUNCTION_THRESHOLD = 80

# Over-engineering (classes per 1000 LOC)
OVER_ENGINEERING_CLASS_DENSITY = 20

# Copy-paste threshold (minimum occurrences of same string)
COPY_PASTE_MIN_OCCURRENCES = 5

# =============================================================================
# FEATURE DETECTION PATTERNS
# =============================================================================

# Patterns that indicate routes/endpoints/features
FEATURE_PATTERNS: Dict[str, List[str]] = {
    "Python": [
        r"@app\.route\(",
        r"@router\.\w+\(",
        r"@api_view\(",
        r"path\(['\"]",
        r"url\(['\"]",
        r"def\s+\w+_view\(",
    ],
    "JavaScript": [
        r"app\.(get|post|put|patch|delete)\(",
        r"router\.(get|post|put|patch|delete)\(",
        r"export\s+(default\s+)?function\s+\w+Page",
        r"export\s+(default\s+)?function\s+\w+Route",
        r"getServerSideProps",
        r"getStaticProps",
    ],
    "TypeScript": [
        r"app\.(get|post|put|patch|delete)\(",
        r"router\.(get|post|put|patch|delete)\(",
        r"export\s+(default\s+)?function\s+\w+Page",
        r"export\s+(default\s+)?function\s+\w+Route",
        r"getServerSideProps",
        r"getStaticProps",
    ],
    "Go": [
        r"http\.HandleFunc\(",
        r"r\.HandleFunc\(",
        r"router\.(GET|POST|PUT|PATCH|DELETE)\(",
        r"e\.(GET|POST|PUT|PATCH|DELETE)\(",
    ],
    "Ruby": [
        r"get\s+['\"]",
        r"post\s+['\"]",
        r"put\s+['\"]",
        r"patch\s+['\"]",
        r"delete\s+['\"]",
        r"resources\s+:",
    ],
    "PHP": [
        r"Route::(get|post|put|patch|delete)\(",
        r"->get\(['\"]",
        r"->post\(['\"]",
    ],
}

# =============================================================================
# SENSITIVE FUNCTION PATTERNS
# =============================================================================

# Function names that should have error handling
SENSITIVE_FUNCTION_PATTERNS: List[str] = [
    "payment",
    "pay_",
    "_pay",
    "charge",
    "billing",
    "invoice",
    "auth",
    "authenticate",
    "login",
    "logout",
    "signin",
    "signout",
    "signup",
    "register",
    "password",
    "passwd",
    "token",
    "secret",
    "key",
    "credential",
    "api_key",
    "apikey",
    "encrypt",
    "decrypt",
    "hash",
    "verify",
    "validate",
    "admin",
    "delete",
    "remove",
    "destroy",
    "transfer",
    "withdraw",
    "deposit",
]
