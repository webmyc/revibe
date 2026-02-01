"""Aggregate metrics and health score calculation for Revibe."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from revibe.analyzer import FileAnalysis, FunctionInfo
from revibe.constants import (
    AI_DEFECT_MULTIPLIER,
    DEFECT_DENSITY_HUMAN_MID,
    FEATURE_PATTERNS,
    OVER_ENGINEERING_CLASS_DENSITY,
    RISK_LEVEL_ELEVATED,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_LOW,
    RISK_LEVEL_MODERATE,
    SMELL_THRESHOLD_HIGH,
    TEST_RATIO_CRITICAL,
    TEST_RATIO_EXCELLENT,
    TEST_RATIO_GOOD,
    TEST_RATIO_POOR,
)
from revibe.scanner import SourceFile


@dataclass
class DuplicateGroup:
    """A group of duplicate or near-duplicate files."""

    files: List[str]  # relative paths
    is_exact: bool
    similarity: float = 1.0


@dataclass
class CodebaseMetrics:
    """Aggregate metrics for an entire codebase."""

    # File counts
    total_files: int = 0
    source_files: int = 0
    test_files: int = 0

    # Line counts
    total_lines: int = 0
    source_loc: int = 0
    test_loc: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0

    # Code structure
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0

    # Issues
    todos: List[Tuple[str, int, str]] = field(default_factory=list)  # (file, line, content)
    duplicate_groups: List[DuplicateGroup] = field(default_factory=list)

    # Functions requiring attention
    long_functions: List[Tuple[str, FunctionInfo]] = field(default_factory=list)  # (file, func)
    sensitive_functions_without_error_handling: List[Tuple[str, FunctionInfo]] = field(default_factory=list)
    functions_by_file: Dict[str, List[FunctionInfo]] = field(default_factory=dict)

    # Language breakdown
    languages: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Smell scores (0.0 - 1.0)
    ai_smell_scores: Dict[str, float] = field(default_factory=dict)

    # Features detected
    feature_count: int = 0

    # Calculated metrics
    defect_density_estimate: float = 0.0
    estimated_defects: int = 0
    test_to_code_ratio: float = 0.0
    health_score: int = 0
    risk_level: str = "UNKNOWN"

    # Raw file analyses for fixer
    file_analyses: List[FileAnalysis] = field(default_factory=list)

    @property
    def feature_interactions(self) -> int:
        """Calculate feature interaction complexity: 2^n - 1 - n."""
        n = self.feature_count
        if n <= 0:
            return 0
        if n > 20:  # Cap to prevent overflow
            n = 20
        return (2 ** n) - 1 - n

    @property
    def all_todos(self) -> List[Tuple[str, int, str]]:
        """Get all TODOs across the codebase."""
        return self.todos

    def summary(self) -> Dict:
        """Get a summary dictionary for reporting."""
        return {
            "total_files": self.total_files,
            "source_files": self.source_files,
            "test_files": self.test_files,
            "source_loc": self.source_loc,
            "test_loc": self.test_loc,
            "test_to_code_ratio": self.test_to_code_ratio,
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "feature_count": self.feature_count,
            "feature_interactions": self.feature_interactions,
            "estimated_defects": self.estimated_defects,
            "health_score": self.health_score,
            "risk_level": self.risk_level,
            "duplicate_groups": len(self.duplicate_groups),
            "ai_smell_scores": self.ai_smell_scores,
            "todos_count": len(self.todos),
            "long_functions": len(self.long_functions),
            "languages": self.languages,
        }


def calculate_defect_estimate(
    source_loc: int,
    ai_generated: bool = True,
    base_density: float = DEFECT_DENSITY_HUMAN_MID,
) -> Tuple[float, int]:
    """
    Estimate number of defects based on lines of code.

    Args:
        source_loc: Lines of source code
        ai_generated: Whether to apply AI multiplier
        base_density: Base defect density per KLOC

    Returns:
        Tuple of (defect_density, estimated_defects)
    """
    density = base_density
    if ai_generated:
        density *= AI_DEFECT_MULTIPLIER

    estimated = int((source_loc / 1000) * density)
    return density, estimated


def detect_features(analyses: List[FileAnalysis]) -> int:
    """
    Detect the number of features/routes/endpoints in the codebase.

    Args:
        analyses: List of FileAnalysis objects

    Returns:
        Estimated feature count
    """
    feature_count = 0

    for analysis in analyses:
        language = analysis.source_file.language
        patterns = FEATURE_PATTERNS.get(language, [])

        if not patterns:
            continue

        try:
            content = analysis.source_file.path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for pattern_str in patterns:
            matches = re.findall(pattern_str, content)
            feature_count += len(matches)

    return feature_count


def calculate_health_score(metrics: "CodebaseMetrics") -> int:
    """
    Calculate health score (0-100) based on various factors.

    Factors:
    - Test coverage (40 points)
    - Code smells (20 points)
    - Duplicates (10 points)
    - Long functions (10 points)
    - Error handling (10 points)
    - TODOs (5 points)
    - Complexity (5 points)

    Returns:
        Health score between 0 and 100
    """
    score = 100

    # Test coverage (up to 40 points penalty)
    if metrics.test_to_code_ratio >= TEST_RATIO_EXCELLENT:
        pass  # No penalty
    elif metrics.test_to_code_ratio >= TEST_RATIO_GOOD:
        score -= 10
    elif metrics.test_to_code_ratio >= TEST_RATIO_POOR:
        score -= 25
    elif metrics.test_to_code_ratio >= TEST_RATIO_CRITICAL:
        score -= 35
    else:
        score -= 40

    # AI code smells (up to 20 points penalty)
    high_smells = sum(1 for s in metrics.ai_smell_scores.values() if s >= SMELL_THRESHOLD_HIGH)
    score -= min(20, high_smells * 4)

    # Duplicates (up to 10 points penalty)
    duplicate_penalty = min(10, len(metrics.duplicate_groups) * 2)
    score -= duplicate_penalty

    # Long functions (up to 10 points penalty)
    long_func_penalty = min(10, len(metrics.long_functions))
    score -= long_func_penalty

    # Error handling in sensitive functions (up to 10 points penalty)
    sensitive_unhandled = len(metrics.sensitive_functions_without_error_handling)
    score -= min(10, sensitive_unhandled * 2)

    # TODOs (up to 5 points penalty)
    if len(metrics.todos) > 20:
        score -= 5
    elif len(metrics.todos) > 10:
        score -= 3
    elif len(metrics.todos) > 5:
        score -= 1

    # Over-engineering penalty (up to 5 points)
    if metrics.source_loc > 0:
        class_density = (metrics.total_classes / metrics.source_loc) * 1000
        if class_density > OVER_ENGINEERING_CLASS_DENSITY:
            score -= 5

    return max(0, min(100, score))


def determine_risk_level(health_score: int) -> str:
    """Determine risk level from health score."""
    if health_score >= RISK_LEVEL_LOW:
        return "LOW"
    elif health_score >= RISK_LEVEL_MODERATE:
        return "MODERATE"
    elif health_score >= RISK_LEVEL_ELEVATED:
        return "ELEVATED"
    elif health_score >= RISK_LEVEL_HIGH:
        return "HIGH"
    else:
        return "CRITICAL"


def aggregate_metrics(
    source_files: List[SourceFile],
    analyses: List[FileAnalysis],
    smell_scores: Optional[Dict[str, float]] = None,
    duplicate_groups: Optional[List[DuplicateGroup]] = None,
) -> CodebaseMetrics:
    """
    Aggregate all analyses into codebase-wide metrics.

    Args:
        source_files: All discovered source files
        analyses: File analyses
        smell_scores: AI smell detection scores
        duplicate_groups: Detected duplicate file groups

    Returns:
        CodebaseMetrics with aggregated data
    """
    metrics = CodebaseMetrics()
    metrics.file_analyses = analyses

    # File counts
    metrics.total_files = len(source_files)
    metrics.source_files = sum(1 for f in source_files if not f.is_test)
    metrics.test_files = sum(1 for f in source_files if f.is_test)

    # Language breakdown
    for f in source_files:
        if f.language not in metrics.languages:
            metrics.languages[f.language] = {"files": 0, "lines": 0, "test_files": 0}
        metrics.languages[f.language]["files"] += 1
        if f.is_test:
            metrics.languages[f.language]["test_files"] += 1

    # Aggregate from analyses
    for analysis in analyses:
        is_test = analysis.source_file.is_test
        lang = analysis.source_file.language

        metrics.total_lines += analysis.total_lines
        metrics.code_lines += analysis.code_lines
        metrics.comment_lines += analysis.comment_lines
        metrics.blank_lines += analysis.blank_lines

        if is_test:
            metrics.test_loc += analysis.code_lines
        else:
            metrics.source_loc += analysis.code_lines

        if lang in metrics.languages:
            metrics.languages[lang]["lines"] += analysis.code_lines

        metrics.total_functions += analysis.function_count
        metrics.total_classes += analysis.class_count
        metrics.total_imports += analysis.import_count

        # Collect TODOs
        for line_num, content in analysis.todos:
            metrics.todos.append((analysis.source_file.relative_path, line_num, content))

        # Collect long functions
        for func in analysis.long_functions:
            metrics.long_functions.append((analysis.source_file.relative_path, func))

        # Collect sensitive functions without error handling
        if not analysis.has_error_handling:
            for func in analysis.sensitive_functions:
                metrics.sensitive_functions_without_error_handling.append(
                    (analysis.source_file.relative_path, func)
                )

        # Store functions by file for fixer
        metrics.functions_by_file[analysis.source_file.relative_path] = analysis.functions

    # Set smell scores and duplicates
    metrics.ai_smell_scores = smell_scores or {}
    metrics.duplicate_groups = duplicate_groups or []

    # Detect features
    metrics.feature_count = detect_features(analyses)

    # Calculate derived metrics
    if metrics.source_loc > 0:
        metrics.test_to_code_ratio = metrics.test_loc / metrics.source_loc
    else:
        metrics.test_to_code_ratio = 0.0

    metrics.defect_density_estimate, metrics.estimated_defects = calculate_defect_estimate(
        metrics.source_loc
    )

    # Calculate health score
    metrics.health_score = calculate_health_score(metrics)
    metrics.risk_level = determine_risk_level(metrics.health_score)

    return metrics
