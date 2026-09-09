"""
Main entry point and orchestrator for RansomWatch.
Validates dependencies, initializes models and knowledge base, and starts the FastAPI server.
"""

import os
import sys
import time
# pyrefly: ignore [missing-import]
import uvicorn
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import settings
from evidence.database import db
from dataset.generate_dataset import generate_dataset
from detection.train_model import train_ransomwatch_model
from rag.ingest import ingest_knowledge_base

BANNER = """
======================================================================
  ____                                __        __atch
 |  _ \\ __ _ _ __  ___  ___  _ __ ___ \\ \\      / /_ _   _   ___ 
 | |_) / _` | '_ \\/ __|/ _ \\| '_ ` _ \\ \\ \\ /\\ / / _` | | | | / __|
 |  _ < (_| | | | \\__ \\ (_) | | | | | | \\ V  V / (_| | |_| | \\__ \\
 |_| \\_\\__,_|_| |_|___/\\___/|_| |_| |_|  \\_/\\_/ \\__,_|\\__, | |___/
                                                      |___/       
  AI-Based Early Ransomware Behavior Detection and Analysis
  Defensive Cybersecurity Academic Prototype
======================================================================
"""


def check_and_prepare_environment():
    """Verify directories, database, ML models, and RAG knowledge store."""
    print(BANNER)
    print(f"[*] Base Directory:        {settings.BASE_DIR}")
    print(f"[*] Monitored Sandbox:     {settings.TEST_DATA_DIR}")
    print(f"[*] SQLite Database:       {settings.DB_PATH}")

    # 1. Directories
    settings.ensure_directories()

    # 2. Database
    db.init_db()
    print("[+] Evidence Database verified.")

    # 3. ML Model verification
    if not settings.MODEL_PATH.exists():
        print("[!] Detection model not found on disk.")
        if not settings.DATASET_CSV.exists():
            print("[*] Generating synthetic behavioral dataset...")
            generate_dataset(settings.DATASET_CSV, total_samples=5000)
        print("[*] Training RandomForestClassifier model...")
        train_ransomwatch_model()
    else:
        print(f"[+] Behavioral ML model found at: {settings.MODEL_PATH}")

    # 4. RAG Knowledge Base verification
    rag_index_file = settings.VECTOR_STORE_DIR / "knowledge_index.pkl"
    if not rag_index_file.exists():
        print("[*] RAG vector store not found. Ingesting cybersecurity knowledge base...")
        ingest_knowledge_base()
    else:
        print(f"[+] RAG vector store verified at: {rag_index_file}")

    # 5. Gemini API configuration status
    if settings.GEMINI_API_KEY:
        print(f"[+] Google Gemini AI:      ENABLED (Model: {settings.GEMINI_MODEL})")
    else:
        print("[!] Google Gemini AI:      UNCONFIGURED (Graceful fallback active).")
        print("    Tip: Add GEMINI_API_KEY=your_key in .env to activate autonomous LLM triage.")

    print(f"\n[+] RansomWatch Server starting on: http://{settings.HOST}:{settings.PORT}")
    print(f"[+] SOC Dashboard accessible at:   http://{settings.HOST}:{settings.PORT}/dashboard/index.html\n")


def main():
    check_and_prepare_environment()

    # Launch uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
