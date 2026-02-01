"""Command-line interface for Revibe."""

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from revibe import __version__
from revibe.analyzer import FileAnalysis, analyze_files
from revibe.duplicates import DuplicateGroup, find_all_duplicates
from revibe.fixer import FixerEngine, generate_fix_plan
from revibe.metrics import CodebaseMetrics, aggregate_metrics
from revibe.report_html import generate_html_report
from revibe.report_json import generate_json_report
from revibe.report_terminal import print_terminal_report
from revibe.scanner import SourceFile, scan_codebase
from revibe.smells import detect_all_smells


@dataclass
class ScanResult:
    """Results from scanning a codebase."""

    source_files: list[SourceFile]
    analyses: list[FileAnalysis]
    smell_scores: dict
    duplicates: list[DuplicateGroup]
    metrics: CodebaseMetrics


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="revibe",
        description="🔍 Revibe — Codebase health scanner + AI-powered fixer for vibe-coded projects",
        epilog="Learn more at https://revibe.help",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"revibe {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a codebase for health issues",
        description="Scan a codebase and generate health reports with fix instructions",
    )

    _add_scan_arguments(scan_parser)
    return parser


def _add_scan_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the scan command."""
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the codebase to scan (default: current directory)",
    )

    # Output format options
    output_group = parser.add_argument_group("Output formats")
    output_group.add_argument("--html", action="store_true", help="Generate an HTML report")
    output_group.add_argument("--json", action="store_true", help="Output results as JSON to stdout")
    output_group.add_argument(
        "--fix", 
        action="store_true", 
        help="Generate REVIBE_FIXES.md with copy-paste AI fix instructions"
    )
    output_group.add_argument(
        "--cursor", 
        action="store_true", 
        help="Generate .cursorrules file with fix priorities"
    )
    output_group.add_argument(
        "--claude", 
        action="store_true", 
        help="Generate CLAUDE.md section with health notes"
    )
    output_group.add_argument(
        "--all", 
        action="store_true", 
        help="Generate all output formats (HTML + JSON + fix files)"
    )

    # Other options
    parser.add_argument(
        "--output", "-o", 
        type=str, 
        metavar="DIR", 
        help="Output directory for generated files (default: codebase root)"
    )
    parser.add_argument(
        "--ignore", 
        type=str, 
        metavar="DIRS", 
        help="Comma-separated list of additional directories to ignore"
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress terminal output (useful with --json)")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")


def _log(message: str, quiet: bool, json_mode: bool) -> None:
    """Print a log message if not in quiet/JSON mode."""
    if not quiet and not json_mode:
        print(message)


def _perform_scan(path: Path, additional_ignores: Optional[list[str]], quiet: bool, json_mode: bool) -> Optional[ScanResult]:
    """Perform the codebase scan and analysis."""
    _log("  Discovering files...", quiet, json_mode)
    source_files = scan_codebase(str(path), additional_ignores)

    if not source_files:
        if not quiet:
            print("  ⚠️ No source files found in this directory.")
        return None

    langs = {f.language for f in source_files}
    _log(f"  Found {len(source_files)} files across {len(langs)} languages", quiet, json_mode)

    _log("  Analyzing files...", quiet, json_mode)
    analyses = analyze_files(source_files)

    _log("  Detecting code smells...", quiet, json_mode)
    smell_scores = detect_all_smells(analyses)

    _log("  Finding duplicates...", quiet, json_mode)
    duplicates = find_all_duplicates(analyses)

    _log("  Calculating health score...", quiet, json_mode)
    metrics = aggregate_metrics(source_files, analyses, smell_scores, duplicates)

    return ScanResult(
        source_files=source_files,
        analyses=analyses,
        smell_scores=smell_scores,
        duplicates=duplicates,
        metrics=metrics,
    )


def _generate_fix_files(
    args: argparse.Namespace,
    output_dir: Path,
    path: str,
    metrics: CodebaseMetrics,
) -> None:
    """Generate fix instruction files (markdown, cursor rules, claude)."""
    fixer = FixerEngine(path)
    fix_plan = generate_fix_plan(path, metrics)

    if args.fix:
        fix_path = output_dir / "REVIBE_FIXES.md"
        try:
            fix_path.write_text(fixer.render_markdown(fix_plan), encoding="utf-8")
            if not args.quiet:
                print(f"  📝 Fix instructions: {fix_path}")
        except OSError as e:
            print(f"  ❌ Failed to write fixes to {fix_path}: {e}", file=sys.stderr)

    if args.cursor:
        cursor_path = output_dir / ".cursorrules"
        try:
            cursor_path.write_text(fixer.render_cursor_rules(fix_plan), encoding="utf-8")
            if not args.quiet:
                print(f"  🔧 Cursor rules: {cursor_path}")
        except OSError as e:
             print(f"  ❌ Failed to write .cursorrules to {cursor_path}: {e}", file=sys.stderr)

    if args.claude:
        claude_path = output_dir / "REVIBE_CLAUDE.md"
        try:
            claude_path.write_text(fixer.render_claude_md(fix_plan), encoding="utf-8")
            if not args.quiet:
                print(f"  🤖 Claude notes: {claude_path}")
        except OSError as e:
            print(f"  ❌ Failed to write Claude notes to {claude_path}: {e}", file=sys.stderr)


def run_scan(args: argparse.Namespace) -> int:
    """Run the scan command."""
    path = Path(args.path).resolve()

    # Validate path
    if not path.exists():
        print(f"❌ Error: Path does not exist: {path}", file=sys.stderr)
        return 1

    if not path.is_dir():
        print(f"❌ Error: Path is not a directory: {path}", file=sys.stderr)
        return 1

    # Parse ignore list
    additional_ignores = [d.strip() for d in args.ignore.split(",")] if args.ignore else None

    # Determine output directory
    output_dir = Path(args.output) if args.output else path
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle --all flag
    if args.all:
        args.html = args.fix = args.cursor = args.claude = True

    # Show banner
    _log("", args.quiet, args.json)
    _log(f"🔍 Revibe v{__version__} — Scanning {path}", args.quiet, args.json)
    _log("", args.quiet, args.json)

    try:
        result = _perform_scan(path, additional_ignores, args.quiet, args.json)
        if result is None:
            return 0

        # Terminal report
        if not args.quiet and not args.json:
            print()
            print_terminal_report(result.metrics, __version__, force_plain=args.no_color)

        # JSON output
        if args.json:
            print(generate_json_report(result.metrics, str(path), result.analyses))

        # HTML report
        if args.html:
            html_path = output_dir / "revibe_report.html"
            try:
                html_path.write_text(generate_html_report(result.metrics, str(path)), encoding="utf-8")
                if not args.quiet:
                    print(f"  📄 HTML report: {html_path}")
            except OSError as e:
                print(f"  ❌ Failed to write HTML report to {html_path}: {e}", file=sys.stderr)

        # Fix files
        if args.fix or args.cursor or args.claude:
            _generate_fix_files(args, output_dir, str(path), result.metrics)

        _log("", args.quiet, args.json)
        return 0

    except KeyboardInterrupt:
        print("\n  Scan cancelled.")
        return 130

    except Exception as e:
        print(f"\n❌ Error during scan: {e}", file=sys.stderr)
        if os.environ.get("REVIBE_DEBUG"):
            import traceback
            traceback.print_exc()
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        return run_scan(args)
    elif args.command is None:
        parser.print_help()
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
