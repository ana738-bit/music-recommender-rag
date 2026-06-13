import os
from pathlib import Path
from dotenv import load_dotenv

import chromadb
from chromadb.utils import embedding_functions

from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

# ─── Load .env ────────────────────────────────────────────
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ─── Paths ────────────────────────────────────────────────
CHROMA_DB_PATH  = "./music_db"
COLLECTION_NAME = "songs"


# ════════════════════════════════════════════════════════════
# STEP 1 — Connect to ChromaDB
# ════════════════════════════════════════════════════════════
def get_chroma_collection():
    print("Connecting to ChromaDB...")
    ef     = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=ef
    )
    print(f"Connected — {collection.count()} chunks found")
    return collection


# ════════════════════════════════════════════════════════════
# STEP 2 — Pull all chunks as LangChain Documents (for BM25)
# ════════════════════════════════════════════════════════════
def load_chunks_as_documents(collection) -> list:
    print("\nLoading all chunks from ChromaDB...")
    results   = collection.get(include=["documents", "metadatas"])
    documents = []
    for content, meta in zip(results["documents"], results["metadatas"]):
        documents.append(Document(page_content=content, metadata=meta))
    print(f"Loaded {len(documents)} chunks as LangChain Documents")
    return documents


# ════════════════════════════════════════════════════════════
# STEP 3 — BM25 Retriever (Keyword Search)
# ════════════════════════════════════════════════════════════
def build_bm25_retriever(documents: list) -> BM25Retriever:
    print("\nBuilding BM25 keyword retriever...")
    bm25          = BM25Retriever.from_documents(documents)
    bm25.k        = 20
    print("BM25 retriever ready")
    return bm25


# ════════════════════════════════════════════════════════════
# STEP 4 — ChromaDB Semantic Retriever
# ════════════════════════════════════════════════════════════
class ChromaRetriever:
    def __init__(self, collection, k: int = 20):
        self.collection = collection
        self.k          = k
        print("ChromaDB semantic retriever ready")

    def get_relevant_documents(self, query: str) -> list:
        results   = self.collection.query(
            query_texts=[query],
            n_results=self.k,
            include=["documents", "metadatas", "distances"]
        )
        documents = []
        for content, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            similarity              = 1 - distance
            doc                     = Document(page_content=content, metadata=meta)
            doc.metadata["_semantic_score"] = round(similarity, 4)
            documents.append(doc)
        return documents


def build_semantic_retriever(collection) -> ChromaRetriever:
    print("\nBuilding ChromaDB semantic retriever...")
    return ChromaRetriever(collection, k=20)


# ════════════════════════════════════════════════════════════
# STEP 5 — Catalog Check
# ════════════════════════════════════════════════════════════
def is_in_catalog(semantic_results: list) -> bool:
    if not semantic_results:
        return False
    best_score = max(
        doc.metadata.get("_semantic_score", 0)
        for doc in semantic_results
    )
    THRESHOLD = 0.10
    print(f"   Best semantic score: {best_score:.4f} (threshold: {THRESHOLD})")
    return best_score >= THRESHOLD

# ════════════════════════════════════════════════════════════
# STEP 6 — Weighted Hybrid Merge
# Semantic 80% + BM25 20%
# ════════════════════════════════════════════════════════════
def weighted_merge(semantic_results: list, bm25_results: list) -> list:
    scores = {}
    docs   = {}

    # Semantic — 80% weight using actual similarity score
    for doc in semantic_results:
        title  = doc.metadata.get("title", "")
        score  = doc.metadata.get("_semantic_score", 0)
        scores[title] = scores.get(title, 0) + (0.8 * score)
        docs[title]   = doc

    # BM25 — 20% weight using rank position
    total = len(bm25_results)
    for rank, doc in enumerate(bm25_results):
        title      = doc.metadata.get("title", "")
        bm25_score = (total - rank) / total
        scores[title] = scores.get(title, 0) + (0.2 * bm25_score)
        if title not in docs:
            docs[title] = doc

    # Sort by combined score
    ranked = sorted(scores, key=lambda t: scores[t], reverse=True)

    result = []
    for title in ranked:
        doc = docs[title]
        doc.metadata["_hybrid_score"] = round(scores[title], 4)
        result.append(doc)

    return result


# ════════════════════════════════════════════════════════════
# STEP 7 — Globals + Initialize (run once)
# ════════════════════════════════════════════════════════════
_collection         = None
_bm25_retriever     = None
_semantic_retriever = None


def _initialize():
    global _collection, _bm25_retriever, _semantic_retriever
    if _bm25_retriever is not None:
        return
    _collection         = get_chroma_collection()
    all_chunks          = load_chunks_as_documents(_collection)
    _bm25_retriever     = build_bm25_retriever(all_chunks)
    _semantic_retriever = build_semantic_retriever(_collection)


# ════════════════════════════════════════════════════════════
# STEP 8 — Main Integration Function
# Called by chain.py — returns dict with found + results
# ════════════════════════════════════════════════════════════
def get_top_songs(query: str) -> dict:
    """
    Hybrid search: 80% semantic + 20% BM25.
    Returns dict:
    {
        "found":   True/False,
        "message": error message if not found,
        "results": list of top 10 LangChain Documents
    }
    """
    _initialize()

    print(f"\n🔍 Searching for: '{query}'")

    semantic_results = _semantic_retriever.get_relevant_documents(query)
    bm25_results     = _bm25_retriever.invoke(query)

    # Check catalog relevance
    if not is_in_catalog(semantic_results):
        print("❌ Query not relevant to catalog — using fallback")
        # FALLBACK — return best available results anyway
        combined = weighted_merge(semantic_results, bm25_results)
        combined = [
            doc for doc in combined
            if doc.metadata.get("_hybrid_score", 0) > 0
        ]
        final = combined[:10]
        if final:
            print(f"✅ Fallback found {len(final)} songs")
            return {
                "found":   True,
                "message": "",
                "results": final
            }
        return {
            "found":   False,
            "message": f"Sorry, we couldn't find songs matching '{query}'. Try a different mood!",
            "results": []
        }

# ════════════════════════════════════════════════════════════
# STEP 9 — Verify
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🚀 Testing retriever.py...\n")

    test_queries = [
        "sad songs for a rainy night",
        "hip-hop songs",
        "party dance songs",
        "focus study calm music",
        "disco",
    ]

    for query in test_queries:
        print(f"\n{'='*55}")
        response = get_top_songs(query)

        if not response["found"]:
            print(f"\n⚠️  {response['message']}")
            continue

        print(f"\nQuery : '{query}'")
        print(f"Results ({len(response['results'])}):")
        for i, doc in enumerate(response["results"], 1):
            title  = doc.metadata.get("title",         "Unknown")
            artist = doc.metadata.get("artist",        "Unknown")
            mood   = doc.metadata.get("mood",          "Unknown")
            score  = doc.metadata.get("_hybrid_score", 0)
            print(f"  {i}. {title} — {artist} | {mood} | score: {score}")

    print("\n\n✅ retriever.py verification complete!")