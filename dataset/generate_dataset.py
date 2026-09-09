"""
Synthetic behavioral dataset generator for RansomWatch.
Generates realistic filesystem behavioral vectors for BENIGN (0) and RANSOMWARE_LIKE (1) activity.
"""

import random
import numpy as np
import pandas as pd
from pathlib import Path

from config.settings import settings


def generate_benign_samples(count: int = 2500) -> pd.DataFrame:
    """
    Generate synthetic benign samples covering:
    - Idle desktop / light typing
    - Software build / compilation
    - Web browser caching / downloads
    - Log file rotation / system audits
    """
    records = []
    for _ in range(count):
        profile = random.choices(
            ["idle", "editor", "compiler", "browser", "backup"],
            weights=[0.35, 0.25, 0.15, 0.15, 0.10],
            k=1,
        )[0]

        if profile == "idle":
            create_rate = np.random.exponential(scale=0.1)
            modified_rate = np.random.exponential(scale=0.15)
            rename_rate = 0.0 if random.random() > 0.05 else np.random.uniform(0.0, 0.2)
            delete_rate = 0.0 if random.random() > 0.05 else np.random.uniform(0.0, 0.2)
            dirs = random.choice([0, 1])
            burst = np.random.choice([0, 1, 2], p=[0.7, 0.25, 0.05])

        elif profile == "editor":
            create_rate = np.random.uniform(0.0, 0.4)
            modified_rate = np.random.uniform(0.2, 1.2)
            rename_rate = 0.0 if random.random() > 0.15 else np.random.uniform(0.1, 0.4)
            delete_rate = 0.0 if random.random() > 0.10 else np.random.uniform(0.0, 0.3)
            dirs = random.choice([1, 2])
            burst = np.random.randint(1, 4)

        elif profile == "compiler":
            create_rate = np.random.uniform(1.0, 4.5)
            modified_rate = np.random.uniform(1.5, 5.0)
            rename_rate = np.random.uniform(0.0, 0.5)  # builds rarely rename bulk files
            delete_rate = np.random.uniform(0.2, 1.5)
            dirs = random.randint(1, 3)
            burst = np.random.randint(3, 8)

        elif profile == "browser":
            create_rate = np.random.uniform(0.5, 2.5)
            modified_rate = np.random.uniform(0.5, 2.0)
            rename_rate = 0.0 if random.random() > 0.08 else np.random.uniform(0.0, 0.3)
            delete_rate = np.random.uniform(0.1, 0.8)
            dirs = random.choice([1, 2])
            burst = np.random.randint(2, 6)

        else:  # backup / file organizer
            create_rate = np.random.uniform(1.0, 3.5)
            modified_rate = np.random.uniform(1.0, 3.0)
            rename_rate = np.random.uniform(0.1, 0.8)
            delete_rate = np.random.uniform(0.0, 0.5)
            dirs = random.randint(1, 3)
            burst = np.random.randint(2, 7)

        # Ensure realistic operations rate sum
        total_ops = create_rate + modified_rate + rename_rate + delete_rate
        # Add slight observational noise
        total_ops = max(0.0, total_ops + np.random.normal(0, 0.05))

        records.append({
            "create_rate": round(max(0.0, create_rate), 3),
            "modified_rate": round(max(0.0, modified_rate), 3),
            "rename_rate": round(max(0.0, rename_rate), 3),
            "delete_rate": round(max(0.0, delete_rate), 3),
            "operations_rate": round(max(0.0, total_ops), 3),
            "directories_affected": int(dirs),
            "activity_burst": round(float(burst), 3),
            "label": 0,  # BENIGN
        })

    return pd.DataFrame(records)


def generate_ransomware_samples(count: int = 2500) -> pd.DataFrame:
    """
    Generate synthetic ransomware samples covering:
    - High-speed batch encryption & extension change
    - Stealth/trickle ransomware
    - Destructive / wiper-like bursts
    - Multi-directory recursive traversals
    """
    records = []
    for _ in range(count):
        variant = random.choices(
            ["fast_burst", "stealth", "multi_dir", "rename_heavy"],
            weights=[0.40, 0.20, 0.25, 0.15],
            k=1,
        )[0]

        if variant == "fast_burst":
            create_rate = np.random.uniform(2.0, 10.0)
            modified_rate = np.random.uniform(8.0, 35.0)
            rename_rate = np.random.uniform(8.0, 35.0)
            delete_rate = np.random.uniform(0.0, 3.0)
            dirs = random.randint(3, 8)
            burst = np.random.randint(15, 60)

        elif variant == "stealth":
            # Slower to evade simple thresholding, but high rename and cross-directory footprint
            create_rate = np.random.uniform(0.8, 3.5)
            modified_rate = np.random.uniform(3.5, 9.0)
            rename_rate = np.random.uniform(3.0, 8.5)
            delete_rate = np.random.uniform(0.0, 1.0)
            dirs = random.randint(3, 6)
            burst = np.random.randint(7, 18)

        elif variant == "multi_dir":
            create_rate = np.random.uniform(2.0, 8.0)
            modified_rate = np.random.uniform(6.0, 25.0)
            rename_rate = np.random.uniform(5.0, 22.0)
            delete_rate = np.random.uniform(0.2, 4.0)
            dirs = random.randint(4, 12)
            burst = np.random.randint(12, 45)

        else:  # rename_heavy (e.g. extension appending bursts)
            create_rate = np.random.uniform(1.0, 5.0)
            modified_rate = np.random.uniform(4.0, 18.0)
            rename_rate = np.random.uniform(10.0, 40.0)
            delete_rate = np.random.uniform(0.0, 2.0)
            dirs = random.randint(2, 7)
            burst = np.random.randint(14, 50)

        total_ops = create_rate + modified_rate + rename_rate + delete_rate
        total_ops = max(0.0, total_ops + np.random.normal(0, 0.2))

        records.append({
            "create_rate": round(max(0.0, create_rate), 3),
            "modified_rate": round(max(0.0, modified_rate), 3),
            "rename_rate": round(max(0.0, rename_rate), 3),
            "delete_rate": round(max(0.0, delete_rate), 3),
            "operations_rate": round(max(0.0, total_ops), 3),
            "directories_affected": int(dirs),
            "activity_burst": round(float(burst), 3),
            "label": 1,  # RANSOMWARE_LIKE
        })

    return pd.DataFrame(records)


def generate_dataset(output_path: Path | None = None, total_samples: int = 5000) -> Path:
    """Generate and save the balanced, varied behavioral dataset."""
    target_file = (output_path or settings.DATASET_CSV).resolve()
    target_file.parent.mkdir(parents=True, exist_ok=True)

    half = total_samples // 2
    benign_df = generate_benign_samples(count=half)
    ransom_df = generate_ransomware_samples(count=half)

    combined_df = pd.concat([benign_df, ransom_df], ignore_index=True)
    # Shuffle randomly
    combined_df = combined_df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    combined_df.to_csv(target_file, index=False)
    print(f"[+] Successfully generated {len(combined_df)} samples saved to: {target_file}")
    print(f"    - Benign (0): {(combined_df['label'] == 0).sum()}")
    print(f"    - Ransomware-like (1): {(combined_df['label'] == 1).sum()}")
    return target_file


if __name__ == "__main__":
    generate_dataset()
