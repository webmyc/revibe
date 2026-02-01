"""Terminal report output for Revibe (with optional rich support)."""


from revibe.metrics import CodebaseMetrics

# Try to import rich for pretty output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def get_risk_color(risk_level: str) -> str:
    """Get color for risk level."""
    colors = {
        "LOW": "green",
        "MODERATE": "yellow",
        "ELEVATED": "orange1",
        "HIGH": "red",
        "CRITICAL": "bold red",
    }
    return colors.get(risk_level, "white")


def get_risk_emoji(risk_level: str) -> str:
    """Get emoji for risk level."""
    emojis = {
        "LOW": "🟢",
        "MODERATE": "🟡",
        "ELEVATED": "🟠",
        "HIGH": "🔴",
        "CRITICAL": "🔴",
    }
    return emojis.get(risk_level, "⚪")


def print_terminal_report_rich(metrics: CodebaseMetrics, version: str) -> None:
    """Print rich terminal report with colors and formatting."""
    console = Console()

    # Header
    console.print()
    console.print(f"[bold cyan]🔍 Revibe v{version}[/bold cyan] — Scan Complete")
    console.print()

    # Health score panel
    risk_color = get_risk_color(metrics.risk_level)
    risk_emoji = get_risk_emoji(metrics.risk_level)

    score_text = Text()
    score_text.append(f"Health Score: {metrics.health_score} / 100\n", style="bold")
    score_text.append(f"Risk Level:   {risk_emoji} {metrics.risk_level}", style=risk_color)

    console.print(Panel(
        score_text,
        title="Codebase Health",
        border_style=risk_color,
        width=40,
    ))
    console.print()

    # Metrics table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column(style="bold")
    table.add_column()

    # Code metrics
    test_ratio_pct = metrics.test_to_code_ratio * 100
    test_status = "⚠️" if test_ratio_pct < 50 else "✅" if test_ratio_pct >= 80 else ""

    table.add_row("Source Code:", f"{metrics.source_loc:,} lines", f"({metrics.source_files} files)")
    table.add_row("Test Code:", f"{metrics.test_loc:,} lines", f"({metrics.test_files} files)")
    table.add_row("Test Ratio:", f"{test_ratio_pct:.1f}%", f"{test_status} (target: ≥80%)")
    table.add_row("Est. Defects:", f"~{metrics.estimated_defects} bugs", "hiding in your code")
    table.add_row("Features:", f"{metrics.feature_count}", f"({metrics.feature_interactions:,} interaction paths)")

    if metrics.duplicate_groups:
        table.add_row("Duplicates:", f"{len(metrics.duplicate_groups)} groups", "(redundant code)")

    high_smells = sum(1 for s in metrics.ai_smell_scores.values() if s > 0.5)
    if high_smells:
        table.add_row("AI Smells:", f"{high_smells} of 8", "detected")

    console.print(table)
    console.print()

    # Top fixes
    from revibe.fixer import generate_fix_plan
    plan = generate_fix_plan(".", metrics)

    if plan.fixes:
        console.print("[bold]Top Fixes:[/bold]")
        for fix in plan.fixes[:3]:
            priority_colors = {
                "CRITICAL": "red",
                "HIGH": "orange1",
                "MEDIUM": "yellow",
                "LOW": "green",
            }
            color = priority_colors.get(fix.priority, "white")
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(fix.priority, "⚪")
            console.print(f"  {emoji} [bold {color}]{fix.priority}[/bold {color}]  {fix.title}")
        console.print()

    # Call to action
    console.print("[dim]Run [bold]revibe scan . --fix[/bold] to generate copy-paste fix instructions[/dim]")
    console.print("[dim]Run [bold]revibe scan . --html[/bold] for a detailed visual report[/dim]")
    console.print()


def print_terminal_report_plain(metrics: CodebaseMetrics, version: str) -> None:
    """Print plain text terminal report (no rich)."""
    print()
    print(f"🔍 Revibe v{version} — Scan Complete")
    print()

    # Health score box
    risk_emoji = get_risk_emoji(metrics.risk_level)
    print("╭─────────────────────────────────────╮")
    print(f"│     Health Score: {metrics.health_score:3d} / 100          │")
    print(f"│     Risk Level:   {risk_emoji} {metrics.risk_level:12s}   │")
    print("╰─────────────────────────────────────╯")
    print()

    # Metrics
    test_ratio_pct = metrics.test_to_code_ratio * 100
    test_status = "⚠️" if test_ratio_pct < 50 else "✅" if test_ratio_pct >= 80 else ""

    print(f"  Source Code:    {metrics.source_loc:,} lines ({metrics.source_files} files)")
    print(f"  Test Code:      {metrics.test_loc:,} lines ({metrics.test_files} files)")
    print(f"  Test Ratio:     {test_ratio_pct:.1f}% {test_status} (target: ≥80%)")
    print(f"  Est. Defects:   ~{metrics.estimated_defects} bugs hiding in your code")
    print(f"  Features:       {metrics.feature_count} ({metrics.feature_interactions:,} interaction paths)")

    if metrics.duplicate_groups:
        print(f"  Duplicates:     {len(metrics.duplicate_groups)} groups (redundant code)")

    high_smells = sum(1 for s in metrics.ai_smell_scores.values() if s > 0.5)
    if high_smells:
        print(f"  AI Smells:      {high_smells} of 8 detected")

    print()

    # Top fixes
    from revibe.fixer import generate_fix_plan
    plan = generate_fix_plan(".", metrics)

    if plan.fixes:
        print("  Top Fixes:")
        for fix in plan.fixes[:3]:
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(fix.priority, "⚪")
            print(f"  {emoji} {fix.priority:8s}  {fix.title}")
        print()

    # Call to action
    print("  Run `revibe scan . --fix` to generate copy-paste fix instructions")
    print("  Run `revibe scan . --html` for a detailed visual report")
    print()


def print_terminal_report(
    metrics: CodebaseMetrics,
    version: str,
    force_plain: bool = False,
) -> None:
    """
    Print terminal report with optional rich formatting.

    Args:
        metrics: Codebase metrics to report
        version: Revibe version string
        force_plain: Force plain text output even if rich is available
    """
    if RICH_AVAILABLE and not force_plain:
        print_terminal_report_rich(metrics, version)
    else:
        print_terminal_report_plain(metrics, version)
