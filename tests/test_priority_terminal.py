"""
Verbose tests for terminal reporting to increase test volume and coverage ratio.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from revibe.report_terminal import (
    print_terminal_report, 
    print_terminal_report_plain, 
    print_terminal_report_rich,
    get_risk_color,
    get_risk_emoji
)
from revibe.metrics import CodebaseMetrics, DuplicateGroup
from revibe.fixer import FixPlan, Fix

@pytest.fixture
def verbose_metrics():
    return CodebaseMetrics(
        total_files=100,
        source_files=80,
        test_files=20,
        source_loc=8000,
        test_loc=2000,
        health_score=65,
        risk_level="MODERATE",
        estimated_defects=200,
        feature_count=10,
        # feature_interactions=1023, # Calculated property
        ai_smell_scores={"bloated_code": 0.7, "magic_numbers": 0.6},
        duplicate_groups=[
            DuplicateGroup(files=["a.py", "b.py"], is_exact=True),
            DuplicateGroup(files=["c.py", "d.py"], is_exact=False, similarity=0.8)
        ],
        test_to_code_ratio=0.25
    )

class TestRiskHelpersVerbose:
    """Exhaustive tests for risk helpers."""

    def test_get_risk_color_exhaustive(self):
        assert get_risk_color("LOW") == "green"
        assert get_risk_color("MODERATE") == "yellow"
        assert get_risk_color("ELEVATED") == "orange1"
        assert get_risk_color("HIGH") == "red"
        assert get_risk_color("CRITICAL") == "bold red"
        assert get_risk_color("UNKNOWN") == "white"
        assert get_risk_color("") == "white"

    def test_get_risk_emoji_exhaustive(self):
        assert get_risk_emoji("LOW") == "🟢"
        assert get_risk_emoji("MODERATE") == "🟡"
        assert get_risk_emoji("ELEVATED") == "🟠"
        assert get_risk_emoji("HIGH") == "🔴"
        assert get_risk_emoji("CRITICAL") == "🔴"
        assert get_risk_emoji("UNKNOWN") == "⚪"

class TestTerminalReportPlainVerbose:
    """Verbose output verification for plain text report."""

    def test_plain_report_structure(self, capsys, verbose_metrics):
        """Verify every line of the plain report."""
        with patch("revibe.fixer.generate_fix_plan") as mock_plan:
            mock_plan.return_value = FixPlan(
                fixes=[
                    Fix(priority="CRITICAL", title="Fix Critical", description="d", prompt="p"),
                    Fix(priority="HIGH", title="Fix High", description="d", prompt="p"),
                    Fix(priority="MEDIUM", title="Fix Medium", description="d", prompt="p"),
                    Fix(priority="LOW", title="Fix Low", description="d", prompt="p"),
                ],
                codebase_path=".", health_score=65, risk_level="MODERATE", generated_at="now"
            )
            
            print_terminal_report_plain(verbose_metrics, "0.1.0")
            
        captured = capsys.readouterr()
        out = captured.out
        
        # Header
        assert "🔍 Revibe v0.1.0 — Scan Complete" in out
        
        # Box
        assert "╭─────────────────────────────────────╮" in out
        assert "│     Health Score:  65 / 100          │" in out
        assert "│     Risk Level:   🟡 MODERATE       │" in out
        assert "╰─────────────────────────────────────╯" in out
        
        # Metrics
        assert "Source Code:    8,000 lines (80 files)" in out
        assert "Test Code:      2,000 lines (20 files)" in out
        assert "Test Ratio:     25.0% ⚠️ (target: ≥80%)" in out
        assert "Est. Defects:   ~200 bugs hiding in your code" in out
        
        # Duplicates
        assert "Duplicates:     2 groups (redundant code)" in out
        
        # Smells
        assert "AI Smells:      2 of 8 detected" in out
        
        # Fixes logic (top 3)
        assert "Top Fixes:" in out
        assert "🔴 CRITICAL  Fix Critical" in out
        assert "🟠 HIGH      Fix High" in out
        assert "🟡 MEDIUM    Fix Medium" in out
        assert "🟢 LOW" not in out # Should be cut off after top 3

        # Call to action
        assert "Run `revibe scan . --fix`" in out
        assert "Run `revibe scan . --html`" in out

    def test_plain_top_fixes_empty(self, capsys, verbose_metrics):
        """Verify no fixes section if empty."""
        with patch("revibe.fixer.generate_fix_plan") as mock_plan:
            mock_plan.return_value = FixPlan(fixes=[], codebase_path=".", health_score=65, risk_level="MODERATE", generated_at="now")
            print_terminal_report_plain(verbose_metrics, "0.1.0")
            
        out = capsys.readouterr().out
        assert "Top Fixes:" not in out

class TestTerminalReportRichVerbose:
    """Verbose verification for rich output calls."""
    
    @patch("revibe.report_terminal.Console")
    @patch("revibe.report_terminal.Panel")
    @patch("revibe.report_terminal.Table")
    def test_rich_calls_sequence(self, mock_table, mock_panel, mock_console, verbose_metrics):
        """Verify sequence of rich object creation."""
        
        # Setup table mock
        table_instance = mock_table.return_value
        
        # Run
        print_terminal_report_rich(verbose_metrics, "0.1.0")
        
        # Verify console prints
        c_prints = mock_console.return_value.print.call_args_list
        # Expect at least: header, panel, table, fixes header, fix1, fix2, fix3, footer
        assert len(c_prints) >= 10
        
        # Verify Panel creation
        mock_panel.assert_called_once()
        args, kwargs = mock_panel.call_args
        assert kwargs.get("title") == "Codebase Health"
        assert kwargs.get("border_style") == "yellow" # MODERATE

        # Verify Table rows
        # We expect add_row calls
        row_calls = table_instance.add_row.call_args_list
        
        # 1. Source Code
        assert "Source Code:" in row_calls[0][0][0]
        # 2. Test Code
        assert "Test Code:" in row_calls[1][0][0]
        # 3. Test Ratio
        assert "Test Ratio:" in row_calls[2][0][0]
        # 4. Defects
        assert "Est. Defects:" in row_calls[3][0][0]
        # 5. Features
        assert "Features:" in row_calls[4][0][0]
        # 6. Duplicates
        assert "Duplicates:" in row_calls[5][0][0]
        # 7. Smells
        assert "AI Smells:" in row_calls[6][0][0]

    @patch("revibe.report_terminal.RICH_AVAILABLE", False)
    @patch("revibe.report_terminal.print_terminal_report_plain")
    @patch("revibe.report_terminal.print_terminal_report_rich")
    def test_fallback_logic(self, mock_rich, mock_plain, verbose_metrics):
        """Verify fallback when rich is not available."""
        print_terminal_report(verbose_metrics, "0.1.0")
        mock_rich.assert_not_called()
        mock_plain.assert_called_once()

    @patch("revibe.report_terminal.RICH_AVAILABLE", True)
    @patch("revibe.report_terminal.print_terminal_report_plain")
    @patch("revibe.report_terminal.print_terminal_report_rich")
    def test_force_plain_logic(self, mock_rich, mock_plain, verbose_metrics):
        """Verify force_plain argument."""
        print_terminal_report(verbose_metrics, "0.1.0", force_plain=True)
        mock_rich.assert_not_called()
        mock_plain.assert_called_once()
