"""RAG (Retrieval-Augmented Generation) package for RansomWatch."""
# Keep package init lightweight to allow clean -m CLI execution

__all__ = ["ingest_knowledge_base", "RAGRetriever"]

def __getattr__(name):
    if name == "ingest_knowledge_base":
        from rag.ingest import ingest_knowledge_base
        return ingest_knowledge_base
    elif name == "RAGRetriever":
        from rag.retriever import RAGRetriever
        return RAGRetriever
    raise AttributeError(f"module {__name__} has no attribute {name}")
