"""Per-file analysis for Revibe scanner."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from revibe.constants import SENSITIVE_FUNCTION_PATTERNS
from revibe.patterns import (
    CLASS_PATTERNS,
    COMMENT_PATTERNS,
    ERROR_HANDLING_PATTERNS,
    FUNCTION_PATTERNS,
    IMPORT_PATTERNS,
    STRING_LITERAL_PATTERN,
    TODO_PATTERN,
)
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

    # Check for binary content
    if "\0" in content:
        return None

    lines = content.splitlines()
    analysis = FileAnalysis(source_file=source_file, total_lines=len(lines))

    # Get patterns for this language
    patterns = _get_language_patterns(source_file.language)
    
    # Process lines
    _analyze_lines(analysis, lines, patterns)
    
    # Calculate final scores
    analysis.complexity_score = _calculate_complexity_score(analysis, lines)

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


def _get_language_patterns(language: str) -> dict:
    """Get all regex patterns for a specific language."""
    return {
        "func": FUNCTION_PATTERNS.get(language, []),
        "class": CLASS_PATTERNS.get(language, []),
        "import": IMPORT_PATTERNS.get(language, []),
        "comment": COMMENT_PATTERNS.get(language, ("#", None)),
        "error": ERROR_HANDLING_PATTERNS.get(language, []),
    }


def _analyze_lines(analysis: FileAnalysis, lines: List[str], patterns: dict):
    """Process all lines in the file."""
    single_comment = patterns["comment"][0]
    multi_comment = patterns["comment"][1]
    
    in_multiline_comment = False
    current_function: Optional[Tuple[str, int]] = None
    current_class: Optional[Tuple[str, int, int]] = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 1. Check basic line types (blank, comments, code)
        is_comment, in_multiline_comment = _check_comments(
            stripped, single_comment, multi_comment, in_multiline_comment
        )
        
        if not stripped:
            analysis.blank_lines += 1
            continue
            
        # Check content (TODOs, imports, error handling, strings)
        _check_line_content(analysis, line, stripped, i, patterns)

        if is_comment:
            analysis.comment_lines += 1
            continue
            
        analysis.code_lines += 1

        # Check structure (functions, classes)
        current_function = _check_functions(
            analysis, line, i, patterns["func"], current_function
        )
        current_class = _check_classes(
            analysis, line, i, patterns["class"], current_class
        )

    # Close any open blocks
    _close_remaining_blocks(analysis, len(lines), current_function, current_class)


def _check_comments(
    stripped: str, 
    single: str, 
    multi: Optional[Tuple[str, str]], 
    in_multi: bool
) -> Tuple[bool, bool]:
    """Check if line is a comment and update multiline state."""
    if multi:
        start, end = multi
        if start in stripped and end in stripped:
            return True, in_multi
        if start in stripped:
            return True, True
        if end in stripped:
            return True, False
            
    if in_multi:
        return True, True
        
    if stripped.startswith(single):
        return True, False
        
    return False, False


def _check_line_content(
    analysis: FileAnalysis, 
    line: str, 
    stripped: str, 
    line_num: int, 
    patterns: dict
):
    """Check line for TODOs, imports, errors, and strings."""
    # Task Markers (TODO/FIXME)
    todo_match = TODO_PATTERN.search(line)
    if todo_match:
        analysis.todos.append((line_num, todo_match.group(1).strip()))

    # Imports
    for pattern in patterns["import"]:
        if pattern.search(line):
            analysis.imports.append(stripped)
            break

    # Error handling
    if not analysis.has_error_handling:
        for pattern in patterns["error"]:
            if pattern.search(line):
                analysis.has_error_handling = True
                break

    # String literals
    analysis.string_literals.extend(STRING_LITERAL_PATTERN.findall(line))


def _check_functions(
    analysis: FileAnalysis, 
    line: str, 
    line_num: int, 
    patterns: List, 
    current: Optional[Tuple[str, int]]
) -> Optional[Tuple[str, int]]:
    """Check for function definitions."""
    for pattern in patterns:
        match = pattern.search(line)
        if match:
            func_name = match.group(1)
            
            if current:
                _close_function(analysis, current, line_num - 1)
                
            return (func_name, line_num)
            
    return current


def _check_classes(
    analysis: FileAnalysis, 
    line: str, 
    line_num: int, 
    patterns: List, 
    current: Optional[Tuple[str, int, int]]
) -> Optional[Tuple[str, int, int]]:
    """Check for class definitions."""
    for pattern in patterns:
        match = pattern.search(line)
        if match:
            class_name = match.group(1)
            
            if current:
                _close_class(analysis, current, line_num - 1)
                
            return (class_name, line_num, 0)
            
    return current


def _close_function(analysis: FileAnalysis, current: Tuple[str, int], end_line: int):
    """Add a completed function to analysis."""
    name, start = current
    analysis.functions.append(FunctionInfo(
        name=name,
        start_line=start,
        end_line=end_line,
        line_count=end_line - start + 1,
        is_sensitive=is_sensitive_function(name),
    ))


def _close_class(analysis: FileAnalysis, current: Tuple[str, int, int], end_line: int):
    """Add a completed class to analysis."""
    name, start, method_count = current
    analysis.classes.append(ClassInfo(
        name=name,
        start_line=start,
        end_line=end_line,
        method_count=method_count,
    ))


def _close_remaining_blocks(
    analysis: FileAnalysis, 
    total_lines: int, 
    func: Optional[Tuple[str, int]], 
    cls: Optional[Tuple[str, int, int]]
):
    """Close any blocks open at end of file."""
    if func:
        _close_function(analysis, func, total_lines)
    if cls:
        _close_class(analysis, cls, total_lines)


def _calculate_complexity_score(analysis: FileAnalysis, lines: List[str]) -> float:
    """Calculate complexity score based on structure and keywords."""
    # Base indicators: functions + classes
    indicators = len(analysis.functions) + len(analysis.classes)

    # Keywords that imply branching/logic
    branching_keywords = {"if", "else", "elif", "for", "while", "switch", "case", "match", "try", "catch"}
    
    for line in lines:
        stripped = line.strip().lower()
        if not stripped:
            continue
            
        # Check start of line for keywords
        first_word = stripped.split(' ', 1)[0].split('(', 1)[0]
        if first_word in branching_keywords:
            indicators += 1

    # Normalize by lines of code
    if analysis.code_lines > 0:
        return (indicators / analysis.code_lines) * 100
    
    return 0.0
