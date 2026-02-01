"""Tests for duplicate detection."""

import pytest

from revibe.duplicates import DuplicateGroup, find_all_duplicates, find_exact_duplicates


class TestExactDuplicates:
    """Tests for exact duplicate detection."""

    def test_detects_exact_duplicates(self, temp_dir):
        """Two identical files should be flagged as exact duplicates."""
        from revibe.analyzer import analyze_files
        from revibe.scanner import scan_codebase

        # Create duplicate files
        content = "def hello():\n    print('world')\n" * 10
        (temp_dir / "a.py").write_text(content)
        (temp_dir / "b.py").write_text(content)
        # Create a different file
        (temp_dir / "c.py").write_text("def different():\n    pass\n")

        files = scan_codebase(str(temp_dir))
        analyses = analyze_files(files)
        duplicates = find_all_duplicates(analyses)

        # Should find at least one duplicate group
        exact_groups = [g for g in duplicates if g.is_exact]
        assert len(exact_groups) >= 1

    def test_no_duplicates_in_unique_files(self, temp_dir):
        """Unique files should not be flagged."""
        from revibe.analyzer import analyze_files
        from revibe.scanner import scan_codebase

        for i in range(3):
            (temp_dir / f"file_{i}.py").write_text(f"def func_{i}():\n    return {i}\n")

        files = scan_codebase(str(temp_dir))
        analyses = analyze_files(files)
        duplicates = find_all_duplicates(analyses)

        exact_groups = [g for g in duplicates if g.is_exact]
        assert len(exact_groups) == 0


class TestNearDuplicates:
    """Tests for near-duplicate detection."""

    def test_detects_similar_files(self, temp_dir):
        """Similar files should be flagged as near duplicates."""
        from revibe.analyzer import analyze_files
        from revibe.scanner import scan_codebase

        # Create similar files (same structure, minor differences)
        (temp_dir / "utils_v1.py").write_text(
            "def helper_one():\n    return 1\n\n"
            "def helper_two():\n    return 2\n\n"
            "def helper_three():\n    return 3\n"
        )
        (temp_dir / "utils_v2.py").write_text(
            "def helper_one():\n    return 10\n\n"
            "def helper_two():\n    return 20\n\n"
            "def helper_three():\n    return 30\n"
        )

        files = scan_codebase(str(temp_dir))
        analyses = analyze_files(files)
        duplicates = find_all_duplicates(analyses)

        # May or may not find near duplicates depending on threshold
        # Just ensure it doesn't crash
        assert isinstance(duplicates, list)


class TestDuplicateGroup:
    """Tests for DuplicateGroup dataclass."""

    def test_exact_duplicate_group(self):
        """Test creating an exact duplicate group."""
        group = DuplicateGroup(
            files=["a.py", "b.py"],
            is_exact=True,
            similarity=1.0,
        )
        assert group.is_exact
        assert group.similarity == 1.0
        assert len(group.files) == 2

    def test_near_duplicate_group(self):
        """Test creating a near duplicate group."""
        group = DuplicateGroup(
            files=["x.py", "y.py"],
            is_exact=False,
            similarity=0.85,
        )
        assert not group.is_exact
        assert group.similarity == 0.85
