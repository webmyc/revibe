"""Command-line interface for Revibe."""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from revibe import __version__
from revibe.analyzer import analyze_files
from revibe.duplicates import find_all_duplicates
from revibe.fixer import FixerEngine, generate_fix_plan
from revibe.metrics import aggregate_metrics
from revibe.report_html import generate_html_report
from revibe.report_json import render_json_report
from revibe.report_terminal import print_terminal_report
from revibe.scanner import scan_codebase
from revibe.smells import detect_all_smells


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

    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the codebase to scan (default: current directory)",
    )

    # Output format options
    output_group = scan_parser.add_argument_group("Output formats")
    output_group.add_argument(
        "--html",
        action="store_true",
        help="Generate an HTML report",
    )
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON to stdout",
    )
    output_group.add_argument(
        "--fix",
        action="store_true",
        help="Generate REVIBE_FIXES.md with copy-paste AI fix instructions",
    )
    output_group.add_argument(
        "--cursor",
        action="store_true",
        help="Generate .cursorrules file with fix priorities",
    )
    output_group.add_argument(
        "--claude",
        action="store_true",
        help="Generate CLAUDE.md section with health notes",
    )
    output_group.add_argument(
        "--all",
        action="store_true",
        help="Generate all output formats (HTML + JSON + fix files)",
    )

    # Other options
    scan_parser.add_argument(
        "--output", "-o",
        type=str,
        metavar="DIR",
        help="Output directory for generated files (default: codebase root)",
    )
    scan_parser.add_argument(
        "--ignore",
        type=str,
        metavar="DIRS",
        help="Comma-separated list of additional directories to ignore",
    )
    scan_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress terminal output (useful with --json)",
    )
    scan_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    return parser


def run_scan(args: argparse.Namespace) -> int:
    """Run the scan command."""
    path = Path(args.path).resolve()

    if not path.exists():
        print(f"❌ Error: Path does not exist: {path}", file=sys.stderr)
        return 1

    if not path.is_dir():
        print(f"❌ Error: Path is not a directory: {path}", file=sys.stderr)
        return 1

    # Parse ignore list
    additional_ignores: Optional[List[str]] = None
    if args.ignore:
        additional_ignores = [d.strip() for d in args.ignore.split(",")]

    # Determine output directory
    output_dir = Path(args.output) if args.output else path
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle --all flag
    if args.all:
        args.html = True
        args.fix = True
        args.cursor = True
        args.claude = True

    # Show scanning message
    if not args.quiet and not args.json:
        print()
        print(f"🔍 Revibe v{__version__} — Scanning {path}")
        print()

    try:
        # Step 1: Scan for files
        if not args.quiet and not args.json:
            print("  Discovering files...")
        source_files = scan_codebase(str(path), additional_ignores)

        if not source_files:
            if not args.quiet:
                print("  ⚠️ No source files found in this directory.")
            return 0

        if not args.quiet and not args.json:
            langs = set(f.language for f in source_files)
            print(f"  Found {len(source_files)} files across {len(langs)} languages")

        # Step 2: Analyze files
        if not args.quiet and not args.json:
            print("  Analyzing files...")
        analyses = analyze_files(source_files)

        # Step 3: Detect smells
        if not args.quiet and not args.json:
            print("  Detecting code smells...")
        smell_scores = detect_all_smells(analyses)

        # Step 4: Find duplicates
        if not args.quiet and not args.json:
            print("  Finding duplicates...")
        duplicates = find_all_duplicates(analyses)

        # Step 5: Aggregate metrics
        if not args.quiet and not args.json:
            print("  Calculating health score...")
        metrics = aggregate_metrics(source_files, analyses, smell_scores, duplicates)

        # Step 6: Generate outputs

        # Terminal report (unless --quiet or --json only)
        if not args.quiet and not args.json:
            print()
            print_terminal_report(metrics, __version__, force_plain=args.no_color)

        # JSON output
        if args.json:
            json_output = render_json_report(metrics, str(path))
            print(json_output)

        # HTML report
        if args.html:
            html_path = output_dir / "revibe_report.html"
            html_content = generate_html_report(metrics, str(path))
            html_path.write_text(html_content, encoding="utf-8")
            if not args.quiet:
                print(f"  📄 HTML report: {html_path}")

        # Fix instructions
        if args.fix or args.cursor or args.claude:
            fixer = FixerEngine(str(path))
            fix_plan = generate_fix_plan(str(path), metrics)

            if args.fix:
                fix_path = output_dir / "REVIBE_FIXES.md"
                fix_content = fixer.render_markdown(fix_plan)
                fix_path.write_text(fix_content, encoding="utf-8")
                if not args.quiet:
                    print(f"  📝 Fix instructions: {fix_path}")

            if args.cursor:
                cursor_path = output_dir / ".cursorrules"
                cursor_content = fixer.render_cursor_rules(fix_plan)
                cursor_path.write_text(cursor_content, encoding="utf-8")
                if not args.quiet:
                    print(f"  🔧 Cursor rules: {cursor_path}")

            if args.claude:
                claude_path = output_dir / "REVIBE_CLAUDE.md"
                claude_content = fixer.render_claude_md(fix_plan)
                claude_path.write_text(claude_content, encoding="utf-8")
                if not args.quiet:
                    print(f"  🤖 Claude notes: {claude_path}")

        if not args.quiet and not args.json:
            print()

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


def main(argv: Optional[List[str]] = None) -> int:
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
