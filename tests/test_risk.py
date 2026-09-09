"""
Unit tests for the Risk Engine score calculations, bounds, and explainable reasons.
"""

from risk_engine.risk_scorer import RiskScorer


def test_risk_scorer_bounds():
    """Verify that risk scores remain strictly within the 0 to 100 range."""
    scorer = RiskScorer()

    # Minimal benign scenario
    ml_low = {"ransomware_probability": 0.05}
    feat_low = {
        "rename_rate": 0.0,
        "activity_burst": 0.0,
        "directories_affected": 0,
        "operations_rate": 0.0,
        "modified_rate": 0.0,
    }
    res_low = scorer.calculate_risk(ml_low, feat_low)
    assert 0 <= res_low["risk_score"] <= 100
    assert res_low["severity"] == "LOW"

    # Extreme attack burst scenario
    ml_high = {"ransomware_probability": 0.99}
    feat_high = {
        "rename_rate": 40.0,
        "activity_burst": 80.0,
        "directories_affected": 10,
        "operations_rate": 90.0,
        "modified_rate": 50.0,
    }
    res_high = scorer.calculate_risk(ml_high, feat_high)
    assert 0 <= res_high["risk_score"] <= 100
    assert res_high["risk_score"] >= 80
    assert res_high["severity"] == "CRITICAL"
    assert len(res_high["reasons"]) > 0


def test_severity_classification_thresholds():
    """Verify standard severity tier mapping."""
    scorer = RiskScorer(low_threshold=30, med_threshold=60, high_threshold=80)

    # Moderate suspicion
    ml_med = {"ransomware_probability": 0.55}
    feat_med = {
        "rename_rate": 3.0,
        "activity_burst": 8.0,
        "directories_affected": 2,
        "operations_rate": 5.0,
        "modified_rate": 4.0,
    }
    res_med = scorer.calculate_risk(ml_med, feat_med)
    assert res_med["severity"] in ("MEDIUM", "HIGH")
    assert any("ML" in r or "rename" in r.lower() for r in res_med["reasons"])
