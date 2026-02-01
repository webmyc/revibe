"""Tests for report generation modules."""

import json

import pytest

from revibe.fixer import FixerEngine, generate_fix_plan
from revibe.report_html import generate_html_report
from revibe.report_json import render_json_report
from revibe.report_terminal import print_terminal_report


class TestHtmlReport:
    """Tests for HTML report generation."""

    def test_generates_valid_html(self, healthy_project):
        """HTML report should contain expected sections and be valid HTML."""
        from revibe.analyzer import analyze_files
        from revibe.duplicates import find_all_duplicates
        from revibe.metrics import aggregate_metrics
        from revibe.scanner import scan_codebase
        from revibe.smells import detect_all_smells

        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)
        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        html = generate_html_report(metrics, str(healthy_project))
        assert "<html" in html
        assert "</html>" in html
        assert "Revibe Report" in html
        assert "revibe.help" in html

    def test_includes_fix_section(self, bloated_project):
        """HTML report should include fix instructions."""
        from revibe.analyzer import analyze_files
        from revibe.duplicates import find_all_duplicates
        from revibe.metrics import aggregate_metrics
        from revibe.scanner import scan_codebase
        from revibe.smells import detect_all_smells

        files = scan_codebase(str(bloated_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)
        metrics = aggregate_metrics(files, analyses, smells, duplicates)
        fix_plan = generate_fix_plan(str(bloated_project), metrics)

        html = generate_html_report(metrics, str(bloated_project), fix_plan=fix_plan)
        assert "Fix" in html or "fix" in html

    def test_escapes_html_in_path(self, healthy_project):
        """HTML report should escape special characters in paths."""
        from revibe.analyzer import analyze_files
        from revibe.duplicates import find_all_duplicates
        from revibe.metrics import aggregate_metrics
        from revibe.scanner import scan_codebase
        from revibe.smells import detect_all_smells

        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)
        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        # Should not crash with special path
        html = generate_html_report(metrics, "/path/<with>/special&chars")
        assert "&lt;with&gt;" in html
        assert "&amp;chars" in html


class TestJsonReport:
    """Tests for JSON report generation."""

    def test_is_valid_json(self, healthy_project):
        """JSON report should be parseable JSON with expected keys."""
        from revibe.analyzer import analyze_files
        from revibe.duplicates import find_all_duplicates
        from revibe.metrics import aggregate_metrics
        from revibe.scanner import scan_codebase
        from revibe.smells import detect_all_smells

        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)
        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        result = render_json_report(metrics, str(healthy_project))
        data = json.loads(result)

        # JSON has nested structure
        assert "summary" in data
        assert "health_score" in data["summary"]
        assert "risk_level" in data["summary"]
        assert "source_loc" in data["summary"]
        assert "test_to_code_ratio" in data["summary"]

    def test_contains_smells(self, bloated_project):
        """JSON report should include smell scores."""
        from revibe.analyzer import analyze_files
        from revibe.duplicates import find_all_duplicates
        from revibe.metrics import aggregate_metrics
        from revibe.scanner import scan_codebase
        from revibe.smells import detect_all_smells

        files = scan_codebase(str(bloated_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)
        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        result = render_json_report(metrics, str(bloated_project))
        data = json.loads(result)

        assert "ai_smell_scores" in data
        assert isinstance(data["ai_smell_scores"], dict)


class TestTerminalReport:
    """Tests for terminal report generation."""

    def test_runs_without_error(self, healthy_project, capsys):
        """Terminal report should not crash."""
        from revibe.analyzer import analyze_files
        from revibe.duplicates import find_all_duplicates
        from revibe.metrics import aggregate_metrics
        from revibe.scanner import scan_codebase
        from revibe.smells import detect_all_smells

        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)
        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        # Should not raise
        print_terminal_report(metrics, "0.1.0")
        captured = capsys.readouterr()
        assert "Health Score" in captured.out

    def test_plain_mode(self, healthy_project, capsys):
        """Terminal report should work in plain mode."""
        from revibe.analyzer import analyze_files
        from revibe.duplicates import find_all_duplicates
        from revibe.metrics import aggregate_metrics
        from revibe.scanner import scan_codebase
        from revibe.smells import detect_all_smells

        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)
        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        print_terminal_report(metrics, "0.1.0", force_plain=True)
        captured = capsys.readouterr()
        assert "Health Score" in captured.out
