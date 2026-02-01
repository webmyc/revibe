"""
Verbose tests for fixer module to ensure high quality prompts and increase test volume.
"""

from unittest.mock import MagicMock

import pytest

from revibe.analyzer import FileAnalysis, FunctionInfo, SourceFile
from revibe.fixer import FixerEngine
from revibe.metrics import CodebaseMetrics, DuplicateGroup


@pytest.fixture
def fixer_metrics():
    """Create a metrics object that triggers all fix types."""
    source_file = SourceFile(MagicMock(), "src/main.py", "Python", False, 1000)
    analysis = FileAnalysis(
        source_file=source_file,
        total_lines=200,
        code_lines=150,
        comment_lines=10,
        blank_lines=40,
        functions=[
            FunctionInfo("long_func", 1, 100, 99),
            FunctionInfo("sensitive_func", 101, 150, 49, is_sensitive=True)
        ],
        classes=[],
        imports=[],
        todos=[(10, "TODO: fix critical bug")],
        string_literals=[],
        has_error_handling=False
    )

    metrics = CodebaseMetrics()
    metrics.file_analyses = [analysis]
    metrics.source_loc = 15000 # Trigger size fix
    metrics.test_loc = 100 # Trigger test fix (low ratio)
    metrics.test_to_code_ratio = 100 / 15000
    metrics.sensitive_functions_without_error_handling = [("src/main.py", analysis.functions[1])]
    metrics.long_functions = [("src/main.py", analysis.functions[0])]
    metrics.duplicate_groups = [DuplicateGroup(files=["a.py", "b.py"], is_exact=True)]
    metrics.ai_smell_scores = {"excessive_comments": 0.8}
    metrics.todos = [("src/main.py", 10, "TODO: fix critical bug")]
    metrics.health_score = 40
    metrics.risk_level = "HIGH"

    return metrics

class TestFixerPromptsVerbose:
    """Detailed prompt content verification."""

    def test_critical_test_fix_prompt(self, fixer_metrics):
        """Verify critical test fix prompt content."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)

        fix = next(f for f in plan.fixes if "Add Tests" in f.title)
        assert fix.priority == "CRITICAL"

        # Check specific instructions in prompt
        prompt = fix.prompt
        assert "Analyze this codebase and generate comprehensive test files" in prompt
        assert "critical modules that currently have ZERO test coverage" in prompt
        assert "1. Tests happy path for each function" in prompt
        assert "2. Tests edge cases" in prompt
        assert "3. Tests error conditions" in prompt
        assert "4. Uses pytest fixtures" in prompt

        # Check context
        assert "src/main.py" in prompt
        assert "long_func" in prompt

    def test_sensitive_error_fix_prompt(self, fixer_metrics):
        """Verify error handling fix prompt."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)

        fix = next(f for f in plan.fixes if "lack error handling" in f.title)

        prompt = fix.prompt.lower()
        assert "handle sensitive operations" in prompt
        assert "security and reliability risk" in prompt
        assert "input validation" in prompt
        assert "try/except blocks" in prompt
        assert "logging of errors" in prompt

        assert "sensitive_func" in fix.prompt
        assert "src/main.py" in fix.prompt

    def test_duplicate_fix_prompt(self, fixer_metrics):
        """Verify duplicate fix prompt."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)

        fix = next(f for f in plan.fixes if "duplicate file groups" in f.title)

        assert "Consolidate them to reduce maintenance" in fix.prompt
        assert "Identify the most complete/canonical version" in fix.prompt
        assert "Delete the duplicate files" in fix.prompt
        assert "Update all imports" in fix.prompt

        assert "a.py" in fix.prompt
        assert "b.py" in fix.prompt

    def test_long_function_fix_prompt(self, fixer_metrics):
        """Verify refactoring prompt."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)

        fix = next(f for f in plan.fixes if "long functions" in f.title)

        assert "too long and should be refactored" in fix.prompt
        assert "Identify logical sections" in fix.prompt
        assert "Create well-named helper functions" in fix.prompt
        assert "Keep the original function as a coordinator" in fix.prompt

        assert "long_func" in fix.prompt
        assert "99 lines" in fix.prompt

    def test_smell_fix_prompt(self, fixer_metrics):
        """Verify code smell prompt."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)

        fix = next(f for f in plan.fixes if "AI code smell" in f.title)

        assert "excessive_comments" in fix.prompt
        assert "Remove obvious/redundant comments" in fix.prompt # Check instruction exists

    def test_size_optimization_prompt(self, fixer_metrics):
        """Verify optimization prompt."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)

        fix = next(f for f in plan.fixes if "optimization" in f.title)

        assert "Remove dead code" in fix.prompt
        assert "Consolidate utilities" in fix.prompt
        assert "15,000" in fix.prompt # LOC count

class TestFixerRenderingVerbose:
    """Detailed rendering tests."""

    def test_render_cursor_rules_content(self, fixer_metrics):
        """Verify cursor rules content."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)
        rules = engine.render_cursor_rules(plan)

        assert "# Revibe Rules" in rules
        assert "HIGH RISK" in rules

        # Check rule generation
        assert "- ALWAYS add tests" in rules or "ALWAYS" in rules
        assert "DO NOT add new features" in rules # For low health score (40)

        # Check specific fixes mentioned
        assert "error handling" in rules.lower()

    def test_render_claude_md_content(self, fixer_metrics):
        """Verify CLAUDE.md content."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)
        md = engine.render_claude_md(plan)

        assert "Code Health Notes (Revibe)" in md
        assert "Health score: 40/100" in md
        assert "**Add Tests**" in md or "Add Tests" in md
        assert "critical issues detected" not in md

    def test_render_markdown_content(self, fixer_metrics):
        """Verify full markdown report."""
        engine = FixerEngine(".")
        plan = engine.generate_fixes(fixer_metrics)
        md = engine.render_markdown(plan)

        assert "# Revibe Fix Instructions" in md
        assert "> Codebase: ." in md
        assert "40/100" in md

        # Check sections exist
        assert "## 🔴 CRITICAL" in md
        assert "### Prompt 1:" in md
        assert "```" in md
        assert "**Affected files:**" in md
        assert "- `src/main.py`" in md
