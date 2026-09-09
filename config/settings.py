"""
Settings and configuration management for RansomWatch.
Loads environment variables from .env and provides centralized paths and parameters.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Base project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Centralized configuration settings for RansomWatch."""

    # Project metadata
    PROJECT_NAME: str = "RansomWatch"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "AI-Based Early Ransomware Behavior Detection and Analysis"

    # Base Paths
    BASE_DIR: Path = BASE_DIR
    TEST_DATA_DIR: Path = BASE_DIR / "test_data"
    DATASET_DIR: Path = BASE_DIR / "dataset"
    DATASET_CSV: Path = DATASET_DIR / "behavior_dataset.csv"
    DETECTION_DIR: Path = BASE_DIR / "detection"
    MODEL_DIR: Path = DETECTION_DIR / "model"
    MODEL_PATH: Path = MODEL_DIR / "ransomwatch_model.pkl"
    MODEL_META_PATH: Path = MODEL_DIR / "model_metadata.json"
    EVIDENCE_DIR: Path = BASE_DIR / "evidence"
    DB_PATH: Path = BASE_DIR / "ransomwatch.db"
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"

    # RAG Paths
    RAG_DIR: Path = BASE_DIR / "rag"
    KNOWLEDGE_BASE_DIR: Path = RAG_DIR / "knowledge_base"
    VECTOR_STORE_DIR: Path = RAG_DIR / "vector_store"

    # Web & Logging Paths
    DASHBOARD_DIR: Path = BASE_DIR / "dashboard"
    LOGS_DIR: Path = BASE_DIR / "logs"
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Monitoring Parameters
    MONITOR_WINDOW_SECONDS: float = float(os.getenv("MONITOR_WINDOW_SECONDS", "5.0"))
    SUBWINDOW_SECONDS: float = 1.0  # Used for burst calculation

    # Feature List (Must maintain consistent order across training and live inference)
    FEATURE_NAMES: list[str] = [
        "create_rate",
        "modified_rate",
        "rename_rate",
        "delete_rate",
        "operations_rate",
        "directories_affected",
        "activity_burst",
    ]

    # Risk Engine Thresholds
    RISK_THRESHOLD_LOW: int = int(os.getenv("RISK_THRESHOLD_LOW", "30"))
    RISK_THRESHOLD_MEDIUM: int = int(os.getenv("RISK_THRESHOLD_MEDIUM", "60"))
    RISK_THRESHOLD_HIGH: int = int(os.getenv("RISK_THRESHOLD_HIGH", "80"))

    # AI Configuration (Gemini)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required runtime directories exist."""
        directories = [
            cls.TEST_DATA_DIR,
            cls.DATASET_DIR,
            cls.MODEL_DIR,
            cls.EVIDENCE_DIR,
            cls.KNOWLEDGE_BASE_DIR,
            cls.VECTOR_STORE_DIR,
            cls.LOGS_DIR,
            cls.REPORTS_DIR,
            cls.DASHBOARD_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def setup_logging(cls, level: int = logging.INFO) -> logging.Logger:
        """Configure structured logging to both console and file."""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = cls.LOGS_DIR / "ransomwatch.log"

        logger = logging.getLogger("RansomWatch")
        logger.setLevel(level)

        # Avoid duplicate handlers if already configured
        if not logger.handlers:
            formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # File handler
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger


settings = Settings()
