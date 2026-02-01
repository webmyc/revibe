"""Tests for the analyzer module."""

import pytest

from revibe.analyzer import (
    FileAnalysis,
    FunctionInfo,
    analyze_file,
    analyze_files,
    is_sensitive_function,
)
from revibe.scanner import scan_codebase


class TestIsSensitiveFunction:
    """Tests for sensitive function detection."""

    def test_payment_functions(self):
        assert is_sensitive_function("process_payment") is True
        assert is_sensitive_function("handle_payment") is True
        assert is_sensitive_function("pay_invoice") is True

    def test_auth_functions(self):
        assert is_sensitive_function("authenticate_user") is True
        assert is_sensitive_function("login") is True
        assert is_sensitive_function("verify_password") is True

    def test_sensitive_data_functions(self):
        assert is_sensitive_function("get_api_key") is True
        assert is_sensitive_function("decrypt_token") is True
        assert is_sensitive_function("validate_secret") is True

    def test_non_sensitive_functions(self):
        assert is_sensitive_function("get_user") is False
        assert is_sensitive_function("format_date") is False
        assert is_sensitive_function("calculate_total") is False


class TestAnalyzeFile:
    """Tests for single file analysis."""

    def test_analyze_python_file(self, temp_dir):
        # Create a Python file
        py_file = temp_dir / "test.py"
        py_file.write_text('''"""Module docstring."""

import os
from pathlib import Path

# A comment
def greet(name):
    """Greet someone."""
    return f"Hello, {name}!"

def add(a, b):
    return a + b

class Calculator:
    def multiply(self, a, b):
        return a * b
''')

        files = scan_codebase(str(temp_dir))
        assert len(files) == 1

        analysis = analyze_file(files[0])
        assert analysis is not None

        # Check line counts
        assert analysis.total_lines > 0
        assert analysis.code_lines > 0
        assert analysis.comment_lines >= 0
        assert analysis.blank_lines >= 0

        # Check functions detected
        assert analysis.function_count >= 2  # greet, add, multiply

        # Check classes detected
        assert analysis.class_count >= 1  # Calculator

        # Check imports detected
        assert analysis.import_count >= 2  # os, Path

    def test_analyze_file_with_todos(self, temp_dir):
        py_file = temp_dir / "todo.py"
        py_file.write_text('''
def foo():
    # TODO: Implement this
    pass

def bar():
    # FIXME: This is broken
    pass
''')

        files = scan_codebase(str(temp_dir))
        analysis = analyze_file(files[0])

        assert analysis.todo_count == 2
        assert any("Implement" in content for _, content in analysis.todos)
        assert any("broken" in content for _, content in analysis.todos)

    def test_analyze_file_with_error_handling(self, temp_dir):
        py_file = temp_dir / "errors.py"
        py_file.write_text('''
def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
''')

        files = scan_codebase(str(temp_dir))
        analysis = analyze_file(files[0])

        assert analysis.has_error_handling is True

    def test_analyze_file_without_error_handling(self, temp_dir):
        py_file = temp_dir / "unsafe.py"
        py_file.write_text('''
def divide(a, b):
    return a / b
''')

        files = scan_codebase(str(temp_dir))
        analysis = analyze_file(files[0])

        assert analysis.has_error_handling is False

    def test_sensitive_function_detection(self, temp_dir):
        py_file = temp_dir / "auth.py"
        py_file.write_text('''
def authenticate_user(username, password):
    pass

def process_payment(amount):
    pass

def get_data():
    pass
''')

        files = scan_codebase(str(temp_dir))
        analysis = analyze_file(files[0])

        sensitive = analysis.sensitive_functions
        assert len(sensitive) >= 2
        names = [f.name for f in sensitive]
        assert "authenticate_user" in names
        assert "process_payment" in names


class TestAnalyzeFiles:
    """Tests for analyzing multiple files."""

    def test_analyze_healthy_project(self, healthy_project):
        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)

        assert len(analyses) > 0

        # All analyses should be FileAnalysis objects
        for analysis in analyses:
            assert isinstance(analysis, FileAnalysis)

    def test_analyze_mixed_languages(self, mixed_languages_project):
        files = scan_codebase(str(mixed_languages_project))
        analyses = analyze_files(files)

        # Should analyze files from multiple languages
        languages = set(a.source_file.language for a in analyses)
        assert len(languages) > 1

    def test_analyze_empty_project(self, empty_project):
        files = scan_codebase(str(empty_project))
        analyses = analyze_files(files)
        assert len(analyses) == 0


class TestFunctionInfo:
    """Tests for FunctionInfo properties."""

    def test_is_long_property(self):
        short_func = FunctionInfo(
            name="short", start_line=1, end_line=10, line_count=10
        )
        assert short_func.is_long is False

        long_func = FunctionInfo(
            name="long", start_line=1, end_line=100, line_count=100
        )
        assert long_func.is_long is True

    def test_is_sensitive_property(self):
        sensitive_func = FunctionInfo(
            name="process_payment",
            start_line=1,
            end_line=10,
            line_count=10,
            is_sensitive=True,
        )
        assert sensitive_func.is_sensitive is True


class TestFileAnalysisProperties:
    """Tests for FileAnalysis computed properties."""

    def test_long_functions_property(self, temp_dir):
        py_file = temp_dir / "long.py"
        # Create a file with a long function
        lines = ["def very_long_function():"]
        lines.extend(["    x = 1" for _ in range(100)])
        py_file.write_text("\n".join(lines))

        files = scan_codebase(str(temp_dir))
        analysis = analyze_file(files[0])

        long_funcs = analysis.long_functions
        assert len(long_funcs) > 0
