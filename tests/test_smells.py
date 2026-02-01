"""Tests for the smells module."""


from revibe.analyzer import analyze_files
from revibe.scanner import scan_codebase
from revibe.smells import (
    clamp_score,
    detect_all_smells,
    detect_boilerplate_heavy,
    detect_copy_paste_artifacts,
    detect_dead_code_indicators,
    detect_excessive_comments,
    detect_inconsistent_patterns,
    detect_missing_error_handling,
    detect_over_engineering,
    detect_verbose_naming,
    get_smell_descriptions,
)


class TestClampScore:
    """Tests for score clamping."""

    def test_clamp_normal_values(self):
        assert clamp_score(0.5) == 0.5
        assert clamp_score(0.0) == 0.0
        assert clamp_score(1.0) == 1.0

    def test_clamp_below_zero(self):
        assert clamp_score(-0.5) == 0.0
        assert clamp_score(-1.0) == 0.0

    def test_clamp_above_one(self):
        assert clamp_score(1.5) == 1.0
        assert clamp_score(2.0) == 1.0


class TestIndividualDetectors:
    """Tests for individual smell detectors."""

    def test_excessive_comments_detection(self, temp_dir):
        # Create over-commented file
        (temp_dir / "commented.py").write_text('''
# Comment 1
# Comment 2
# Comment 3
# Comment 4
# Comment 5
x = 1  # inline comment
# Comment 6
y = 2
''')

        files = scan_codebase(str(temp_dir))
        analyses = analyze_files(files)
        result = detect_excessive_comments(analyses)

        assert result.name == "excessive_comments"
        assert 0.0 <= result.score <= 1.0

    def test_verbose_naming_detection(self, bloated_project):
        files = scan_codebase(str(bloated_project))
        analyses = analyze_files(files)
        result = detect_verbose_naming(analyses)

        assert result.name == "verbose_naming"
        assert 0.0 <= result.score <= 1.0
        # Should detect verbose names in bloated project
        assert result.score > 0

    def test_boilerplate_detection(self, temp_dir):
        # Create file with many imports, few functions
        (temp_dir / "imports.py").write_text('''
import os
import sys
import json
import math
import random
import datetime
from pathlib import Path
from typing import List, Dict, Optional

def only_function():
    pass
''')

        files = scan_codebase(str(temp_dir))
        analyses = analyze_files(files)
        result = detect_boilerplate_heavy(analyses)

        assert result.name == "boilerplate_heavy"
        assert 0.0 <= result.score <= 1.0
        # High import-to-function ratio
        assert result.score > 0.3

    def test_inconsistent_patterns_detection(self, temp_dir):
        # Mix snake_case and camelCase
        (temp_dir / "mixed.py").write_text('''
def snake_case_function():
    pass

def camelCaseFunction():
    pass

def anotherSnakeCase():
    pass

def yet_another_snake():
    pass
''')

        files = scan_codebase(str(temp_dir))
        analyses = analyze_files(files)
        result = detect_inconsistent_patterns(analyses)

        assert result.name == "inconsistent_patterns"
        assert 0.0 <= result.score <= 1.0

    def test_dead_code_indicators(self, bloated_project):
        files = scan_codebase(str(bloated_project))
        analyses = analyze_files(files)
        result = detect_dead_code_indicators(analyses)

        assert result.name == "dead_code_indicators"
        assert 0.0 <= result.score <= 1.0
        # Should detect duplicate function names
        assert result.score > 0

    def test_over_engineering_detection(self, bloated_project):
        files = scan_codebase(str(bloated_project))
        analyses = analyze_files(files)
        result = detect_over_engineering(analyses)

        assert result.name == "over_engineering"
        assert 0.0 <= result.score <= 1.0

    def test_missing_error_handling(self, no_tests_project):
        files = scan_codebase(str(no_tests_project))
        analyses = analyze_files(files)
        result = detect_missing_error_handling(analyses)

        assert result.name == "missing_error_handling"
        assert 0.0 <= result.score <= 1.0
        # No error handling in no_tests_project
        assert result.score > 0

    def test_copy_paste_artifacts(self, temp_dir):
        # Create files with repeated strings
        repeated_string = "This is a very long string literal that appears multiple times"
        for i in range(3):
            (temp_dir / f"file{i}.py").write_text(f'''
msg1 = "{repeated_string}"
msg2 = "{repeated_string}"
msg3 = "{repeated_string}"
''')

        files = scan_codebase(str(temp_dir))
        analyses = analyze_files(files)
        result = detect_copy_paste_artifacts(analyses)

        assert result.name == "copy_paste_artifacts"
        assert 0.0 <= result.score <= 1.0


class TestDetectAllSmells:
    """Tests for the combined smell detection."""

    def test_detect_all_returns_dict(self, healthy_project):
        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        scores = detect_all_smells(analyses)

        assert isinstance(scores, dict)
        assert len(scores) == 8  # 8 smell detectors

    def test_all_scores_in_range(self, bloated_project):
        files = scan_codebase(str(bloated_project))
        analyses = analyze_files(files)
        scores = detect_all_smells(analyses)

        for name, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{name} score out of range: {score}"

    def test_expected_smell_names(self, healthy_project):
        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        scores = detect_all_smells(analyses)

        expected_smells = {
            "excessive_comments",
            "verbose_naming",
            "boilerplate_heavy",
            "inconsistent_patterns",
            "dead_code_indicators",
            "over_engineering",
            "missing_error_handling",
            "copy_paste_artifacts",
        }

        assert set(scores.keys()) == expected_smells

    def test_healthy_project_lower_scores(self, healthy_project):
        healthy_files = scan_codebase(str(healthy_project))
        healthy_analyses = analyze_files(healthy_files)
        healthy_scores = detect_all_smells(healthy_analyses)

        # Healthy project should generally have low smell scores
        healthy_avg = sum(healthy_scores.values()) / len(healthy_scores)

        # Average smell score should be under 0.5 for a healthy project
        assert healthy_avg < 0.5

    def test_empty_project_no_crash(self, empty_project):
        files = scan_codebase(str(empty_project))
        analyses = analyze_files(files)
        scores = detect_all_smells(analyses)

        # Should return all zeros without crashing
        assert len(scores) == 8
        for score in scores.values():
            assert score == 0.0


class TestGetSmellDescriptions:
    """Tests for smell descriptions."""

    def test_returns_all_descriptions(self):
        descriptions = get_smell_descriptions()

        assert len(descriptions) == 8
        for name, desc in descriptions.items():
            assert isinstance(name, str)
            assert isinstance(desc, str)
            assert len(desc) > 10  # Should be a meaningful description

    def test_matches_detector_names(self, healthy_project):
        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        scores = detect_all_smells(analyses)
        descriptions = get_smell_descriptions()

        assert set(scores.keys()) == set(descriptions.keys())
