"""
Gemini AI Incident Analyzer for RansomWatch.
Uses the official google-genai SDK to generate structured defensive incident triage,
investigation guidance, and mitigation recommendations.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from config.settings import settings

logger = logging.getLogger("RansomWatch.GeminiAnalyzer")


class GeminiAnalyzer:
    """Provides post-detection defensive analysis and investigation recommendations."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (api_key if api_key is not None else settings.GEMINI_API_KEY).strip()
        self.model_name = model_name or settings.GEMINI_MODEL
        self._client = None

        if self.is_configured():
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info("Gemini client successfully initialized.")
            except Exception as e:
                logger.warning(f"Could not initialize google-genai client: {e}")
                self._client = None

    def is_configured(self) -> bool:
        """Check if an API key is present."""
        return bool(self.api_key and len(self.api_key) > 5)

    def analyze_incident(
        self,
        incident_data: Dict[str, Any],
        rag_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a detected ransomware incident using Gemini AI with RAG context.
        Strictly defensive analysis. Never creates, modifies, or assists ransomware.
        """
        if not self.is_configured() or self._client is None:
            return self._build_offline_fallback(incident_data, rag_chunks)

        try:
            prompt = self._build_prompt(incident_data, rag_chunks or [])
            logger.info(f"Submitting incident {incident_data.get('id')} to Gemini API...")

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            raw_text = response.text or ""
            return self._parse_gemini_response(raw_text, incident_data)

        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            fallback = self._build_offline_fallback(incident_data, rag_chunks)
            fallback["api_error"] = str(e)
            return fallback

    def _build_prompt(
        self,
        incident: Dict[str, Any],
        rag_chunks: List[Dict[str, Any]],
    ) -> str:
        """Construct a defensive prompt containing incident telemetry and RAG cybersecurity context."""
        features = incident.get("features", {})
        reasons = incident.get("reasons", [])
        rag_text = "\n\n".join([f"[{c.get('source')} - {c.get('section')}]:\n{c.get('content')}" for c in rag_chunks])

        prompt = f"""
You are an expert SOC Incident Responder assisting a defensive ransomware detection system called RansomWatch.
SAFETY POLICY: You are assisting a defensive ransomware detection system. Do not provide instructions for creating, modifying, deploying, or improving ransomware. Strictly provide defensive analysis, SOC investigation steps, and containment guidance.

Incident Telemetry:
- Incident ID: {incident.get('id')}
- Timestamp: {incident.get('timestamp')}
- Process Name: {incident.get('process_name')} (PID: {incident.get('pid')})
- ML Prediction: {incident.get('label')} (Confidence: {incident.get('confidence')})
- Ransomware Probability: {incident.get('ransomware_probability')}
- Risk Score: {incident.get('risk_score')} / 100 ({incident.get('severity')})
- Monitored Path: {incident.get('affected_path')}

Behavioral Features (5-second window):
- Create Rate: {features.get('create_rate', 0)} files/sec
- Modified Rate: {features.get('modified_rate', 0)} files/sec
- Rename Rate: {features.get('rename_rate', 0)} files/sec
- Delete Rate: {features.get('delete_rate', 0)} files/sec
- Total Operations Rate: {features.get('operations_rate', 0)} ops/sec
- Affected Directories: {features.get('directories_affected', 0)}
- Activity Burst Peak: {features.get('activity_burst', 0)} ops/sec

Trigger Reasons:
{json.dumps(reasons, indent=2)}

Retrieved Defensive Cybersecurity Knowledge (RAG Context):
{rag_text if rag_text else "No external RAG chunks provided."}

Task:
Provide a structured JSON response with exactly the following JSON keys:
{{
  "summary": "Concise executive summary of what was detected",
  "suspicious_indicators": ["List of distinct behavioral anomalies observed"],
  "likely_technique": "Mapped MITRE ATT&CK technique (e.g. T1486 - Data Encrypted for Impact)",
  "investigation_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
  "containment_recommendations": ["Action 1: ...", "Action 2: ..."],
  "defensive_posture": "Guidance on hardening against future similar attacks",
  "severity_assessment": "Defensive justification of the severity rating"
}}

Respond ONLY with valid JSON. Do not include markdown code block backticks if possible.
"""
        return prompt

    def _parse_gemini_response(self, raw_text: str, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and parse JSON from Gemini's output."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.lstrip("```json").rstrip("```").strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.lstrip("```").rstrip("```").strip()

        try:
            parsed = json.loads(cleaned)
            parsed["available"] = True
            parsed["status"] = "AI_ANALYZED"
            parsed["model_used"] = self.model_name
            return parsed
        except json.JSONDecodeError:
            # If not strict JSON, structure it gracefully
            return {
                "available": True,
                "status": "AI_ANALYZED",
                "summary": cleaned[:300] + "...",
                "raw_text": cleaned,
                "model_used": self.model_name,
                "suspicious_indicators": incident.get("reasons", []),
                "likely_technique": "T1486: Data Encrypted for Impact",
                "investigation_steps": [
                    "Inspect open file descriptors for PID " + str(incident.get("pid")),
                    "Examine recently created or renamed files in test_data/",
                    "Verify backup integrity and isolate host from subnet",
                ],
                "containment_recommendations": [
                    "Suspend anomalous process",
                    "Sever network interfaces",
                ],
            }

    def _build_offline_fallback(
        self,
        incident: Dict[str, Any],
        rag_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Deterministic, reliable fallback analysis when Gemini API key is unconfigured."""
        severity = incident.get("severity", "CRITICAL")
        features = incident.get("features", {})
        rename_rate = features.get("rename_rate", 0.0)
        burst = features.get("activity_burst", 0.0)

        indicators = incident.get("reasons", [])
        if not indicators:
            indicators = [
                f"Elevated rename velocity ({rename_rate} ops/sec)",
                f"Sharp 1-second burst ({burst} ops/sec)",
            ]

        return {
            "available": False,
            "status": "FALLBACK_RULES",
            "summary": "Gemini analysis unavailable — API key not configured.",
            "suspicious_indicators": indicators,
            "likely_technique": "T1486: Data Encrypted for Impact",
            "investigation_steps": [
                f"1. Check active processes accessing {incident.get('affected_path', 'target directory')}.",
                f"2. Inspect file extensions for anomalous suffixes (.locked, .crypto).",
                "3. Check for unauthorized volume shadow copy deletion commands (T1490).",
                "4. Configure GEMINI_API_KEY in .env to activate autonomous generative AI analysis.",
            ],
            "containment_recommendations": [
                "Immediate network isolation to prevent lateral movement (T1021).",
                "Suspend (SIGSTOP) offending process tree rather than killing to preserve cryptographic memory keys.",
                "Verify immutable offline backup status before attempting data restoration.",
            ],
            "defensive_posture": "Implement canary decoy directories and restrict write access on file shares.",
            "severity_assessment": f"Classified as {severity} based on combined Random Forest probability and behavioral rename/burst heuristics.",
            "disclaimer": "Gemini analysis unavailable — API key not configured in .env.",
        }
