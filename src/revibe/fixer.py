"""
Fixer Engine — THE KEY DIFFERENTIATOR.

Generates AI-ready fix instructions that users can copy-paste into
Cursor, Claude, Copilot, or any AI coding tool.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from revibe import __version__
from revibe.metrics import CodebaseMetrics, DuplicateGroup
from revibe.smells import get_smell_descriptions


@dataclass
class Fix:
    """A single fix instruction."""

    priority: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    title: str
    description: str
    prompt: str  # The copy-paste prompt for AI tools
    affected_files: List[str] = field(default_factory=list)
    verification: str = ""  # How to verify the fix worked


@dataclass
class FixPlan:
    """Complete fix plan for a codebase."""

    fixes: List[Fix]
    codebase_path: str
    health_score: int
    risk_level: str
    generated_at: str
    version: str = __version__

    @property
    def critical_fixes(self) -> List[Fix]:
        return [f for f in self.fixes if f.priority == "CRITICAL"]

    @property
    def high_fixes(self) -> List[Fix]:
        return [f for f in self.fixes if f.priority == "HIGH"]

    @property
    def medium_fixes(self) -> List[Fix]:
        return [f for f in self.fixes if f.priority == "MEDIUM"]

    @property
    def low_fixes(self) -> List[Fix]:
        return [f for f in self.fixes if f.priority == "LOW"]


class FixerEngine:
    """Generate AI-ready fix instructions from audit results."""

    def __init__(self, codebase_path: str):
        self.codebase_path = codebase_path

    def generate_fixes(self, metrics: CodebaseMetrics) -> FixPlan:
        """Analyze metrics and generate prioritized fix instructions."""
        fixes = []

        # Critical: Test coverage
        if metrics.test_to_code_ratio < 0.1:
            fix = self._generate_test_fix_critical(metrics)
            if fix:
                fixes.append(fix)
        elif metrics.test_to_code_ratio < 0.5:
            fix = self._generate_test_fix_moderate(metrics)
            if fix:
                fixes.append(fix)

        # Critical: Missing error handling in sensitive functions
        if metrics.sensitive_functions_without_error_handling:
            fix = self._generate_error_handling_fix(metrics)
            if fix:
                fixes.append(fix)

        # High: Duplicates
        if metrics.duplicate_groups:
            fix = self._generate_duplicate_fix(metrics.duplicate_groups)
            if fix:
                fixes.append(fix)

        # High: Long functions
        if metrics.long_functions:
            fix = self._generate_long_function_fix(metrics)
            if fix:
                fixes.append(fix)

        # Medium: High AI smells
        high_smells = {k: v for k, v in metrics.ai_smell_scores.items() if v > 0.5}
        if high_smells:
            fix = self._generate_smell_fix(high_smells, metrics)
            if fix:
                fixes.append(fix)

        # Low: TODOs
        if len(metrics.todos) > 5:
            fix = self._generate_todo_triage(metrics)
            if fix:
                fixes.append(fix)

        # Low: Large codebase optimization
        if metrics.source_loc > 10000:
            fix = self._generate_size_optimization_fix(metrics)
            if fix:
                fixes.append(fix)

        return FixPlan(
            fixes=fixes,
            codebase_path=self.codebase_path,
            health_score=metrics.health_score,
            risk_level=metrics.risk_level,
            generated_at=datetime.now().isoformat(),
        )

    def _generate_test_fix_critical(self, metrics: CodebaseMetrics) -> Optional[Fix]:
        """Generate fix for critically low test coverage."""
        ratio_pct = metrics.test_to_code_ratio * 100

        # Find files with most functions but no tests
        untested_files = []
        for analysis in metrics.file_analyses:
            if not analysis.source_file.is_test and analysis.functions:
                untested_files.append({
                    "path": analysis.source_file.relative_path,
                    "functions": [f.name for f in analysis.functions],
                    "func_count": len(analysis.functions),
                })

        untested_files.sort(key=lambda x: x["func_count"], reverse=True)
        top_files = untested_files[:5]

        if not top_files:
            return None

        file_list = "\n".join(
            f"- {f['path']} ({f['func_count']} functions, 0 tests) — Focus on: {', '.join(f['functions'][:3])}"
            for f in top_files
        )

        prompt = f"""Analyze this codebase and generate comprehensive test files for the following
critical modules that currently have ZERO test coverage:

{file_list}

For each module, create a test file in tests/ that:
1. Tests happy path for each function
2. Tests edge cases (null inputs, invalid data, boundary values)
3. Tests error conditions
4. Uses pytest fixtures for shared setup
5. Includes at least 3 test cases per function

Start with {top_files[0]['path']} as it has the most untested functions."""

        return Fix(
            priority="CRITICAL",
            title="Add Tests (you have almost none)",
            description=f"Your codebase has {metrics.source_loc} lines of source code and only "
                        f"{metrics.test_loc} lines of tests ({ratio_pct:.1f}% ratio). "
                        f"The recommended minimum is 80%.",
            prompt=prompt,
            affected_files=[f["path"] for f in top_files],
            verification="After applying, run: pytest --cov to verify coverage improved",
        )

    def _generate_test_fix_moderate(self, metrics: CodebaseMetrics) -> Optional[Fix]:
        """Generate fix for moderately low test coverage."""
        ratio_pct = metrics.test_to_code_ratio * 100
        target_tests = int(metrics.source_loc * 0.8) - metrics.test_loc

        # Find specific functions without tests
        untested_funcs = []
        for analysis in metrics.file_analyses:
            if not analysis.source_file.is_test:
                for func in analysis.functions:
                    untested_funcs.append({
                        "file": analysis.source_file.relative_path,
                        "name": func.name,
                        "lines": func.line_count,
                    })

        untested_funcs.sort(key=lambda x: x["lines"], reverse=True)
        top_funcs = untested_funcs[:10]

        if not top_funcs:
            return None

        func_list = "\n".join(
            f"- {f['file']}: {f['name']}() ({f['lines']} lines)"
            for f in top_funcs
        )

        prompt = f"""Improve test coverage for this codebase. Current coverage is {ratio_pct:.1f}%.
Target is 80%. You need approximately {target_tests} more lines of test code.

Priority functions to test (longest/most complex):

{func_list}

For each function:
1. Create a test file if one doesn't exist
2. Add tests for normal operation
3. Add tests for edge cases
4. Add tests for error handling"""

        return Fix(
            priority="HIGH",
            title="Improve Test Coverage",
            description=f"Test coverage is {ratio_pct:.1f}%. Target is 80%. "
                        f"Add ~{target_tests} lines of test code.",
            prompt=prompt,
            affected_files=list(set(f["file"] for f in top_funcs)),
            verification="Run: pytest --cov to check coverage percentage",
        )

    def _generate_error_handling_fix(self, metrics: CodebaseMetrics) -> Optional[Fix]:
        """Generate fix for sensitive functions without error handling."""
        sensitive = metrics.sensitive_functions_without_error_handling[:5]

        if not sensitive:
            return None

        func_list = "\n".join(
            f"- {file}: {func.name}() (lines {func.start_line}-{func.end_line})"
            for file, func in sensitive
        )

        first_file, first_func = sensitive[0]

        prompt = f"""The following functions handle sensitive operations but have NO error handling.
This is a security and reliability risk.

{func_list}

For each function, add:
1. Input validation (check for null/empty/invalid inputs)
2. Try/except blocks around risky operations
3. Logging of errors for debugging
4. User-friendly error messages
5. Proper error response codes (if applicable)

Start with {first_func.name}() in {first_file} — this handles sensitive operations
and MUST have comprehensive error handling."""

        return Fix(
            priority="CRITICAL",
            title=f"{len(sensitive)} sensitive functions lack error handling",
            description="Functions handling payments, auth, or sensitive data have no "
                        "try/catch or input validation. This is a security risk.",
            prompt=prompt,
            affected_files=list(set(f for f, _ in sensitive)),
            verification="Review each function for try/except blocks and input validation",
        )

    def _generate_duplicate_fix(self, duplicate_groups: List[DuplicateGroup]) -> Optional[Fix]:
        """Generate fix for duplicate files."""
        if not duplicate_groups:
            return None

        exact_groups = [g for g in duplicate_groups if g.is_exact]
        near_groups = [g for g in duplicate_groups if not g.is_exact]

        group_desc = []
        for i, group in enumerate(exact_groups[:3], 1):
            files = "\n  - ".join(group.files)
            group_desc.append(f"Exact copy group {i}:\n  - {files}")

        for group in near_groups[:2]:
            group_desc.append(
                f"Near-duplicate ({group.similarity:.0%} similar):\n  - {group.files[0]}\n  - {group.files[1]}"
            )

        groups_text = "\n\n".join(group_desc)

        prompt = f"""The following files are duplicates or near-duplicates of each other.
Consolidate them to reduce maintenance burden and potential bugs.

{groups_text}

For each group:
1. Identify the most complete/canonical version
2. Delete the duplicate files
3. Update all imports/references to point to the canonical file
4. Verify no functionality is lost
5. Run tests to confirm nothing broke"""

        all_files = []
        for g in duplicate_groups:
            all_files.extend(g.files)

        return Fix(
            priority="HIGH",
            title=f"Remove {len(duplicate_groups)} duplicate file groups",
            description="These files are copies of each other. Consolidate to reduce confusion.",
            prompt=prompt,
            affected_files=all_files[:10],
            verification="Search for any broken imports after consolidating",
        )

    def _generate_long_function_fix(self, metrics: CodebaseMetrics) -> Optional[Fix]:
        """Generate fix for overly long functions."""
        long_funcs = metrics.long_functions[:5]

        if not long_funcs:
            return None

        func_list = "\n".join(
            f"- {file}: {func.name}() — {func.line_count} lines (lines {func.start_line}-{func.end_line})"
            for file, func in long_funcs
        )

        first_file, first_func = long_funcs[0]

        prompt = f"""The following functions are too long and should be refactored.
Long functions are harder to test, maintain, and debug.

{func_list}

For each function:
1. Identify logical sections that can be extracted into helper functions
2. Create well-named helper functions for each section
3. Keep the original function as a coordinator that calls the helpers
4. Ensure each new function does ONE thing
5. Add docstrings to new functions
6. Keep each function under 50 lines

Start with {first_func.name}() in {first_file} — it's {first_func.line_count} lines long."""

        return Fix(
            priority="MEDIUM",
            title=f"Refactor {len(long_funcs)} long functions",
            description="Functions over 80 lines are hard to test and maintain. Break them up.",
            prompt=prompt,
            affected_files=list(set(f for f, _ in long_funcs)),
            verification="Each function should be under 50 lines after refactoring",
        )

    def _generate_smell_fix(
        self,
        high_smells: dict,
        metrics: CodebaseMetrics,
    ) -> Optional[Fix]:
        """Generate fix for high AI smell scores."""
        descriptions = get_smell_descriptions()

        smell_details = []
        for smell, score in sorted(high_smells.items(), key=lambda x: -x[1]):
            desc = descriptions.get(smell, smell)
            smell_details.append(f"- {smell} ({score:.0%}): {desc}")

        smell_text = "\n".join(smell_details)

        prompt = f"""This codebase has patterns commonly found in AI-generated code that may
indicate quality issues. Review and address these patterns:

{smell_text}

For each smell:

1. **excessive_comments**: Remove obvious/redundant comments. Keep only comments that
   explain WHY, not WHAT.

2. **verbose_naming**: Shorten overly long names while keeping them descriptive.
   Example: handleUserAuthenticationWithPasswordAndTwoFactorVerification -> authenticateUser

3. **boilerplate_heavy**: Remove unused imports. Consolidate similar imports.

4. **inconsistent_patterns**: Pick one naming convention per language and apply consistently.
   Python: snake_case. JavaScript: camelCase.

5. **dead_code_indicators**: Find and consolidate duplicate function implementations.

6. **over_engineering**: Simplify class hierarchies. Not everything needs to be a class.

7. **missing_error_handling**: Add try/except blocks to functions that do I/O or API calls.

8. **copy_paste_artifacts**: Extract repeated strings into constants or config files."""

        return Fix(
            priority="MEDIUM",
            title=f"Address {len(high_smells)} AI code smell patterns",
            description="The code shows patterns commonly found in AI-generated code. "
                        "Review and clean up these areas.",
            prompt=prompt,
            affected_files=[],  # Codebase-wide
            verification="Run `revibe scan .` again and check if smell scores decreased",
        )

    def _generate_todo_triage(self, metrics: CodebaseMetrics) -> Optional[Fix]:
        """Generate fix for TODO/FIXME triage."""
        todos = metrics.todos[:15]

        if not todos:
            return None

        todo_list = "\n".join(
            f"- {file}:{line}: {content[:60]}..."
            if len(content) > 60 else f"- {file}:{line}: {content}"
            for file, line, content in todos
        )

        prompt = f"""This codebase has {len(metrics.todos)} TODO/FIXME markers that need triage.
Here are the first {len(todos)}:

{todo_list}

For each TODO:
1. Determine if it's still relevant
2. If relevant: create an issue or fix it now
3. If not relevant: delete the comment
4. If it's a FIXME or BUG: prioritize fixing it immediately

Address critical TODOs (FIXME, BUG, HACK) first."""

        return Fix(
            priority="LOW",
            title=f"Triage {len(metrics.todos)} TODO/FIXME markers",
            description="These markers indicate unfinished or problematic code. "
                        "Review and address or remove them.",
            prompt=prompt,
            affected_files=list(set(f for f, _, _ in todos)),
            verification="Run `grep -r 'TODO\\|FIXME' .` to verify reduction",
        )

    def _generate_size_optimization_fix(self, metrics: CodebaseMetrics) -> Optional[Fix]:
        """Generate fix for large codebase optimization."""
        prompt = f"""This codebase has {metrics.source_loc:,} lines of code across {metrics.source_files} files.
Consider these optimizations:

1. **Remove dead code**: Search for functions/classes that are never called
2. **Consolidate utilities**: Merge similar utility functions
3. **Extract shared code**: If multiple files have similar code, create a shared module
4. **Review dependencies**: Are there large libraries being used for small tasks?
5. **Remove generated/bundled code**: Ensure build artifacts aren't committed

Run these commands to find candidates:
- Dead exports: Look for exported functions with no imports
- Large files: Find files over 500 lines that could be split
- Duplicate code: Use the Revibe duplicate detection results"""

        return Fix(
            priority="LOW",
            title="Consider codebase size optimization",
            description=f"At {metrics.source_loc:,} LOC, consider removing dead code and consolidating.",
            prompt=prompt,
            affected_files=[],
            verification="Track LOC over time. Aim for smaller but complete codebase.",
        )

    def render_markdown(self, plan: FixPlan) -> str:
        """Render fix plan as markdown with copy-paste prompts."""
        lines = [
            "# Revibe Fix Instructions",
            f"> Generated by Revibe v{plan.version} on {plan.generated_at[:10]}",
            f"> Codebase: {plan.codebase_path} | Health Score: {plan.health_score}/100 ({plan.risk_level} RISK)",
            "> Copy any section below into Cursor, Claude, or your AI coding tool.",
            "",
        ]

        if not plan.fixes:
            lines.append("✅ **No critical fixes needed!** Your codebase looks healthy.")
            return "\n".join(lines)

        prompt_num = 1

        priority_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }

        for fix in plan.fixes:
            emoji = priority_emoji.get(fix.priority, "⚪")
            lines.append(f"## {emoji} {fix.priority}: {fix.title}")
            lines.append("")
            lines.append(fix.description)
            lines.append("")

            if fix.affected_files:
                lines.append("**Affected files:**")
                for f in fix.affected_files[:5]:
                    lines.append(f"- `{f}`")
                if len(fix.affected_files) > 5:
                    lines.append(f"- ... and {len(fix.affected_files) - 5} more")
                lines.append("")

            lines.append(f"### Prompt {prompt_num}: {fix.title}")
            lines.append("```")
            lines.append(fix.prompt)
            lines.append("```")
            lines.append("")

            if fix.verification:
                lines.append(f"**Verification:** {fix.verification}")
                lines.append("")

            lines.append("---")
            lines.append("")
            prompt_num += 1

        return "\n".join(lines)

    def render_cursor_rules(self, plan: FixPlan) -> str:
        """Render as .cursorrules file."""
        lines = [
            "# Revibe Rules — Generated " + plan.generated_at[:10],
            f"# Health Score: {plan.health_score}/100 — {plan.risk_level} RISK",
            "",
            "## Priority fixes for this codebase:",
            "",
        ]

        # Add rules based on fixes
        for fix in plan.fixes[:5]:
            if fix.priority == "CRITICAL":
                lines.append(f"- ALWAYS {fix.title.lower()} before adding new features")
            elif fix.priority == "HIGH":
                lines.append(f"- PREFER fixing {fix.title.lower()} over adding new code")
            else:
                lines.append(f"- CONSIDER addressing: {fix.title}")

        # Add general rules based on health
        lines.append("")
        lines.append("## General rules:")
        lines.append("")

        if plan.health_score < 60:
            lines.append("- DO NOT add new features until existing issues are fixed")
            lines.append("- ALWAYS write tests for new functions")
            lines.append("- ALWAYS add error handling to new functions")
        else:
            lines.append("- PREFER writing tests alongside new code")
            lines.append("- PREFER small, focused functions over large ones")

        lines.append("- NEVER create duplicate files — check if similar code exists")
        lines.append("- PREFER consolidating into existing files over creating new ones")

        return "\n".join(lines)

    def render_claude_md(self, plan: FixPlan) -> str:
        """Render as CLAUDE.md section."""
        lines = [
            "## Code Health Notes (Revibe)",
            "",
            f"Health score: {plan.health_score}/100 ({plan.risk_level} risk). Key issues:",
            "",
        ]

        for fix in plan.fixes[:5]:
            # Create a one-liner summary
            summary = fix.description.split(".")[0] + "."
            lines.append(f"- **{fix.title}**: {summary}")

        if not plan.fixes:
            lines.append("- ✅ No critical issues detected")

        lines.append("")
        lines.append(f"_Generated by Revibe v{plan.version} on {plan.generated_at[:10]}_")

        return "\n".join(lines)


def generate_fix_plan(
    codebase_path: str,
    metrics: CodebaseMetrics,
) -> FixPlan:
    """
    Generate a complete fix plan for a codebase.

    Args:
        codebase_path: Path to the codebase
        metrics: Aggregated codebase metrics

    Returns:
        FixPlan with prioritized fixes
    """
    engine = FixerEngine(codebase_path)
    return engine.generate_fixes(metrics)
