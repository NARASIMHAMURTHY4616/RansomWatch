"""
Risk Scoring Engine for RansomWatch.
Calculates an explainable 0-100 risk score and severity level based on ML predictions and behavioral heuristics.
"""

from typing import Dict, Any, List
from config.settings import settings


class RiskScorer:
    """Calculates transparent risk scores and severity classifications."""

    def __init__(
        self,
        low_threshold: int = 30,
        med_threshold: int = 60,
        high_threshold: int = 80,
    ):
        self.low_threshold = low_threshold
        self.med_threshold = med_threshold
        self.high_threshold = high_threshold

    def calculate_risk(
        self,
        ml_result: Dict[str, Any],
        features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute risk score from 0-100 with explainable reasons.

        Weights & Components:
        - ML Confidence / Probability: up to 45 pts
        - Rapid File Renames:          up to 20 pts (primary hallmark of extension alteration)
        - Activity Burst (1s peak):    up to 15 pts
        - Multi-Directory Footprint:   up to 10 pts
        - Overall Operations Rate:     up to 10 pts
        Total Max: 100 pts
        """
        score = 0.0
        reasons: List[str] = []
        breakdown: Dict[str, float] = {}

        # 1. Machine Learning Component (Max 45 pts)
        prob = ml_result.get("ransomware_probability", 0.0)
        ml_pts = prob * 45.0
        score += ml_pts
        breakdown["ml_score"] = round(ml_pts, 1)

        if prob >= 0.75:
            reasons.append(f"High ML ransomware confidence ({prob*100:.1f}%)")
        elif prob >= 0.50:
            reasons.append(f"Elevated ML suspicion score ({prob*100:.1f}%)")

        # 2. File Rename Rate (Max 20 pts)
        rename_rate = float(features.get("rename_rate", 0.0))
        if rename_rate >= 10.0:
            rename_pts = 20.0
            reasons.append(f"Critical rename rate detected ({rename_rate:.1f} renames/sec) indicating bulk extension changes")
        elif rename_rate >= 5.0:
            rename_pts = 15.0
            reasons.append(f"High rename rate ({rename_rate:.1f} renames/sec)")
        elif rename_rate >= 2.0:
            rename_pts = 10.0
            reasons.append(f"Moderate rename frequency ({rename_rate:.1f} renames/sec)")
        elif rename_rate >= 0.5:
            rename_pts = 5.0
        else:
            rename_pts = 0.0
        score += rename_pts
        breakdown["rename_score"] = rename_pts

        # 3. Activity Burst in 1-second subwindow (Max 15 pts)
        burst = float(features.get("activity_burst", 0.0))
        if burst >= 20.0:
            burst_pts = 15.0
            reasons.append(f"Severe 1-second activity burst ({burst:.0f} operations/sec peak)")
        elif burst >= 10.0:
            burst_pts = 10.0
            reasons.append(f"Sharp activity burst ({burst:.0f} operations/sec peak)")
        elif burst >= 5.0:
            burst_pts = 5.0
            reasons.append(f"Moderate operations burst ({burst:.0f} operations/sec peak)")
        else:
            burst_pts = 0.0
        score += burst_pts
        breakdown["burst_score"] = burst_pts

        # 4. Multi-Directory Footprint (Max 10 pts)
        dirs_affected = int(features.get("directories_affected", 0))
        if dirs_affected >= 5:
            dir_pts = 10.0
            reasons.append(f"Broad recursive traversal across {dirs_affected} directories simultaneously")
        elif dirs_affected >= 3:
            dir_pts = 7.0
            reasons.append(f"Activity spans across {dirs_affected} distinct directories")
        elif dirs_affected >= 2:
            dir_pts = 4.0
        else:
            dir_pts = 0.0
        score += dir_pts
        breakdown["directory_score"] = dir_pts

        # 5. Overall Operations & Modification Rate (Max 10 pts)
        ops_rate = float(features.get("operations_rate", 0.0))
        mod_rate = float(features.get("modified_rate", 0.0))
        if ops_rate >= 15.0 or mod_rate >= 12.0:
            ops_pts = 10.0
            reasons.append(f"High filesystem throughput ({ops_rate:.1f} ops/sec, {mod_rate:.1f} modifies/sec)")
        elif ops_rate >= 8.0 or mod_rate >= 6.0:
            ops_pts = 6.0
            reasons.append(f"Elevated filesystem modifications ({mod_rate:.1f} modifies/sec)")
        elif ops_rate >= 3.0:
            ops_pts = 3.0
        else:
            ops_pts = 0.0
        score += ops_pts
        breakdown["ops_score"] = ops_pts

        # Clamp score between 0 and 100
        final_score = int(round(min(100.0, max(0.0, score))))

        # Determine Severity
        if final_score >= self.high_threshold:
            severity = "CRITICAL"
        elif final_score >= self.med_threshold:
            severity = "HIGH"
        elif final_score >= self.low_threshold:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        if not reasons:
            reasons.append("Filesystem metrics remain within baseline benign parameters.")

        return {
            "risk_score": final_score,
            "severity": severity,
            "reasons": reasons,
            "breakdown": breakdown,
        }
