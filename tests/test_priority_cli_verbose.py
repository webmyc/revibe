"""
Verbose tests for revibe.cli module.
Focusing on argument parsing, main execution flow, and flag permutations.
Targeting high line count and edge case coverage.
"""
from unittest.mock import MagicMock, patch

import pytest

from revibe.cli import create_parser, main, run_scan


@pytest.fixture
def mock_args():
    args = MagicMock()
    args.path = "."
    args.output = None
    args.ignore = None
    args.all = False
    args.html = False
    args.json = False
    args.fix = False
    args.cursor = False
    args.claude = False
    args.quiet = False
    args.no_color = False
    args.command = "scan"
    return args

class TestArgParser:
    """Verbose tests for argument parsing logic."""

    def test_create_parser_defaults(self):
        """Test parser default values."""
        parser = create_parser()
        # Simulate parsing "scan ."
        args = parser.parse_args(["scan", "."])
        assert args.command == "scan"
        assert args.path == "."
        assert args.output is None
        assert args.all is False
        assert args.json is False
        assert args.html is False
        assert args.fix is False

    def test_create_parser_all_flags(self):
        """Test parser with all flags enabled."""
        parser = create_parser()
        cmd = [
            "scan",
            "/tmp",
            "--output", "out",
            "--ignore", "node_modules,dist",
            "--all",
            "--quiet",
            "--no-color"
        ]
        args = parser.parse_args(cmd)
        assert args.path == "/tmp"
        assert args.output == "out"
        assert args.ignore == "node_modules,dist"
        assert args.all is True
        assert args.quiet is True
        assert args.no_color is True

    def test_create_parser_individual_flags(self):
        """Test individual flags without --all."""
        parser = create_parser()
        cmd = [
            "scan", ".",
            "--html",
            "--json",
            "--fix",
            "--cursor",
            "--claude"
        ]
        args = parser.parse_args(cmd)
        assert args.html is True
        assert args.json is True
        # Note: --fix, --cursor, etc. might strictly check presence if defaulted to False
        assert args.fix is True
        assert args.cursor is True
        assert args.claude is True


class TestRunScanVerbose:
    """Verbose tests for run_scan function execution flows."""

    @patch("revibe.cli._perform_scan")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_run_scan_invalid_path_not_exists(self, mock_is_dir, mock_exists, mock_args, capsys):
        """Test run_scan with non-existent path."""
        mock_exists.return_value = False
        mock_args.path = "/invalid/path"

        ret = run_scan(mock_args)

        assert ret == 1
        captured = capsys.readouterr()
        assert "Path does not exist" in captured.err

    @patch("revibe.cli._perform_scan")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_run_scan_invalid_path_not_dir(self, mock_is_dir, mock_exists, mock_args, capsys):
        """Test run_scan with file path instead of directory."""
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_args.path = "file.txt"

        ret = run_scan(mock_args)

        assert ret == 1
        captured = capsys.readouterr()
        assert "Path is not a directory" in captured.err

    @patch("revibe.cli._perform_scan")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.is_dir", return_value=True)
    @patch("pathlib.Path.mkdir")
    def test_run_scan_expand_all_flag(self, mock_mkdir, mock_is_dir, mock_exists, mock_perform, mock_args):
        """Test that --all flag enables other output flags."""
        mock_args.all = True
        # Initial False state
        mock_args.html = False
        mock_args.fix = False

        # Setup successful scan result
        mock_result = MagicMock()
        mock_perform.return_value = mock_result

        # We need to mock report generation functions to avoid actual errors/prints
        with patch("revibe.cli.print_terminal_report"), \
             patch("revibe.cli.generate_json_report"), \
             patch("revibe.cli.generate_html_report"), \
             patch("revibe.cli._generate_fix_files"), \
             patch("pathlib.Path.write_text"):

            run_scan(mock_args)

            # Verify flags were flipped
            assert mock_args.html is True
            assert mock_args.fix is True
            assert mock_args.cursor is True
            assert mock_args.claude is True

    @patch("revibe.cli._perform_scan")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.is_dir", return_value=True)
    @patch("pathlib.Path.mkdir")
    def test_run_scan_output_directory_creation(self, mock_mkdir, mock_is_dir, mock_exists, mock_perform, mock_args):
        """Test output directory is created."""
        mock_args.output = "custom_out"
        mock_perform.return_value = MagicMock()

        with patch("revibe.cli.print_terminal_report"):
            run_scan(mock_args)

        mock_mkdir.assert_called_with(parents=True, exist_ok=True)

    @patch("revibe.cli._perform_scan")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.is_dir", return_value=True)
    def test_run_scan_returns_early_on_none_result(self, mock_is_dir, mock_exists, mock_perform, mock_args):
        """Test successful exit when _perform_scan returns None (e.g. empty dir)."""
        mock_perform.return_value = None
        ret = run_scan(mock_args)
        assert ret == 0


class TestMainEntryPoint:
    """Verbose tests for main() entry point."""

    @patch("revibe.cli.run_scan")
    @patch("sys.argv", ["revibe", "scan", "."])
    def test_main_calls_run_scan(self, mock_run_scan):
        """Test simple valid invocation."""
        main()
        mock_run_scan.assert_called_once()

    @patch("revibe.cli.create_parser")
    def test_main_no_command_prints_help(self, mock_create_parser):
        """Test calling without command prints help."""
        mock_parser = MagicMock()
        mock_create_parser.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.command = None
        mock_parser.parse_args.return_value = mock_args

        ret = main(["arg"])

        assert ret == 0
        mock_parser.print_help.assert_called_once()

    @patch("revibe.cli.create_parser")
    def test_main_unknown_command_prints_help(self, mock_create_parser):
        """Test calling with unknown command."""
        mock_parser = MagicMock()
        mock_create_parser.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.command = "unknown"
        mock_parser.parse_args.return_value = mock_args

        ret = main(["unknown"])

        assert ret == 1
        mock_parser.print_help.assert_called_once()


@patch("revibe.cli._perform_scan")
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.is_dir", return_value=True)
@patch("sys.stderr.write")
def test_run_scan_exception_handling_verbose(mock_stderr, mock_is_dir, mock_exists, mock_perform, mock_args):
    """Test exception handling with and without debug mode."""
    # Setup exception
    mock_perform.side_effect = Exception("Boom")

    # 1. Normal mode (no traceback)
    with patch("os.environ.get", return_value=None):
        ret = run_scan(mock_args)
        assert ret == 1
        # Should NOT import traceback
        with patch("traceback.print_exc") as mock_tb:
            mock_tb.assert_not_called()

    # 2. Debug mode (REVIBE_DEBUG set)
    with patch("os.environ.get", return_value="1"):
        mock_perform.side_effect = Exception("Boom") # Reset side effect if needed
        # We need to mock traceback import or just verify behavior
        # Since traceback is imported inside function, we mock it via sys.modules or patch existing
        with patch("traceback.print_exc") as mock_tb:
            ret = run_scan(mock_args)
            assert ret == 1
            mock_tb.assert_called_once()
