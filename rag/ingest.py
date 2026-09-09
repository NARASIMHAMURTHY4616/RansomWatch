"""
RAG Ingestion pipeline for RansomWatch.
Parses markdown knowledge base documents, chunks sections, builds normalized vector embeddings,
and serializes the index to rag/vector_store/.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from config.settings import settings


def parse_and_chunk_markdown(file_path: Path) -> List[Dict[str, Any]]:
    """Split a markdown document into semantic section chunks."""
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    chunks = []
    current_title = file_path.stem.replace("_", " ").title()
    current_section = "Overview"
    current_text = []

    for line in lines:
        if line.startswith("# "):
            current_title = line.lstrip("# ").strip()
        elif line.startswith("## ") or line.startswith("### "):
            # Flush previous section chunk if non-empty
            text_body = "\n".join(current_text).strip()
            if len(text_body) > 40:
                chunks.append({
                    "source": file_path.name,
                    "title": current_title,
                    "section": current_section,
                    "content": f"[{current_title} - {current_section}]\n{text_body}",
                })
            current_section = line.lstrip("# ").strip()
            current_text = []
        else:
            current_text.append(line)

    # Flush final chunk
    text_body = "\n".join(current_text).strip()
    if len(text_body) > 40:
        chunks.append({
            "source": file_path.name,
            "title": current_title,
            "section": current_section,
            "content": f"[{current_title} - {current_section}]\n{text_body}",
        })

    return chunks


def ingest_knowledge_base(
    kb_dir: Path | None = None,
    output_dir: Path | None = None,
) -> Dict[str, Any]:
    """Ingest markdown files, compute vector index, and persist to disk."""
    knowledge_dir = (kb_dir or settings.KNOWLEDGE_BASE_DIR).resolve()
    vector_dir = (output_dir or settings.VECTOR_STORE_DIR).resolve()
    vector_dir.mkdir(parents=True, exist_ok=True)

    md_files = list(knowledge_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No markdown documents found in {knowledge_dir}")

    print(f"[*] Ingesting {len(md_files)} knowledge base documents from: {knowledge_dir}")

    all_chunks = []
    for md_file in md_files:
        doc_chunks = parse_and_chunk_markdown(md_file)
        all_chunks.extend(doc_chunks)
        print(f"  - Parsed {md_file.name}: {len(doc_chunks)} chunks")

    corpus = [chunk["content"] for chunk in all_chunks]

    # Build TF-IDF vectorizer with unigrams + bigrams and sublinear term frequency
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
        norm="l2",
    )
    embeddings_matrix = vectorizer.fit_transform(corpus)

    # Persist artifacts
    store_bundle = {
        "vectorizer": vectorizer,
        "embeddings": embeddings_matrix,
        "chunks": all_chunks,
    }
    bundle_path = vector_dir / "knowledge_index.pkl"
    joblib.dump(store_bundle, bundle_path)

    # Also save human-readable chunks metadata
    metadata_path = vector_dir / "chunks_metadata.json"
    metadata_path.write_text(
        json.dumps(
            [
                {
                    "source": c["source"],
                    "section": c["section"],
                    "length": len(c["content"]),
                }
                for c in all_chunks
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[+] Knowledge base ingestion successful!")
    print(f"    - Total Chunks Indexed: {len(all_chunks)}")
    print(f"    - Vocabulary Size:      {len(vectorizer.vocabulary_)}")
    print(f"    - Saved Index:          {bundle_path}")

    return {
        "chunks_count": len(all_chunks),
        "index_path": str(bundle_path),
    }


if __name__ == "__main__":
    ingest_knowledge_base()
