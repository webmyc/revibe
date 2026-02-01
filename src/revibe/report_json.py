"""JSON report output for Revibe."""

import json
from datetime import datetime
from typing import Any, Dict

from revibe import __version__
from revibe.metrics import CodebaseMetrics


def generate_json_report(metrics: CodebaseMetrics, codebase_path: str) -> Dict[str, Any]:
    """
    Generate a JSON-serializable report from metrics.

    Args:
        metrics: Codebase metrics
        codebase_path: Path to the scanned codebase

    Returns:
        Dictionary suitable for JSON serialization
    """
    # Convert complex objects to serializable format
    languages = {}
    for lang, data in metrics.languages.items():
        languages[lang] = {
            "files": data["files"],
            "lines": data["lines"],
            "test_files": data.get("test_files", 0),
        }

    duplicate_groups = []
    for group in metrics.duplicate_groups:
        duplicate_groups.append({
            "files": group.files,
            "is_exact": group.is_exact,
            "similarity": group.similarity,
        })

    long_functions = []
    for file_path, func in metrics.long_functions[:20]:
        long_functions.append({
            "file": file_path,
            "name": func.name,
            "line_count": func.line_count,
            "start_line": func.start_line,
            "end_line": func.end_line,
        })

    sensitive_unhandled = []
    for file_path, func in metrics.sensitive_functions_without_error_handling[:20]:
        sensitive_unhandled.append({
            "file": file_path,
            "name": func.name,
            "line_count": func.line_count,
        })

    todos = []
    for file_path, line_num, content in metrics.todos[:50]:
        todos.append({
            "file": file_path,
            "line": line_num,
            "content": content,
        })

    return {
        "revibe_version": __version__,
        "generated_at": datetime.now().isoformat(),
        "codebase_path": codebase_path,
        "summary": {
            "health_score": metrics.health_score,
            "risk_level": metrics.risk_level,
            "total_files": metrics.total_files,
            "source_files": metrics.source_files,
            "test_files": metrics.test_files,
            "source_loc": metrics.source_loc,
            "test_loc": metrics.test_loc,
            "test_to_code_ratio": round(metrics.test_to_code_ratio, 4),
            "estimated_defects": metrics.estimated_defects,
            "defect_density": round(metrics.defect_density_estimate, 2),
            "feature_count": metrics.feature_count,
            "feature_interactions": metrics.feature_interactions,
        },
        "code_structure": {
            "total_lines": metrics.total_lines,
            "code_lines": metrics.code_lines,
            "comment_lines": metrics.comment_lines,
            "blank_lines": metrics.blank_lines,
            "total_functions": metrics.total_functions,
            "total_classes": metrics.total_classes,
            "total_imports": metrics.total_imports,
        },
        "languages": languages,
        "ai_smell_scores": {k: round(v, 3) for k, v in metrics.ai_smell_scores.items()},
        "issues": {
            "duplicate_groups": duplicate_groups,
            "long_functions": long_functions,
            "sensitive_functions_without_error_handling": sensitive_unhandled,
            "todos": todos,
        },
    }


def render_json_report(metrics: CodebaseMetrics, codebase_path: str, indent: int = 2) -> str:
    """
    Render metrics as a JSON string.

    Args:
        metrics: Codebase metrics
        codebase_path: Path to the scanned codebase
        indent: JSON indentation level

    Returns:
        JSON string
    """
    report = generate_json_report(metrics, codebase_path)
    return json.dumps(report, indent=indent)
