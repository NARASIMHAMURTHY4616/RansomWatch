"""
Safe Attack Simulator for RansomWatch.
Simulates benign activity and ransomware-like burst filesystem activity.

SAFETY GUARANTEES:
1. Operates STRICTLY inside the dedicated test directory (test_data/).
2. Never encrypts files - only performs harmless simulated text/byte modifications.
3. Never affects any files or directories outside test_data/.
4. Does not communicate with external networks or servers.
"""

import os
import sys
import time
import random
import string
import shutil
import argparse
from pathlib import Path
from typing import List

from config.settings import settings

SIMULATION_BANNER = """
======================================================================
  [!] SAFE DEFENSIVE RESEARCH PROTOTYPE
  [!] SIMULATION ONLY — NO REAL FILE ENCRYPTION
  [!] Target sandbox: {target_dir}
======================================================================
"""


class SafeAttackSimulator:
    """Safe filesystem activity generator for benign and ransomware-like patterns."""

    def __init__(self, target_dir: Path | None = None):
        self.target_dir = (target_dir or settings.TEST_DATA_DIR).resolve()
        self._ensure_sandbox_safety()

    def _ensure_sandbox_safety(self) -> None:
        """Strict safety assertion: Target directory must be strictly inside the project test_data."""
        expected_root = settings.TEST_DATA_DIR.resolve()
        try:
            # Check relative to expected root or equal
            self.target_dir.relative_to(expected_root)
        except ValueError:
            raise SecurityError(
                f"SAFETY VIOLATION: Simulator target '{self.target_dir}' is outside the authorized sandbox '{expected_root}'!"
            )
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def _random_content(self, lines: int = 15) -> str:
        """Generate harmless dummy text."""
        words = ["project", "audit", "report", "analysis", "system", "database", "security", "metrics", "log"]
        out = []
        for _ in range(lines):
            line = " ".join(random.choices(words, k=8))
            out.append(f"{line} - hash:{random.randint(100000, 999999)}")
        return "\n".join(out)

    def cleanup(self) -> None:
        """Safely remove all files inside test_data/."""
        self._ensure_sandbox_safety()
        print(f"[*] Cleaning up sandbox: {self.target_dir}")
        for item in self.target_dir.iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    item.unlink()
                except OSError:
                    pass
        print("[+] Sandbox cleaned.")

    def seed_dummy_files(self, count_per_dir: int = 5) -> List[Path]:
        """Seed harmless sample files across structured directories."""
        self._ensure_sandbox_safety()
        directories = ["documents", "finance", "projects", "backup", "logs"]
        created_files = []

        for folder_name in directories:
            folder = self.target_dir / folder_name
            folder.mkdir(parents=True, exist_ok=True)
            for i in range(count_per_dir):
                file_path = folder / f"doc_{folder_name}_{i+1}.txt"
                if not file_path.exists():
                    file_path.write_text(self._random_content(), encoding="utf-8")
                    created_files.append(file_path)

        return created_files

    def run_benign(self, duration_seconds: int = 10) -> None:
        """
        Simulate normal user/system behavior:
        - Low frequency operations
        - Normal inter-operation pauses (0.5 - 1.5s)
        - Creating an occasional document
        - Modifying an existing file
        - Occasional rename
        """
        self._ensure_sandbox_safety()
        print(SIMULATION_BANNER.format(target_dir=self.target_dir))
        print(f"[*] Starting BENIGN simulation for ~{duration_seconds} seconds...")
        print("[*] Pattern: Low-frequency file creation, modification, and rare rename.")

        self.seed_dummy_files(count_per_dir=3)
        end_time = time.time() + duration_seconds
        step = 0

        while time.time() < end_time:
            step += 1
            action = random.choice(["create", "modify", "rename", "idle"])
            subdirs = [d for d in self.target_dir.iterdir() if d.is_dir()]
            target_sub = random.choice(subdirs) if subdirs else self.target_dir

            if action == "create":
                new_file = target_sub / f"user_note_{int(time.time())}_{step}.txt"
                new_file.write_text(f"Benign user memo created at {time.ctime()}\n" + self._random_content(5))
                print(f"  [BENIGN] Created: {new_file.name}")

            elif action == "modify":
                existing = [f for f in target_sub.glob("*.txt")]
                if existing:
                    target_file = random.choice(existing)
                    with open(target_file, "a", encoding="utf-8") as f:
                        f.write(f"\nAppended line by user at {time.ctime()}\n")
                    print(f"  [BENIGN] Modified: {target_file.name}")

            elif action == "rename":
                existing = [f for f in target_sub.glob("*.txt") if not f.name.endswith(".bak")]
                if existing:
                    target_file = random.choice(existing)
                    new_name = target_file.with_suffix(".txt.bak")
                    target_file.rename(new_name)
                    print(f"  [BENIGN] Renamed: {target_file.name} -> {new_name.name}")

            # Realistic human/system delay (0.5 to 1.5 seconds)
            time.sleep(random.uniform(0.6, 1.4))

        print("[+] BENIGN simulation complete.")

    def run_ransomware(self, duration_seconds: int = 8, intensity: str = "high") -> None:
        """
        Simulate ransomware-LIKE behavioral characteristics SAFELY:
        - High frequency of file operations
        - Rapid traversal across multiple subdirectories
        - Read file -> write simulated transformed dummy payload (NO real encryption)
        - Rapid file rename with ransomware extension (.locked, .crypto, .rwenc)
        - Drop simulated informational ransom note (RESTORE_INSTRUCTIONS.txt)
        """
        self._ensure_sandbox_safety()
        print(SIMULATION_BANNER.format(target_dir=self.target_dir))
        print(f"[*] Starting RANSOMWARE SIMULATION for ~{duration_seconds} seconds [intensity={intensity}]...")
        print("[*] SIMULATION ONLY — NO REAL FILE ENCRYPTION")
        print("[*] Rapid traversal, burst modifications, safe dummy transforms, bulk renames.")

        # Seed files across directories
        seed_files = self.seed_dummy_files(count_per_dir=6)
        subdirs = [d for d in self.target_dir.iterdir() if d.is_dir()]

        delay = 0.02 if intensity == "high" else 0.08
        end_time = time.time() + duration_seconds
        processed_count = 0

        # Phase 1: Rapidly create dummy targets if directory is small
        for folder in subdirs:
            for i in range(5):
                fpath = folder / f"target_asset_{i}_{int(time.time()*1000)%10000}.dat"
                fpath.write_text(self._random_content(10), encoding="utf-8")
                time.sleep(delay)

        # Phase 2: Rapid read -> modify -> rename loop across multiple folders
        all_files = [f for f in self.target_dir.rglob("*.txt")] + [f for f in self.target_dir.rglob("*.dat")]

        extensions = [".locked", ".crypto", ".rwenc", ".enc"]

        for file_path in all_files:
            if time.time() >= end_time:
                break
            if file_path.suffix in extensions or file_path.name.startswith("RESTORE_"):
                continue

            try:
                # 1. Read file
                _ = file_path.read_text(encoding="utf-8", errors="ignore")

                # 2. Modify with simulated dummy transform (Harmless mock banner)
                mock_payload = (
                    f"--- SIMULATED_TRANSFORMED_HEADER_ONLY ---\n"
                    f"ORIGINAL_SIZE: {file_path.stat().st_size} BYTES\n"
                    f"SIMULATION_NONCE: {random.randint(10000000, 99999999)}\n"
                    f"PAYLOAD: " + "".join(random.choices(string.ascii_letters + string.digits, k=128)) + "\n"
                )
                file_path.write_text(mock_payload, encoding="utf-8")

                # 3. Bulk rename with simulated ransomware extension
                ext = random.choice(extensions)
                new_path = file_path.with_suffix(file_path.suffix + ext)
                file_path.rename(new_path)

                processed_count += 1
                if processed_count % 3 == 0:
                    print(f"  [SIMULATION BURST] Transformed & Renamed: {file_path.name} -> {new_path.name}")

                time.sleep(delay)

            except Exception as e:
                print(f"  [DEBUG] Simulation error handling file {file_path}: {e}")
                continue

        # Phase 3: Harmless simulated informational note
        note_content = (
            "===================================================================\n"
            "            RANSOMWATCH DEFENSIVE RESEARCH SIMULATION              \n"
            "===================================================================\n"
            "This is a harmless simulated attack note generated inside test_data/.\n"
            "NO REAL ENCRYPTION HAS OCCURRED.\n"
            "No files outside test_data/ were touched.\n"
            "Run simulator with --cleanup to reset the test directory.\n"
        )
        for folder in subdirs:
            note_file = folder / "RESTORE_INSTRUCTIONS.txt"
            note_file.write_text(note_content, encoding="utf-8")

        print(f"[+] RANSOMWARE SIMULATION complete. Processed {processed_count} files in burst mode.")


def main():
    parser = argparse.ArgumentParser(
        description="RansomWatch Safe Attack Simulator (Simulation Only - No Real Encryption)"
    )
    parser.add_argument(
        "--mode",
        choices=["benign", "ransomware", "cleanup"],
        default="benign",
        help="Simulation mode to run",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=8,
        help="Duration in seconds for simulation (default: 8s)",
    )
    parser.add_argument(
        "--intensity",
        choices=["normal", "high"],
        default="high",
        help="Intensity level for ransomware simulation",
    )

    args = parser.parse_args()
    simulator = SafeAttackSimulator()

    if args.mode == "benign":
        simulator.run_benign(duration_seconds=args.duration)
    elif args.mode == "ransomware":
        simulator.run_ransomware(duration_seconds=args.duration, intensity=args.intensity)
    elif args.mode == "cleanup":
        simulator.cleanup()


if __name__ == "__main__":
    main()
