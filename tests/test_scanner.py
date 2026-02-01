"""Tests for the scanner module."""

from pathlib import Path

import pytest

from revibe.scanner import (
    SourceFile,
    detect_language,
    is_test_file,
    scan_codebase,
    should_ignore_directory,
)


class TestDetectLanguage:
    """Tests for language detection."""

    def test_python_extensions(self):
        assert detect_language(Path("app.py")) == "Python"
        assert detect_language(Path("script.pyw")) == "Python"
        assert detect_language(Path("types.pyi")) == "Python"

    def test_javascript_extensions(self):
        assert detect_language(Path("app.js")) == "JavaScript"
        assert detect_language(Path("module.mjs")) == "JavaScript"
        assert detect_language(Path("component.jsx")) == "JavaScript"

    def test_typescript_extensions(self):
        assert detect_language(Path("app.ts")) == "TypeScript"
        assert detect_language(Path("component.tsx")) == "TypeScript"

    def test_go_extension(self):
        assert detect_language(Path("main.go")) == "Go"

    def test_rust_extension(self):
        assert detect_language(Path("lib.rs")) == "Rust"

    def test_unknown_extension(self):
        """Test file with unknown extension."""
        assert detect_language(Path("unknown.xyz")) is None


class TestIsTestFile:
    """Tests for test file detection."""

    def test_test_prefix(self):
        assert is_test_file(Path("test_app.py"), "test_app.py") is True
        assert is_test_file(Path("test_utils.py"), "src/test_utils.py") is True

    def test_test_suffix(self):
        assert is_test_file(Path("app_test.py"), "app_test.py") is True
        assert is_test_file(Path("app.test.js"), "app.test.js") is True

    def test_spec_files(self):
        assert is_test_file(Path("app.spec.ts"), "app.spec.ts") is True
        assert is_test_file(Path("app_spec.rb"), "app_spec.rb") is True

    def test_test_directory(self):
        assert is_test_file(Path("app.py"), "tests/app.py") is True
        assert is_test_file(Path("app.py"), "__tests__/app.py") is True
        assert is_test_file(Path("app.js"), "spec/app.js") is True

    def test_not_test_file(self):
        assert is_test_file(Path("app.py"), "src/app.py") is False
        assert is_test_file(Path("utils.js"), "lib/utils.js") is False


class TestShouldIgnoreDirectory:
    """Tests for directory ignore patterns."""

    def test_ignore_node_modules(self):
        assert should_ignore_directory("node_modules") is True

    def test_ignore_git(self):
        assert should_ignore_directory(".git") is True

    def test_ignore_venv(self):
        assert should_ignore_directory("venv") is True
        assert should_ignore_directory(".venv") is True

    def test_ignore_pycache(self):
        assert should_ignore_directory("__pycache__") is True

    def test_ignore_hidden(self):
        assert should_ignore_directory(".hidden") is True

    def test_dont_ignore_src(self):
        assert should_ignore_directory("src") is False
        assert should_ignore_directory("lib") is False


class TestScanCodebase:
    """Tests for codebase scanning."""

    def test_scan_healthy_project(self, healthy_project):
        files = scan_codebase(str(healthy_project))

        # Should find source and test files
        assert len(files) > 0

        # Check languages detected
        languages = {f.language for f in files}
        assert "Python" in languages

        # Check test file detection
        test_files = [f for f in files if f.is_test]
        source_files = [f for f in files if not f.is_test]

        assert len(test_files) > 0
        assert len(source_files) > 0

    def test_scan_mixed_languages(self, mixed_languages_project):
        files = scan_codebase(str(mixed_languages_project))

        languages = {f.language for f in files}
        assert "Python" in languages
        assert "JavaScript" in languages
        assert "TypeScript" in languages
        assert "Go" in languages

    def test_scan_empty_project(self, empty_project):
        files = scan_codebase(str(empty_project))
        assert len(files) == 0

    def test_scan_with_ignores(self, temp_dir):
        # Create a structure with ignorable directories
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "app.py").write_text("pass")
        (temp_dir / "vendor").mkdir()
        (temp_dir / "vendor" / "lib.py").write_text("pass")

        files = scan_codebase(str(temp_dir))

        # Should only find src/app.py, not vendor/lib.py
        paths = [f.relative_path for f in files]
        assert any("app.py" in p for p in paths)
        assert not any("vendor" in p for p in paths)

    def test_scan_with_additional_ignores(self, temp_dir):
        # Create structure
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "app.py").write_text("pass")
        (temp_dir / "custom_ignore").mkdir()
        (temp_dir / "custom_ignore" / "lib.py").write_text("pass")

        # Without custom ignore
        files1 = scan_codebase(str(temp_dir))
        assert any("custom_ignore" in f.relative_path for f in files1)

        # With custom ignore
        files2 = scan_codebase(str(temp_dir), additional_ignores=["custom_ignore"])
        assert not any("custom_ignore" in f.relative_path for f in files2)

    def test_scan_nonexistent_path(self):
        with pytest.raises(ValueError, match="does not exist"):
            scan_codebase("/nonexistent/path")

    def test_scan_file_not_directory(self, temp_dir):
        file_path = temp_dir / "file.py"
        file_path.write_text("pass")

        with pytest.raises(ValueError, match="not a directory"):
            scan_codebase(str(file_path))

    def test_source_file_properties(self, healthy_project):
        files = scan_codebase(str(healthy_project))

        for f in files:
            assert isinstance(f, SourceFile)
            assert f.path.exists()
            assert f.relative_path
            assert f.language
            assert f.size_bytes >= 0
            assert isinstance(f.is_test, bool)
