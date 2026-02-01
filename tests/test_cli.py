"""Tests for the CLI module."""


import pytest

from revibe.cli import create_parser, main, run_scan


class TestCreateParser:
    """Tests for argument parser creation."""

    def test_creates_parser(self):
        parser = create_parser()
        assert parser.prog == "revibe"

    def test_version_flag(self, capsys):
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "revibe" in captured.out

    def test_scan_command_defaults(self):
        parser = create_parser()
        args = parser.parse_args(["scan"])
        assert args.command == "scan"
        assert args.path == "."
        assert args.html is False
        assert args.json is False
        assert args.fix is False

    def test_scan_with_path(self):
        parser = create_parser()
        args = parser.parse_args(["scan", "/some/path"])
        assert args.path == "/some/path"

    def test_scan_with_all_flags(self):
        parser = create_parser()
        args = parser.parse_args([
            "scan", ".",
            "--html", "--json", "--fix", "--cursor", "--claude",
            "--quiet", "--no-color",
            "--output", "./reports",
            "--ignore", "vendor,tmp"
        ])
        assert args.html is True
        assert args.json is True
        assert args.fix is True
        assert args.cursor is True
        assert args.claude is True
        assert args.quiet is True
        assert args.no_color is True
        assert args.output == "./reports"
        assert args.ignore == "vendor,tmp"

    def test_scan_all_flag(self):
        parser = create_parser()
        args = parser.parse_args(["scan", ".", "--all"])
        assert args.all is True


class TestRunScan:
    """Tests for the run_scan function."""

    def test_nonexistent_path(self, capsys):
        parser = create_parser()
        args = parser.parse_args(["scan", "/nonexistent/path/that/does/not/exist"])
        result = run_scan(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "does not exist" in captured.err

    def test_file_not_directory(self, temp_dir, capsys):
        file_path = temp_dir / "file.txt"
        file_path.write_text("hello")

        parser = create_parser()
        args = parser.parse_args(["scan", str(file_path)])
        result = run_scan(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "not a directory" in captured.err

    def test_empty_directory(self, empty_project):
        parser = create_parser()
        args = parser.parse_args(["scan", str(empty_project), "--quiet"])
        result = run_scan(args)
        assert result == 0

    def test_healthy_project_scan(self, healthy_project, capsys):
        parser = create_parser()
        args = parser.parse_args(["scan", str(healthy_project)])
        result = run_scan(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "Health Score" in captured.out

    def test_quiet_mode(self, healthy_project, capsys):
        parser = create_parser()
        args = parser.parse_args(["scan", str(healthy_project), "--quiet"])
        result = run_scan(args)
        assert result == 0
        captured = capsys.readouterr()
        # Should have minimal output
        assert "Discovering" not in captured.out

    def test_json_output(self, healthy_project, capsys):
        parser = create_parser()
        args = parser.parse_args(["scan", str(healthy_project), "--json"])
        result = run_scan(args)
        assert result == 0
        captured = capsys.readouterr()
        # Should be valid JSON-ish output
        assert "{" in captured.out
        assert "health_score" in captured.out

    def test_html_output(self, healthy_project, temp_dir):
        parser = create_parser()
        args = parser.parse_args([
            "scan", str(healthy_project),
            "--html", "--quiet",
            "--output", str(temp_dir)
        ])
        result = run_scan(args)
        assert result == 0
        # Check HTML file was created
        html_file = temp_dir / "revibe_report.html"
        assert html_file.exists()
        content = html_file.read_text()
        assert "<html" in content
        assert "Revibe" in content  # Check for branding

    def test_fix_output(self, healthy_project, temp_dir):
        parser = create_parser()
        args = parser.parse_args([
            "scan", str(healthy_project),
            "--fix", "--quiet",
            "--output", str(temp_dir)
        ])
        result = run_scan(args)
        assert result == 0
        fix_file = temp_dir / "REVIBE_FIXES.md"
        assert fix_file.exists()
        content = fix_file.read_text()
        assert "Revibe" in content

    def test_cursor_output(self, healthy_project, temp_dir):
        parser = create_parser()
        args = parser.parse_args([
            "scan", str(healthy_project),
            "--cursor", "--quiet",
            "--output", str(temp_dir)
        ])
        result = run_scan(args)
        assert result == 0
        cursor_file = temp_dir / ".cursorrules"
        assert cursor_file.exists()

    def test_claude_output(self, healthy_project, temp_dir):
        parser = create_parser()
        args = parser.parse_args([
            "scan", str(healthy_project),
            "--claude", "--quiet",
            "--output", str(temp_dir)
        ])
        result = run_scan(args)
        assert result == 0
        claude_file = temp_dir / "REVIBE_CLAUDE.md"
        assert claude_file.exists()

    def test_all_flag_generates_all_outputs(self, healthy_project, temp_dir):
        parser = create_parser()
        args = parser.parse_args([
            "scan", str(healthy_project),
            "--all", "--quiet",
            "--output", str(temp_dir)
        ])
        result = run_scan(args)
        assert result == 0
        # All output files should exist
        assert (temp_dir / "revibe_report.html").exists()
        assert (temp_dir / "REVIBE_FIXES.md").exists()
        assert (temp_dir / ".cursorrules").exists()
        assert (temp_dir / "REVIBE_CLAUDE.md").exists()


class TestMain:
    """Tests for the main entry point."""

    def test_no_command_shows_help(self, capsys):
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "revibe" in captured.out or result == 0

    def test_scan_command(self, healthy_project):
        result = main(["scan", str(healthy_project), "--quiet"])
        assert result == 0

    def test_invalid_command(self, capsys):
        # The argparse will error on invalid command
        with pytest.raises(SystemExit) as exc_info:
            main(["invalid"])
        assert exc_info.value.code == 2  # argparse error code
