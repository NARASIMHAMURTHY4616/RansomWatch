"""
Analysis and RAG query routes for RansomWatch.
"""

from fastapi import APIRouter, HTTPException
from evidence.database import db
from rag.retriever import RAGRetriever
from ai.gemini_analyzer import GeminiAnalyzer

router = APIRouter(prefix="/api/analyze", tags=["analysis"])

retriever = RAGRetriever()
analyzer = GeminiAnalyzer()


@router.post("/{incident_id}")
def analyze_incident(incident_id: str):
    """
    Trigger on-demand RAG retrieval and Gemini AI defensive analysis for an incident.
    """
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    incident_dict = incident.to_dict()

    # 1. Retrieve RAG cybersecurity context
    rag_chunks = retriever.retrieve_for_incident(incident_dict, top_k=3)

    # 2. Run Gemini AI analysis
    ai_analysis = analyzer.analyze_incident(incident_dict, rag_chunks=rag_chunks)

    # 3. Persist enriched evidence in SQLite
    db.update_incident_analysis(
        incident_id=incident_id,
        rag_context=rag_chunks,
        ai_analysis=ai_analysis,
        status="AI_ANALYZED" if ai_analysis.get("available") else "ANALYZED",
    )

    return {
        "status": "success",
        "incident_id": incident_id,
        "rag_context": rag_chunks,
        "ai_analysis": ai_analysis,
    }


@router.get("/rag/search")
def search_knowledge_base(query: str, top_k: int = 3):
    """Direct search endpoint for querying the cybersecurity RAG knowledge base."""
    if not query:
        raise HTTPException(status_code=400, detail="Query string is required")
    chunks = retriever.retrieve(query=query, top_k=top_k)
    return {"query": query, "results": chunks}
