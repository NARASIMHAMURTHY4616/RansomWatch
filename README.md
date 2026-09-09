# RansomWatch — AI-Based Early Ransomware Behavior Detection and Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Type: Academic Prototype](https://img.shields.io/badge/Type-Defensive%20Research%20Prototype-red.svg)]()

> **B.Tech Cyber Security Engineering Capstone Prototype**  
> *A real-time behavioral detection, risk scoring, evidence collection, and AI-assisted incident response system running on Ubuntu Linux.*

---

## 1. Project Overview & Problem Statement

### Problem Statement
Traditional signature-based antivirus solutions (AV) and static hash lookups fail against zero-day ransomware, polymorphic payloads, and rapidly mutating threat actors. By the time a signature is updated, ransomware has already encrypted local disks and network shares.

### Solution: RansomWatch
**RansomWatch** detects ransomware **at the behavior level** during the earliest stages of execution (within 5 seconds of the initial burst), before widespread encryption can occur. It monitors filesystem events and active processes, calculates sliding-window velocity metrics, performs inference via a trained **RandomForestClassifier**, computes an explainable **0–100 Risk Score**, persists forensic evidence to **SQLite**, queries a local **RAG knowledge base** (MITRE ATT&CK & NIST Incident Response), and leverages **Google Gemini AI** for autonomous post-detection triage and containment recommendations.

---

## 2. Architecture & Data Flow

```
                      +------------------------------------------+
                      |         SAFE ATTACK SIMULATOR            |
                      | (Operates strictly inside test_data/)    |
                      +------------------------------------------+
                                           │
                                           ▼ (Filesystem & Process Telemetry)
+-----------------------------------------------------------------------------------------+
| REAL-TIME SURVEILLANCE LAYER                                                            |
|  - File Monitor (watchdog): Intercepts CREATE, MODIFY, RENAME, DELETE in test_data/     |
|  - Process Monitor (psutil): Correlates PID, process name, and resource utilization      |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼
+-----------------------------------------------------------------------------------------+
| FEATURE EXTRACTION ENGINE (5.0s Sliding Window)                                         |
|  - create_rate, modified_rate, rename_rate, delete_rate, operations_rate,                |
|    directories_affected, activity_burst (1s peak)                                       |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼
+-----------------------------------------------------------------------------------------+
| ML DETECTION & RISK ENGINE                                                              |
|  - Scikit-Learn RandomForestClassifier (120 trees, balanced weights)                    |
|  - Explainable Risk Engine (0-100 Score, LOW / MEDIUM / HIGH / CRITICAL)                 |
+-----------------------------------------------------------------------------------------+
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     ▼                                           ▼
+------------------------------------------+    +------------------------------------------+
| EVIDENCE DATABASE (SQLite / SQLAlchemy)  |    | FASTAPI REST API (Uvicorn Async Server)   |
| Persistent incident logs & telemetry     |    | Metrics, health status, and live feeds   |
+------------------------------------------+    +------------------------------------------+
                     │                                           │
                     ▼                                           ▼
+------------------------------------------+    +------------------------------------------+
| RAG KNOWLEDGE RETRIEVAL (Vector Store)   |    | CYBERSECURITY SOC DASHBOARD              |
| Ingested MITRE ATT&CK, NIST IR, Defense  |    | Dark SOC UI, Chart.js, Real-time alerts  |
+------------------------------------------+    +------------------------------------------+
                     │
                     ▼
+-----------------------------------------------------------------------------------------+
| GEMINI AI INCIDENT ANALYZER (google-genai SDK)                                          |
| Defensive triage, IOCs, containment steps, MITRE T1486 mapping (graceful offline fallback) |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Technology Stack

- **Operating System**: Ubuntu Linux 22.04 LTS (x86_64)
- **Programming Language**: Python 3.10+
- **Web & API Framework**: FastAPI, Uvicorn, Pydantic v2
- **Filesystem & Process Surveillance**: `watchdog`, `psutil`
- **Machine Learning**: `scikit-learn`, `pandas`, `numpy`, `joblib`
- **Database & ORM**: SQLite 3, `SQLAlchemy`
- **Retrieval-Augmented Generation (RAG)**: Local TF-IDF Vector Embeddings, Cosine Similarity Index
- **Generative AI**: Official `google-genai` SDK (Gemini 2.5 Flash)
- **Frontend Dashboard**: Vanilla HTML5, CSS3 (SOC Dark Theme), JavaScript (ES6+), `Chart.js`
- **Testing**: `pytest`

---

## 4. Safety Guardrails & Academic Precautions

> [!IMPORTANT]
> **SAFETY GUARANTEES FOR ACADEMIC EVALUATION**:
> 1. **Sandbox Isolation**: The Attack Simulator operates **strictly inside `RansomWatch/test_data/`**. Paths are canonicalized and verified before any filesystem operation.
> 2. **Harmless Operations**: The simulator never performs real cryptographic encryption. It performs harmless simulated text transformations (prepending nonces and mock headers) and appends simulated ransom extensions (`.locked`, `.crypto`).
> 3. **Non-Destructive**: Never deletes, modifies, or scans files outside `test_data/`.
> 4. **Safe Process Handling**: The prototype inspects process telemetry read-only; it does not escalate privileges or kill system processes.
> 5. **Defensive AI Prompting**: Gemini AI is strictly constrained to post-detection explanation and defensive incident response.

---

## 5. Installation & Setup (Ubuntu Linux)

### Step 1: Clone Repository & Create Virtual Environment
```bash
cd /home/narasimha/git_prjs/RansomWatch

# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy or edit `.env`:
```bash
# RansomWatch Configuration
HOST=127.0.0.1
PORT=8000
MONITOR_WINDOW_SECONDS=5.0

# Optional: Set your Gemini API key for real-time generative AI incident triage
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: If `GEMINI_API_KEY` is not provided, RansomWatch automatically operates in offline fallback mode with built-in heuristic analysis. Detection and risk scoring are 100% independent of Gemini).*

---

## 6. Training the ML Model & Ingesting RAG Knowledge

The system will automatically initialize models on first boot, but you can also run each stage individually:

### 1. Generate Behavioral Dataset
```bash
python -m dataset.generate_dataset
```
*Generates 5,000 synthetic behavioral samples (`dataset/behavior_dataset.csv`) balancing benign activity (compiling, browsing, text editing, idle) and ransomware patterns (burst modifications, multi-folder traversals, rapid renaming).*

### 2. Train the Random Forest Classifier
```bash
python -m detection.train_model
```
*Trains a balanced `RandomForestClassifier` (120 estimators, depth 12) with stratified 80/20 train/test evaluation. Evaluates accuracy, precision, recall (prioritizing low false negatives), F1-score, and confusion matrix, saving artifacts to `detection/model/ransomwatch_model.pkl`.*

### 3. Ingest Cybersecurity Knowledge into RAG
```bash
python -m rag.ingest
```
*Parses and chunks Markdown documents in `rag/knowledge_base/` (`ransomware.md`, `incident_response.md`, `mitigation.md`, `mitre_attck.md`), creates normalized vector embeddings, and serializes the index to `rag/vector_store/`.*

---

## 7. Running RansomWatch

Start the integrated real-time detection pipeline and FastAPI server:
```bash
python run.py
```

The system will display the startup banner:
```
======================================================================
  RansomWatch — AI-Based Early Ransomware Behavior Detection and Analysis
======================================================================
[+] Evidence Database verified.
[+] Behavioral ML model found at: detection/model/ransomwatch_model.pkl
[+] RAG vector store verified at: rag/vector_store/knowledge_index.pkl
[+] RansomWatch Server starting on: http://127.0.0.1:8000
[+] SOC Dashboard accessible at:   http://127.0.0.1:8000/dashboard/index.html
```

Open your browser to:  
👉 **`http://127.0.0.1:8000`** or **`http://127.0.0.1:8000/dashboard/index.html`**

---

## 8. Live Demonstration Workflow

### Demo Scenario A: Benign Activity (Normal Usage)
In a second terminal window (with `.venv` activated):
```bash
python -m attack_simulator.simulator --mode benign --duration 8
```
- **Observed Behavior**: The simulator creates and updates a few text files with human-like delays (0.6s–1.4s).
- **Dashboard Metric**: Operations velocity remains between 0.5–1.5 ops/sec.
- **Result**: ML predicts `BENIGN`. Risk score remains **LOW** (0–15). No security incidents are triggered.

---

### Demo Scenario B: Ransomware Burst Activity (Attack Detection)
In the second terminal window (or by clicking **"Simulate Ransomware Burst"** directly on the dashboard):
```bash
python -m attack_simulator.simulator --mode ransomware --duration 8 --intensity high
```
- **Observed Behavior**:
  - Seeds files across multiple subdirectories (`documents/`, `finance/`, `projects/`, `logs/`).
  - Reads dummy files, modifies them with simulated transformed headers, and rapidly renames them with ransomware extensions (`.locked`, `.crypto`, `.rwenc`).
  - Drops a harmless `RESTORE_INSTRUCTIONS.txt` note.
- **Pipeline Execution**:
  1. `watchdog` captures bursts of `CREATE`, `MODIFY`, and `RENAME` events in real time.
  2. `feature_extractor` measures:
     - `operations_rate > 15 ops/sec`
     - `rename_rate > 10 renames/sec`
     - `activity_burst > 20 ops/sec`
     - `directories_affected >= 4`
  3. `BehavioralDetector` runs Random Forest inference -> Predicts **`RANSOMWARE_LIKE`** (Confidence > 90%).
  4. `RiskScorer` calculates a score of **85–95 (CRITICAL)**.
  5. Security Incident is saved to SQLite (`ransomwatch.db`).
  6. `RAGRetriever` matches the incident to MITRE ATT&CK **T1486 (Data Encrypted for Impact)** and NIST Containment guidelines.
  7. `GeminiAnalyzer` generates structured defensive triage and containment steps (or offline fallback).
  8. Dashboard emits a real-time visual alert, updates Chart.js, and logs the incident in the table.

---

### Demo Scenario C: Incident Investigation & AI Triage
1. On the dashboard, click **"Inspect & Triage"** on the newly detected incident.
2. An analyst modal opens showing:
   - Behavioral feature pills (rates and 1s burst peak).
   - Offending process ID and name (`python3` or `attack_simulator`).
   - Retrieved RAG cybersecurity recommendations.
   - Post-detection Gemini AI incident summary, MITRE mapping, and network isolation runbook.
3. Click **"Reset Sandbox"** to clear dummy files from `test_data/` after testing.

---

## 9. Running the Automated Test Suite

Run unit and integration tests using `pytest`:
```bash
pytest tests/ -v
```

Tests cover:
- Filesystem event creation, enqueuing, and callback execution (`test_monitor.py`).
- Sliding window feature extraction, pruning, and burst calculation (`test_features.py`).
- Random Forest inference on benign vs. ransomware vectors (`test_detection.py`).
- Risk scoring bounds, severity thresholds, and explainable reasons (`test_risk.py`).

---

## 10. REST API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/status` | Operational health of monitor, ML model, RAG, and AI |
| `GET` | `/api/stats` | Aggregated incident totals and severity breakdown |
| `GET` | `/api/live-metrics` | Real-time 5-second sliding window telemetry and chart history |
| `GET` | `/api/incidents` | List recorded security incidents (supports `limit`, `severity`) |
| `GET` | `/api/incidents/{id}` | Full incident details with features, RAG context, and AI report |
| `DELETE`| `/api/incidents/{id}` | Delete specific incident record |
| `POST`| `/api/incidents/clear-all`| Clear incident history from SQLite |
| `POST`| `/api/analyze/{id}` | Run / re-run RAG retrieval and Gemini AI triage on an incident |
| `GET` | `/api/analyze/rag/search` | Search cybersecurity knowledge base via semantic vectors |
| `POST`| `/api/simulator/run` | Trigger benign or ransomware simulation via API |
| `POST`| `/api/simulator/cleanup` | Safely wipe files inside `test_data/` |

---

## 11. MITRE ATT&CK Mapping

| MITRE ID | Technique Name | RansomWatch Detection & Response Mechanism |
|---|---|---|
| **T1486** | *Data Encrypted for Impact* | Real-time rename velocity and burst modification monitoring |
| **T1083** | *File & Directory Discovery* | Multi-directory traversal tracking (`directories_affected > 3`) |
| **T1490** | *Inhibit System Recovery* | Knowledge base alerting on volume shadow copy tampering |
| **T1021** | *Remote Services* | Immediate network host isolation recommendations |

---

## 12. Limitations & Future Scope

### Current Prototype Limitations
- **User-space Monitoring**: Relies on `watchdog` in user space rather than an in-kernel eBPF probe or Linux Fanotify, which could offer sub-millisecond kernel intercepts.
- **Single Host Prototype**: Designed to run on a standalone Ubuntu machine for academic and viva presentation purposes.
- **Process Attribution**: Uses heuristic process table correlation rather than kernel process-to-inode handles.

### Future Enhancements
1. **eBPF Kernel Probes**: Transition from `watchdog` to eBPF `kprobe`/`tracepoint` monitoring for kernel-level non-bypassable hooks.
2. **Entropy Analysis**: Incorporate real-time block-level Shannon entropy calculation on modified file chunks.
3. **Automated Containment Driver**: Automated Linux cgroups-based process suspension (`SIGSTOP`) upon reaching CRITICAL risk.
4. **SIEM / Syslog Integration**: Forwarding JSON alerts to Splunk, Wazuh, or Elastic Security.

---

## 13. License
This defensive academic prototype is open-source under the MIT License. Built for educational and defensive cybersecurity research.
