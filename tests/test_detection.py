"""
Unit tests for the behavioral ML detector.
"""

from detection.detector import BehavioralDetector


def test_detector_benign_features():
    """Verify that typical benign features produce BENIGN classification."""
    detector = BehavioralDetector()
    benign_features = {
        "create_rate": 0.2,
        "modified_rate": 0.4,
        "rename_rate": 0.0,
        "delete_rate": 0.0,
        "operations_rate": 0.6,
        "directories_affected": 1,
        "activity_burst": 2.0,
    }
    result = detector.detect(benign_features)

    assert result["prediction"] in (0, 1)
    assert 0.0 <= result["confidence"] <= 1.0
    assert 0.0 <= result["ransomware_probability"] <= 1.0
    # Benign patterns should have low ransomware probability
    assert result["ransomware_probability"] < 0.60


def test_detector_ransomware_burst():
    """Verify that extreme burst, high rename, and multi-dir features produce RANSOMWARE_LIKE classification."""
    detector = BehavioralDetector()
    ransom_features = {
        "create_rate": 5.0,
        "modified_rate": 25.0,
        "rename_rate": 25.0,
        "delete_rate": 1.0,
        "operations_rate": 56.0,
        "directories_affected": 6,
        "activity_burst": 45.0,
    }
    result = detector.detect(ransom_features)

    assert result["prediction"] == 1
    assert result["label"] == "RANSOMWARE_LIKE"
    assert result["confidence"] >= 0.70
    assert result["ransomware_probability"] >= 0.70
