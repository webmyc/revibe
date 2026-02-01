"""JSON report generation."""

import json
from datetime import datetime

from revibe.metrics import CodebaseMetrics


def generate_json_report(metrics: CodebaseMetrics, codebase_path: str, files_analysis: list) -> str:
    """
    Generate a JSON report for the codebase analysis.

    Args:
        metrics: Calculated metrics for the codebase
        codebase_path: Path to the codebase
        files_analysis: List of FileAnalysis objects

    Returns:
        JSON string
    """
    report_data = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "codebase_path": codebase_path,
            "tool": "Revibe Code Quality Scanner",
            "version": "0.1.0",
        },
        "summary": _create_summary(metrics),
        "languages": metrics.languages,
        "ai_smell_scores": metrics.ai_smell_scores,
        "files": _create_file_details(files_analysis),
        "issues": _create_issues(files_analysis, metrics),
    }

    try:
        return json.dumps(report_data, indent=2)
    except (TypeError, ValueError) as e:
        # Fallback for JSON serialization errors
        return json.dumps({
            "error": "Failed to generate JSON report",
            "details": str(e)
        }, indent=2)


def _create_summary(metrics: CodebaseMetrics) -> dict:
    """Create the summary section of the report."""
    return {
        "health_score": metrics.health_score,
        "risk_level": metrics.risk_level,
        "total_files": metrics.total_files,
        "source_files": metrics.source_files,
        "test_files": metrics.test_files,
        "total_loc": metrics.source_loc + metrics.test_loc,
        "source_loc": metrics.source_loc,
        "test_loc": metrics.test_loc,
        "test_to_code_ratio": round(metrics.test_to_code_ratio, 2) if metrics.source_loc > 0 else 0,
        "estimated_defects": round(metrics.estimated_defects, 1),
    }


def _create_file_details(files_analysis: list) -> list:
    """Create the files detail list."""
    files_list = []
    for analysis in files_analysis:
        files_list.append({
            "path": analysis.source_file.relative_path,
            "language": analysis.source_file.language,
            "lines": analysis.total_lines,
            "code_lines": analysis.code_lines,
            "comment_lines": analysis.comment_lines,
            "complexity": round(analysis.complexity_score, 1),
            "functions": analysis.function_count,
            "classes": analysis.class_count,
            "issues": {
                "todos": analysis.todo_count,
                "sensitive_functions": len(analysis.sensitive_functions),
                "long_functions": len(analysis.long_functions),
            }
        })
    return files_list


def _create_issues(files_analysis: list, metrics: CodebaseMetrics) -> dict:
    """Create the issues section."""
    all_todos = []
    sensitive_funcs = []
    long_funcs = []

    for analysis in files_analysis:
        # Collect TODOs
        for line, content in analysis.todos:
            all_todos.append({
                "file": analysis.source_file.relative_path,
                "line": line,
                "content": content
            })

        # Collect sensitive functions
        for func in analysis.sensitive_functions:
            sensitive_funcs.append({
                "file": analysis.source_file.relative_path,
                "name": func.name,
                "line": func.start_line
            })

        # Collect long functions
        for func in analysis.long_functions:
            long_funcs.append({
                "file": analysis.source_file.relative_path,
                "name": func.name,
                "lines": func.line_count
            })

    # Sort complex files
    complex_files = sorted(
        [
            {
                "file": a.source_file.relative_path,
                "score": round(a.complexity_score, 1)
            }
            for a in files_analysis if a.complexity_score > 10
        ],
        key=lambda x: x["score"],
        reverse=True
    )

    return {
        "complex_files": complex_files,
        "long_functions": long_funcs,
        "sensitive_functions": sensitive_funcs,
        "todos": all_todos,
    }
