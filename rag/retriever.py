"""
RAG Knowledge Retriever for RansomWatch.
Given an incident or search query, retrieves the most relevant defensive cybersecurity chunks.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config.settings import settings
from rag.ingest import ingest_knowledge_base

logger = logging.getLogger("RansomWatch.RAGRetriever")


class RAGRetriever:
    """Retrieves relevant cybersecurity defense guidelines from local vector index."""

    def __init__(self, vector_dir: Path | None = None):
        self.vector_dir = (vector_dir or settings.VECTOR_STORE_DIR).resolve()
        self.index_file = self.vector_dir / "knowledge_index.pkl"
        self.vectorizer = None
        self.embeddings = None
        self.chunks = []
        self._load_or_ingest()

    def _load_or_ingest(self) -> None:
        """Load the serialized vector index or trigger ingestion if missing."""
        if not self.index_file.exists():
            logger.info("RAG index file not found. Running automatic ingestion...")
            try:
                ingest_knowledge_base(output_dir=self.vector_dir)
            except Exception as e:
                logger.error(f"Failed to auto-ingest knowledge base: {e}")
                return

        try:
            bundle = joblib.load(self.index_file)
            self.vectorizer = bundle["vectorizer"]
            self.embeddings = bundle["embeddings"]
            self.chunks = bundle["chunks"]
            logger.info(f"Loaded RAG vector store with {len(self.chunks)} knowledge chunks.")
        except Exception as e:
            logger.error(f"Failed to load RAG index from {self.index_file}: {e}")

    def is_ready(self) -> bool:
        return self.vectorizer is not None and self.embeddings is not None and len(self.chunks) > 0

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Query the vector index and return top_k most relevant chunks.
        """
        if not self.is_ready():
            self._load_or_ingest()
            if not self.is_ready():
                logger.warning("RAG retriever is not ready; returning empty context.")
                return []

        try:
            query_vec = self.vectorizer.transform([query])
            # Compute cosine similarity between query and all stored document chunks
            similarities = cosine_similarity(query_vec, self.embeddings).flatten()

            # Rank indices by descending similarity
            ranked_indices = np.argsort(similarities)[::-1]

            results = []
            for idx in ranked_indices[:top_k]:
                score = float(similarities[idx])
                chunk = self.chunks[idx]
                results.append({
                    "source": chunk["source"],
                    "section": chunk["section"],
                    "content": chunk["content"],
                    "relevance_score": round(score, 4),
                })
            return results
        except Exception as e:
            logger.error(f"Error during RAG retrieval for query '{query}': {e}")
            return []

    def retrieve_for_incident(self, incident_data: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
        """Construct a contextual query from an incident's indicators and retrieve defense knowledge."""
        reasons = incident_data.get("reasons", [])
        features = incident_data.get("features", {})
        severity = incident_data.get("severity", "CRITICAL")

        query_parts = [
            f"Ransomware detection {severity} alert",
            " ".join(reasons),
            f"file rename rate {features.get('rename_rate', 0)}",
            f"modified rate {features.get('modified_rate', 0)}",
            f"burst operations {features.get('activity_burst', 0)}",
            "containment host isolation T1486 data encrypted",
        ]
        composite_query = " ".join(query_parts)
        return self.retrieve(composite_query, top_k=top_k)
