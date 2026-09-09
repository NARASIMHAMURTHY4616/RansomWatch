"""
Live Behavioral Detector for RansomWatch.
Performs real-time inference on extracted behavioral feature vectors using the trained Random Forest model.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import pandas as pd
import numpy as np

from config.settings import settings

logger = logging.getLogger("RansomWatch.Detector")


class BehavioralDetector:
    """Inference engine applying the trained Random Forest model to behavioral feature streams."""

    def __init__(self, model_path: Path | None = None, meta_path: Path | None = None):
        self.model_path = (model_path or settings.MODEL_PATH).resolve()
        self.meta_path = (meta_path or settings.MODEL_META_PATH).resolve()
        self.model = None
        self.metadata = None
        self.feature_names = settings.FEATURE_NAMES
        self._load_model()

    def _load_model(self) -> None:
        """Load trained model and feature metadata from disk."""
        if not self.model_path.exists():
            logger.warning(
                f"Trained model not found at {self.model_path}. "
                "Run `python -m detection.train_model` to train the model."
            )
            return

        try:
            self.model = joblib.load(self.model_path)
            if self.meta_path.exists():
                self.metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))
                self.feature_names = self.metadata.get("feature_names", settings.FEATURE_NAMES)
            logger.info(f"Loaded behavioral detection model from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model from {self.model_path}: {e}")
            self.model = None

    def is_loaded(self) -> bool:
        """Check if model is ready for inference."""
        return self.model is not None

    def detect(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run inference on behavioral feature dictionary.
        Returns:
            {
                "prediction": 1,
                "label": "RANSOMWARE_LIKE",
                "confidence": 0.94,
                "ransomware_probability": 0.94,
                "features": {...}
            }
        """
        if not self.is_loaded():
            self._load_model()
            if not self.is_loaded():
                # Graceful fallback heuristic if model not trained yet
                # High rename and operations rate heuristic
                rename_rate = features.get("rename_rate", 0.0)
                ops_rate = features.get("operations_rate", 0.0)
                burst = features.get("activity_burst", 0.0)
                is_ransom = (rename_rate > 3.0 and ops_rate > 5.0) or burst > 12.0
                return {
                    "prediction": 1 if is_ransom else 0,
                    "label": "RANSOMWARE_LIKE" if is_ransom else "BENIGN",
                    "confidence": 0.70,
                    "ransomware_probability": 0.70 if is_ransom else 0.30,
                    "model_status": "fallback_heuristic",
                    "features": features,
                }

        # Build feature vector matching model's expected column order
        ordered_data = {feat: [features.get(feat, 0.0)] for feat in self.feature_names}
        input_df = pd.DataFrame(ordered_data)

        # Run inference
        pred_int = int(self.model.predict(input_df)[0])
        probabilities = self.model.predict_proba(input_df)[0]

        prob_benign = float(probabilities[0])
        prob_ransom = float(probabilities[1]) if len(probabilities) > 1 else (1.0 - prob_benign)

        confidence = prob_ransom if pred_int == 1 else prob_benign
        label = "RANSOMWARE_LIKE" if pred_int == 1 else "BENIGN"

        return {
            "prediction": pred_int,
            "label": label,
            "confidence": round(float(confidence), 3),
            "ransomware_probability": round(float(prob_ransom), 3),
            "model_status": "active_random_forest",
            "features": features,
        }
