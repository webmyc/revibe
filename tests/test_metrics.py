"""Tests for the metrics module."""

import pytest

from revibe.analyzer import analyze_files
from revibe.duplicates import find_all_duplicates
from revibe.metrics import (
    CodebaseMetrics,
    aggregate_metrics,
    calculate_defect_estimate,
    calculate_health_score,
    determine_risk_level,
)
from revibe.scanner import scan_codebase
from revibe.smells import detect_all_smells


class TestCalculateDefectEstimate:
    """Tests for defect density calculation."""

    def test_basic_calculation(self):
        density, defects = calculate_defect_estimate(1000)
        # With AI multiplier: 25 * 1.7 = 42.5 per KLOC
        assert density == pytest.approx(42.5)
        assert defects == pytest.approx(42, abs=1)

    def test_no_ai_multiplier(self):
        density, defects = calculate_defect_estimate(1000, ai_generated=False)
        assert density == pytest.approx(25.0)
        assert defects == pytest.approx(25, abs=1)

    def test_zero_loc(self):
        density, defects = calculate_defect_estimate(0)
        assert defects == 0

    def test_large_codebase(self):
        density, defects = calculate_defect_estimate(100000)
        # 100 KLOC * 42.5 = 4250 defects
        assert defects == pytest.approx(4250, abs=50)


class TestFeatureInteractions:
    """Tests for feature interaction formula: 2^n - 1 - n."""

    def test_zero_features(self):
        metrics = CodebaseMetrics(feature_count=0)
        assert metrics.feature_interactions == 0

    def test_one_feature(self):
        metrics = CodebaseMetrics(feature_count=1)
        # 2^1 - 1 - 1 = 0
        assert metrics.feature_interactions == 0

    def test_two_features(self):
        metrics = CodebaseMetrics(feature_count=2)
        # 2^2 - 1 - 2 = 1
        assert metrics.feature_interactions == 1

    def test_five_features(self):
        metrics = CodebaseMetrics(feature_count=5)
        # 2^5 - 1 - 5 = 32 - 1 - 5 = 26
        assert metrics.feature_interactions == 26

    def test_ten_features(self):
        metrics = CodebaseMetrics(feature_count=10)
        # 2^10 - 1 - 10 = 1024 - 1 - 10 = 1013
        assert metrics.feature_interactions == 1013

    def test_large_feature_count_capped(self):
        metrics = CodebaseMetrics(feature_count=100)
        # Should be capped at n=20 to prevent overflow
        # 2^20 - 1 - 20 = 1048555
        assert metrics.feature_interactions == 2 ** 20 - 1 - 20


class TestCalculateHealthScore:
    """Tests for health score calculation."""

    def test_perfect_score(self):
        # Create metrics with excellent values
        metrics = CodebaseMetrics(
            source_loc=1000,
            test_loc=1000,
            test_to_code_ratio=1.0,
            ai_smell_scores={},
            duplicate_groups=[],
            long_functions=[],
            sensitive_functions_without_error_handling=[],
            todos=[],
            total_classes=5,
        )
        score = calculate_health_score(metrics)
        # Should be near 100
        assert score >= 90

    def test_no_tests_penalty(self):
        metrics = CodebaseMetrics(
            source_loc=1000,
            test_loc=0,
            test_to_code_ratio=0.0,
        )
        score = calculate_health_score(metrics)
        # Should lose 40 points for no tests
        assert score <= 60

    def test_high_smells_penalty(self):
        metrics = CodebaseMetrics(
            source_loc=1000,
            test_to_code_ratio=1.0,
            ai_smell_scores={
                "smell1": 0.8,
                "smell2": 0.9,
                "smell3": 0.7,
            },
        )
        score = calculate_health_score(metrics)
        # Should lose points for high smells
        assert score < 100

    def test_score_stays_in_range(self):
        # Test with terrible metrics
        metrics = CodebaseMetrics(
            source_loc=1000,
            test_to_code_ratio=0.0,
            ai_smell_scores={f"smell{i}": 0.9 for i in range(8)},
            duplicate_groups=[None] * 10,
            long_functions=[(None, None)] * 20,
            sensitive_functions_without_error_handling=[(None, None)] * 10,
            todos=[None] * 50,
            total_classes=100,
        )
        score = calculate_health_score(metrics)
        assert 0 <= score <= 100


class TestDetermineRiskLevel:
    """Tests for risk level determination."""

    def test_low_risk(self):
        assert determine_risk_level(80) == "LOW"
        assert determine_risk_level(100) == "LOW"

    def test_moderate_risk(self):
        assert determine_risk_level(60) == "MODERATE"
        assert determine_risk_level(79) == "MODERATE"

    def test_elevated_risk(self):
        assert determine_risk_level(40) == "ELEVATED"
        assert determine_risk_level(59) == "ELEVATED"

    def test_high_risk(self):
        assert determine_risk_level(20) == "HIGH"
        assert determine_risk_level(39) == "HIGH"

    def test_critical_risk(self):
        assert determine_risk_level(0) == "CRITICAL"
        assert determine_risk_level(19) == "CRITICAL"


class TestAggregateMetrics:
    """Tests for metrics aggregation."""

    def test_aggregate_healthy_project(self, healthy_project):
        files = scan_codebase(str(healthy_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)

        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        assert isinstance(metrics, CodebaseMetrics)
        assert metrics.total_files > 0
        assert metrics.source_files > 0
        assert metrics.test_files > 0
        assert metrics.source_loc > 0
        assert metrics.test_loc > 0
        assert 0 <= metrics.health_score <= 100
        assert metrics.risk_level in ["LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL"]

    def test_aggregate_no_tests_project(self, no_tests_project):
        files = scan_codebase(str(no_tests_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)

        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        assert metrics.test_files == 0
        assert metrics.test_loc == 0
        assert metrics.test_to_code_ratio == 0.0
        # Health score should be lower due to no tests
        assert metrics.health_score < 70

    def test_aggregate_empty_project(self, empty_project):
        files = scan_codebase(str(empty_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)

        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        assert metrics.total_files == 0
        assert metrics.source_loc == 0

    def test_language_breakdown(self, mixed_languages_project):
        files = scan_codebase(str(mixed_languages_project))
        analyses = analyze_files(files)
        smells = detect_all_smells(analyses)
        duplicates = find_all_duplicates(analyses)

        metrics = aggregate_metrics(files, analyses, smells, duplicates)

        assert len(metrics.languages) >= 4  # Python, JS, TS, Go
        assert "Python" in metrics.languages
        assert "JavaScript" in metrics.languages


class TestMetricsSummary:
    """Tests for the summary method."""

    def test_summary_contains_key_fields(self):
        """Test that summary contains all required fields."""
        try:
            metrics = CodebaseMetrics(
                total_files=10,
                source_files=8,
                test_files=2,
                source_loc=500,
                test_loc=100,
                health_score=75,
                risk_level="MODERATE",
            )

            summary = metrics.summary()

            if not summary:
                pytest.fail("Summary dictionary is empty")

            required_fields = [
                "total_files", "source_files", "health_score",
                "risk_level", "estimated_defects"
            ]

            for field in required_fields:
                assert field in summary, f"Missing required field: {field}"

            assert summary["health_score"] == 75

        except Exception as e:
            pytest.fail(f"Summary generation failed: {e}")
