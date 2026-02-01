"""AI code smell detection for Revibe."""

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List

from revibe.analyzer import FileAnalysis
from revibe.constants import (
    BOILERPLATE_IMPORT_RATIO,
    COPY_PASTE_MIN_OCCURRENCES,
    EXCESSIVE_COMMENT_RATIO,
    VERBOSE_NAME_LENGTH,
)


@dataclass
class SmellResult:
    """Result from a smell detector."""

    name: str
    score: float  # 0.0 - 1.0
    description: str
    details: List[str]


def clamp_score(score: float) -> float:
    """Clamp a score to the 0.0-1.0 range."""
    return max(0.0, min(1.0, score))


def detect_excessive_comments(analyses: List[FileAnalysis]) -> SmellResult:
    """
    Detect excessive comment-to-code ratio.

    AI-generated code often has verbose explanatory comments.
    """
    total_code = sum(a.code_lines for a in analyses)
    total_comments = sum(a.comment_lines for a in analyses)

    if total_code == 0:
        return SmellResult(
            name="excessive_comments",
            score=0.0,
            description="Comment-to-code ratio analysis",
            details=[],
        )

    ratio = total_comments / total_code
    score = clamp_score(ratio / EXCESSIVE_COMMENT_RATIO)

    details = []
    if score > 0.5:
        # Find files with highest comment ratios
        high_comment_files = []
        for a in analyses:
            if a.code_lines > 0:
                file_ratio = a.comment_lines / a.code_lines
                if file_ratio > EXCESSIVE_COMMENT_RATIO:
                    high_comment_files.append(
                        (a.source_file.relative_path, file_ratio)
                    )

        high_comment_files.sort(key=lambda x: x[1], reverse=True)
        for path, r in high_comment_files[:5]:
            details.append(f"{path}: {r:.1%} comments")

    return SmellResult(
        name="excessive_comments",
        score=score,
        description=f"Comment-to-code ratio: {ratio:.1%}",
        details=details,
    )


def detect_verbose_naming(analyses: List[FileAnalysis]) -> SmellResult:
    """
    Detect overly verbose function/variable names.

    AI often generates extremely descriptive names like
    'handleUserAuthenticationWithPasswordAndTwoFactorVerification'.
    """
    verbose_names = []
    total_names = 0

    for a in analyses:
        for func in a.functions:
            total_names += 1
            if len(func.name) > VERBOSE_NAME_LENGTH:
                verbose_names.append((a.source_file.relative_path, func.name))

        for cls in a.classes:
            total_names += 1
            if len(cls.name) > VERBOSE_NAME_LENGTH:
                verbose_names.append((a.source_file.relative_path, cls.name))

    if total_names == 0:
        return SmellResult(
            name="verbose_naming",
            score=0.0,
            description="Verbose naming analysis",
            details=[],
        )

    ratio = len(verbose_names) / total_names
    score = clamp_score(ratio * 2)  # Amplify since verbose names are less common

    details = [f"{path}: {name}" for path, name in verbose_names[:5]]

    return SmellResult(
        name="verbose_naming",
        score=score,
        description=f"{len(verbose_names)} names exceed {VERBOSE_NAME_LENGTH} chars",
        details=details,
    )


def detect_boilerplate_heavy(analyses: List[FileAnalysis]) -> SmellResult:
    """
    Detect high import-to-function ratio.

    AI-generated code often imports many libraries without using them fully.
    """
    total_imports = sum(len(a.imports) for a in analyses)
    total_functions = sum(len(a.functions) for a in analyses)

    if total_functions == 0:
        return SmellResult(
            name="boilerplate_heavy",
            score=0.0,
            description="Import-to-function ratio analysis",
            details=[],
        )

    ratio = total_imports / total_functions
    score = clamp_score(ratio / BOILERPLATE_IMPORT_RATIO)

    details = []
    if score > 0.3:
        # Find files with high import ratios
        for a in analyses:
            if len(a.functions) > 0:
                file_ratio = len(a.imports) / len(a.functions)
                if file_ratio > BOILERPLATE_IMPORT_RATIO:
                    details.append(
                        f"{a.source_file.relative_path}: {len(a.imports)} imports, {len(a.functions)} functions"
                    )

    return SmellResult(
        name="boilerplate_heavy",
        score=score,
        description=f"Import-to-function ratio: {ratio:.1f}",
        details=details[:5],
    )


def detect_inconsistent_patterns(analyses: List[FileAnalysis]) -> SmellResult:
    """
    Detect mixed naming conventions within the codebase.

    AI-generated code often mixes camelCase and snake_case inconsistently.
    """
    snake_case_count = 0
    camel_case_count = 0
    pascal_case_count = 0

    for a in analyses:
        for func in a.functions:
            name = func.name
            if "_" in name and name.islower():
                snake_case_count += 1
            elif name[0].isupper() and "_" not in name:
                pascal_case_count += 1
            elif name[0].islower() and any(c.isupper() for c in name):
                camel_case_count += 1

    total = snake_case_count + camel_case_count + pascal_case_count

    if total < 5:
        return SmellResult(
            name="inconsistent_patterns",
            score=0.0,
            description="Naming convention analysis",
            details=[],
        )

    # Calculate how mixed the conventions are
    counts = [snake_case_count, camel_case_count, pascal_case_count]
    dominant = max(counts)
    consistency = dominant / total

    # Lower consistency = higher smell score
    score = clamp_score(1.0 - consistency)

    details = [
        f"snake_case: {snake_case_count}",
        f"camelCase: {camel_case_count}",
        f"PascalCase: {pascal_case_count}",
    ]

    return SmellResult(
        name="inconsistent_patterns",
        score=score,
        description=f"Naming consistency: {consistency:.1%}",
        details=details,
    )


def detect_dead_code_indicators(analyses: List[FileAnalysis]) -> SmellResult:
    """
    Detect duplicate function names across files.

    AI often re-implements the same function in multiple files.
    """
    function_locations: Dict[str, List[str]] = {}

    for a in analyses:
        for func in a.functions:
            if func.name not in function_locations:
                function_locations[func.name] = []
            function_locations[func.name].append(a.source_file.relative_path)

    # Find functions defined in multiple files
    duplicates = {
        name: files for name, files in function_locations.items()
        if len(files) > 1 and name not in ("__init__", "main", "setup", "teardown", "run")
    }

    total_functions = sum(len(a.functions) for a in analyses)
    if total_functions == 0:
        return SmellResult(
            name="dead_code_indicators",
            score=0.0,
            description="Duplicate function detection",
            details=[],
        )

    duplicate_count = sum(len(files) for files in duplicates.values())
    score = clamp_score(duplicate_count / total_functions * 5)

    details = [
        f"{name}: defined in {len(files)} files"
        for name, files in sorted(duplicates.items(), key=lambda x: -len(x[1]))[:5]
    ]

    return SmellResult(
        name="dead_code_indicators",
        score=score,
        description=f"{len(duplicates)} functions have duplicate definitions",
        details=details,
    )


def detect_over_engineering(analyses: List[FileAnalysis]) -> SmellResult:
    """
    Detect excessive class density.

    AI-generated code sometimes creates unnecessary class hierarchies.
    """
    total_classes = sum(len(a.classes) for a in analyses)
    total_loc = sum(a.code_lines for a in analyses)

    if total_loc < 100:
        return SmellResult(
            name="over_engineering",
            score=0.0,
            description="Class density analysis",
            details=[],
        )

    # Classes per KLOC
    class_density = (total_classes / total_loc) * 1000

    # More than ~15 classes per KLOC is suspicious
    score = clamp_score((class_density - 10) / 20)

    details = []
    if score > 0.3:
        # Find files with many small classes
        for a in analyses:
            if len(a.classes) > 3 and a.code_lines < 200:
                details.append(
                    f"{a.source_file.relative_path}: {len(a.classes)} classes in {a.code_lines} lines"
                )

    return SmellResult(
        name="over_engineering",
        score=score,
        description=f"Class density: {class_density:.1f} per KLOC",
        details=details[:5],
    )


def detect_missing_error_handling(analyses: List[FileAnalysis]) -> SmellResult:
    """
    Detect functions without error handling.

    AI-generated code often skips proper error handling.
    """
    functions_with_errors = 0
    total_functions = 0

    files_without_handling = []

    for a in analyses:
        total_functions += len(a.functions)
        if a.has_error_handling:
            functions_with_errors += len(a.functions)
        elif len(a.functions) > 0:
            files_without_handling.append(
                (a.source_file.relative_path, len(a.functions))
            )

    if total_functions == 0:
        return SmellResult(
            name="missing_error_handling",
            score=0.0,
            description="Error handling analysis",
            details=[],
        )

    # What percentage of functions are in files without error handling?
    unhandled_ratio = 1.0 - (functions_with_errors / total_functions)
    score = clamp_score(unhandled_ratio)

    details = [
        f"{path}: {count} functions, no error handling"
        for path, count in sorted(files_without_handling, key=lambda x: -x[1])[:5]
    ]

    return SmellResult(
        name="missing_error_handling",
        score=score,
        description=f"{unhandled_ratio:.1%} of functions lack error handling",
        details=details,
    )


def detect_copy_paste_artifacts(analyses: List[FileAnalysis]) -> SmellResult:
    """
    Detect repeated string literals across files.

    AI often copy-pastes the same code patterns.
    """
    all_strings: Counter = Counter()

    for a in analyses:
        all_strings.update(a.string_literals)

    # Find strings that appear too many times
    repeated = [
        (s, count) for s, count in all_strings.items()
        if count >= COPY_PASTE_MIN_OCCURRENCES and len(s) > 20
    ]

    total_strings = sum(all_strings.values())
    if total_strings < 10:
        return SmellResult(
            name="copy_paste_artifacts",
            score=0.0,
            description="Copy-paste detection",
            details=[],
        )

    repeated_count = sum(count for _, count in repeated)
    score = clamp_score(repeated_count / total_strings * 2)

    details = [
        f'"{s[:40]}..." appears {count} times'
        for s, count in sorted(repeated, key=lambda x: -x[1])[:5]
    ]

    return SmellResult(
        name="copy_paste_artifacts",
        score=score,
        description=f"{len(repeated)} repeated string patterns",
        details=details,
    )


def detect_all_smells(analyses: List[FileAnalysis]) -> Dict[str, float]:
    """
    Run all smell detectors and return scores.

    Args:
        analyses: List of FileAnalysis objects

    Returns:
        Dictionary mapping smell names to scores (0.0-1.0)
    """
    detectors = [
        detect_excessive_comments,
        detect_verbose_naming,
        detect_boilerplate_heavy,
        detect_inconsistent_patterns,
        detect_dead_code_indicators,
        detect_over_engineering,
        detect_missing_error_handling,
        detect_copy_paste_artifacts,
    ]

    results = {}
    for detector in detectors:
        result = detector(analyses)
        results[result.name] = result.score

    return results


def get_smell_descriptions() -> Dict[str, str]:
    """Get human-readable descriptions for each smell."""
    return {
        "excessive_comments": "High ratio of comments to code (AI tends to over-explain)",
        "verbose_naming": "Overly long function/variable names (> 35 characters)",
        "boilerplate_heavy": "Many imports relative to actual functions",
        "inconsistent_patterns": "Mixed naming conventions (camelCase vs snake_case)",
        "dead_code_indicators": "Same function defined in multiple files",
        "over_engineering": "Too many classes relative to codebase size",
        "missing_error_handling": "Functions without try/catch or error handling",
        "copy_paste_artifacts": "Repeated string patterns across files",
    }
