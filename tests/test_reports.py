"""Tests for report generation modules."""

import json

from revibe.fixer import generate_fix_plan
from revibe.report_html import generate_html_report
from revibe.report_json import generate_json_report
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

    def test_get_styles_and_scripts(self, healthy_project):
        """Test internal helper functions for styles and scripts."""
        # Inspect the module internals via the public API or direct import if needed
        # Since they are private, we test them via the main function or direct import
        from revibe.report_html import _get_scripts, _get_styles

        styles = _get_styles()
        assert ":root" in styles
        assert "body {" in styles
        assert ".score-circle" in styles

        scripts = _get_scripts()
        assert "document.querySelectorAll" in scripts
        assert "addEventListener" in scripts

    def test_get_component_styles(self):
        """Test component styles generation."""
        from revibe.report_html import _get_component_styles
        styles = _get_component_styles()
        assert ".card" in styles
        assert ".score-circle" in styles
        assert ".risk-badge" in styles
        # Verify specific critical styles
        assert "conic-gradient" in styles
        assert "var(--danger)" in styles

    def test_get_layout_styles(self):
        """Test layout styles generation."""
        from revibe.report_html import _get_layout_styles
        styles = _get_layout_styles()
        assert ".container" in styles
        assert "header" in styles
        assert "footer" in styles
        assert "flex" in styles


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

        result = generate_json_report(metrics, str(healthy_project), analyses)
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

        result = generate_json_report(metrics, str(bloated_project), analyses)
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
