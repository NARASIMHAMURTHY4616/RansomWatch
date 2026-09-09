"""
Model training pipeline for RansomWatch.
Trains a RandomForestClassifier on behavioral filesystem telemetry features.
"""

import json
import time
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

from config.settings import settings
from dataset.generate_dataset import generate_dataset


def train_ransomwatch_model(
    dataset_path: Path | None = None,
    model_save_path: Path | None = None,
    meta_save_path: Path | None = None,
) -> dict:
    """Train, evaluate, and serialize the RansomWatch behavioral detector."""
    csv_file = (dataset_path or settings.DATASET_CSV).resolve()
    model_file = (model_save_path or settings.MODEL_PATH).resolve()
    meta_file = (meta_save_path or settings.MODEL_META_PATH).resolve()

    # If dataset does not exist, generate it automatically
    if not csv_file.exists():
        print(f"[*] Dataset not found at {csv_file}. Generating fresh dataset...")
        generate_dataset(output_path=csv_file)

    print(f"[*] Loading training dataset from: {csv_file}")
    df = pd.read_csv(csv_file)

    features = settings.FEATURE_NAMES
    target = "label"

    X = df[features]
    y = df[target]

    print(f"[*] Dataset shape: {df.shape} | Features: {len(features)}")
    print(f"[*] Class distribution: Benign (0)={sum(y==0)}, Ransomware-like (1)={sum(y==1)}")

    # Stratified Train/Test split for balanced representation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"[*] Training RandomForestClassifier on {len(X_train)} samples...")
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # Predictions
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Feature importances
    importances = {
        feat: round(float(imp), 4)
        for feat, imp in zip(features, clf.feature_importances_)
    }

    print("\n======================================================================")
    print("                RANSOMWATCH ML MODEL TRAINING REPORT                  ")
    print("======================================================================")
    print(f"  Model Type:        RandomForestClassifier (trees=120, depth=12)")
    print(f"  Accuracy:          {acc * 100:.2f}%")
    print(f"  Precision:         {prec * 100:.2f}%")
    print(f"  Recall:            {rec * 100:.2f}% (CRITICAL FOR DETECTION)")
    print(f"  F1 Score:          {f1 * 100:.2f}%")
    print(f"  Confusion Matrix:  TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")
    print("\n  Top Behavioral Feature Importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        print(f"    - {feat:<22}: {imp:.4f}")
    print("======================================================================\n")

    # Save model
    model_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, model_file)
    print(f"[+] Model artifact serialized to: {model_file}")

    # Save metadata with feature order and metrics
    metadata = {
        "model_type": "RandomForestClassifier",
        "feature_names": features,
        "classes": {0: "BENIGN", 1: "RANSOMWARE_LIKE"},
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm,
        "feature_importances": importances,
        "trained_at": time.time(),
    }
    meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[+] Model metadata saved to: {meta_file}")

    return metadata


if __name__ == "__main__":
    train_ransomwatch_model()
