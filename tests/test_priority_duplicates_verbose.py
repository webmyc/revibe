"""
Verbose tests for duplicates.py focusing on near-duplicate detection logic.
Targeting high line count and complex scenarios.
"""
import pytest
from unittest.mock import MagicMock
from revibe.duplicates import find_near_duplicates, DuplicateGroup, calculate_similarity
from revibe.analyzer import FileAnalysis, FunctionInfo, ClassInfo
from revibe.scanner import SourceFile
from pathlib import Path

@pytest.fixture
def clean_analyses():
    """Create a set of distinct analyses."""
    files = [
        ("a.py", "def foo():\n    print('hello')\n", "Python"),
        ("b.py", "def bar():\n    print('world')\n", "Python"),
        ("c.py", "class Baz:\n    pass\n", "Python"),
    ]
    analyses = []
    for name, content, lang in files:
        sf = SourceFile(Path(name), name, lang, False, len(content.encode('utf-8')))
        # Mock path behavior for uniqueness checks if needed, but calculate_similarity uses objects
        sf.path = MagicMock()
        sf.path.name = name
        
        fa = FileAnalysis(
            source_file=sf,
            total_lines=10,
            code_lines=10,
        )
        analyses.append(fa)
    return analyses

class TestDuplicatesVerbose:
    """Verbose tests for duplicate detection."""

    def test_calculate_similarity_identical_metrics(self):
        """Test similarity of files with identical metrics."""
        a1 = FileAnalysis(SourceFile(Path("1"), "1", "Py", False, 100), 100, 100)
        a1.functions = [FunctionInfo("foo", 1, 10, 10)]
        a1.classes = [ClassInfo("Bar", 1, 10, 10)]
        
        a2 = FileAnalysis(SourceFile(Path("2"), "2", "Py", False, 100), 100, 100)
        a2.functions = [FunctionInfo("foo", 1, 10, 10)]
        a2.classes = [ClassInfo("Bar", 1, 10, 10)]
        
        # Expect 1.0 because lines match, functions match, classes match
        assert calculate_similarity(a1, a2) == 1.0

    def test_calculate_similarity_distinct(self):
        """Test similarity of disjoint files."""
        a1 = FileAnalysis(SourceFile(Path("1"), "1", "Py", False, 100), 100, 100)
        a1.functions = [FunctionInfo("foo", 1, 10, 10)]
        
        a2 = FileAnalysis(SourceFile(Path("2"), "2", "Py", False, 200), 200, 200) # Different lines
        a2.functions = [FunctionInfo("bar", 1, 10, 10)] # Different func
        
        # Line sim: 100/200 = 0.5. Weighted 0.3 -> 0.15
        # Func sim: 0. Weighted 0.5 -> 0
        # Class sim: 0 (empty). Weighted 0.2 -> 0?
        
        sim = calculate_similarity(a1, a2)
        # Expected: ~0.15
        assert 0.1 <= sim <= 0.2

    def test_calculate_similarity_partial_overlap(self):
        """Test partial overlap."""
        a1 = FileAnalysis(SourceFile(Path("1"), "1", "Py", False, 100), 100, 100)
        a1.functions = [FunctionInfo("shared", 1, 10, 10), FunctionInfo("unique1", 1, 10, 10)]
        
        a2 = FileAnalysis(SourceFile(Path("2"), "2", "Py", False, 100), 100, 100)
        a2.functions = [FunctionInfo("shared", 1, 10, 10), FunctionInfo("unique2", 1, 10, 10)]
        
        # Line sim: 1.0 -> 0.3
        # Func sim: intersection(1) / union(3) = 0.33. Weighted 0.5 -> ~0.165
        # Class sim: 0.
        # Total: 0.3 + 0.165 + 0 = 0.465
        
        sim = calculate_similarity(a1, a2)
        assert 0.4 <= sim <= 0.5

    def test_find_near_duplicates_empty_input(self):
        """Test with empty analysis list."""
        results = find_near_duplicates([])
        assert len(results) == 0

    def test_find_near_duplicates_single_file(self, clean_analyses):
        """Test with single file."""
        results = find_near_duplicates([clean_analyses[0]])
        assert len(results) == 0

    def test_find_near_duplicates_distinct_files(self, clean_analyses):
        """Test with completely different files (names/content implicitly diff in clean_analyses)."""
        # clean_analyses have lines=10.
        results = find_near_duplicates(clean_analyses)
        assert len(results) == 0

    def test_find_near_duplicates_identical_group_simulated(self):
        """Test grouping of high-similarity files."""
        # Create 2 files that are identical in metrics
        a1 = FileAnalysis(SourceFile(Path("a.py"), "a.py", "Py", False, 100), 100, 100)
        a1.functions = [FunctionInfo("f",1,1,1)]
        a2 = FileAnalysis(SourceFile(Path("b.py"), "b.py", "Py", False, 100), 100, 100)
        a2.functions = [FunctionInfo("f",1,1,1)]
        
        results = find_near_duplicates([a1, a2], threshold=0.7)
        assert len(results) == 1
        assert results[0].similarity > 0.7

    def test_find_near_duplicates_ignore_small_files(self):
        """Test ignoring files with few lines."""
        a1 = FileAnalysis(SourceFile(Path("1"), "1", "Py", False, 10), 5, 5) # < 10 lines
        a2 = FileAnalysis(SourceFile(Path("2"), "2", "Py", False, 10), 5, 5)
        
        results = find_near_duplicates([a1, a2])
        assert len(results) == 0
