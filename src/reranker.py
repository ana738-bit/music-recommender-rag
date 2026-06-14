# Import libraries
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.documents import Document

# Load env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# Step1:load the LLM model
def load_reranker():
    print("Loading Groq LLM reranker...")
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,              
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    print("Groq reranker ready")
    return llm


# Step2: Define the reranker
def build_rerank_prompt(query: str, docs: list) -> str:
    """
    Builds a prompt asking LLM to rank songs by relevance.
    Each song is summarized as: index, title, artist, mood, energy, snippet
    """
    songs_text = ""
    for i, doc in enumerate(docs):
        title = doc.metadata.get("title",   "Unknown")
        artist = doc.metadata.get("artist",  "Unknown")
        mood = doc.metadata.get("mood",    "Unknown")
        energy = doc.metadata.get("energy",  "Unknown")
        tags = doc.metadata.get("tags",    "")
        # Context for short lyrics
        content = doc.page_content[:200].replace("\n", " ")

        songs_text += f"""
    Song {i}:
    Title:   {title}
    Artist:  {artist}
    Mood:    {mood}
    Energy:  {energy}
    Tags:    {tags}
    Snippet: {content}
    """

    prompt = f"""You are a music expert. A user is looking for: "{query}"

Here are {len(docs)} candidate songs. Rank them from MOST to LEAST relevant to the user's request.

{songs_text}

Rules:
- Consider mood, energy, lyrics, and tags when ranking
- Return ONLY a valid JSON array of song indices in ranked order
- Most relevant song index first
- Include ALL {len(docs)} indices
- No explanation, no text, ONLY the JSON array

Example format: [3, 0, 7, 1, 5, 2, 8, 4, 6, 9]

Your ranking:"""

    return prompt


# Step3:Parse the LLM  response
def parse_ranking(response_text: str, docs: list) -> list:
    """
    Parses LLM JSON response into ranked Document list.
    Falls back to original order if parsing fails.
    """
    try:
        # Clean the response
        text = response_text.strip()

        # Find the json array from the response
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found in response")

        json_str = text[start:end]
        indices = json.loads(json_str)

        # Validate indices
        valid_indices = [
            i for i in indices
            if isinstance(i, int) and 0 <= i < len(docs)
        ]

        if not valid_indices:
            raise ValueError("No valid indices found")

        # Rebuild ranked docs
        ranked = []
        for rank, idx in enumerate(valid_indices):
            doc = docs[idx]
            doc.metadata["_rerank_score"] = len(valid_indices) - rank
            doc.metadata["_rerank_rank"] = rank + 1
            ranked.append(doc)

        print(f"   Parsed {len(ranked)} ranked songs from LLM response")
        return ranked

    except Exception as e:
        print(f" Parse failed: {e} — using original order")
        # Fallback(return to the original order with a dummy score)
        for rank, doc in enumerate(docs):
            doc.metadata["_rerank_score"] = len(docs) - rank
            doc.metadata["_rerank_rank"]  = rank + 1
        return docs


# Step4: Global model
_reranker_llm = None


def _initialize():
    global _reranker_llm
    if _reranker_llm is not None:
        return
    _reranker_llm = load_reranker()


# Step5: Integration
def rerank(query: str, docs: list, top_n: int = 3) -> list:
    """
    LLM-based reranking using Groq.

    Input:
        query  — user query string
        docs   — list of LangChain Documents from retriever
        top_n  — how many to keep (default 5)

    Output:
        top 5 LangChain Documents ranked by LLM relevance
        each doc has _rerank_score and _rerank_rank in metadata
    """
    _initialize()

    if not docs:
        print("No documents to rerank")
        return []

    print(f"\nReranking {len(docs)} songs for: '{query}'")

    # Build prompt
    prompt = build_rerank_prompt(query, docs)

    # Ask Groq to rank
    print("   Asking Groq LLM to rank songs...")
    response = _reranker_llm.invoke(prompt)
    response_text = response.content

    print(f"   LLM response: {response_text.strip()[:80]}...")

    # Parse ranking
    ranked_docs = parse_ranking(response_text, docs)

    # Take top N
    final = ranked_docs[:top_n]

    # Show results
    print(f"Reranked — top {len(final)} selected:")
    for i, doc in enumerate(final, 1):
        title = doc.metadata.get("title",         "Unknown")
        artist = doc.metadata.get("artist",        "Unknown")
        mood = doc.metadata.get("mood",          "Unknown")
        rscore = doc.metadata.get("_rerank_score", 0)
        print(f"   {i}. {title} — {artist} | {mood} | rerank score: {rscore}")

    return final


# Step6: Verify full pipeline
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent))
    from retriever import get_top_songs

    print("Testing reranker.py...\n")

    test_queries = [
        "sad songs for a rainy night",
        "party dance songs",
        "focus study calm music",
        "xyzabc123 gibberish query",
    ]

    for query in test_queries:
        print(f"\n{'='*55}")
        print(f"Query: '{query}'")

        # Step 1 — Retriever
        retriever_response = get_top_songs(query)

        if not retriever_response["found"]:
            print(f"{retriever_response['message']}")
            continue

        retriever_docs = retriever_response["results"]
        print(f"Retriever returned: {len(retriever_docs)} songs")

        # Step 2 — Reranker
        reranked_docs = rerank(query, retriever_docs, top_n=5)

        # Before vs After comparison
        print(f"\nBefore vs After Reranking:")
        print(f"{'Retriever Order':<35} {'Reranker Order':<35}")
        print("-" * 70)

        retriever_titles = [
            d.metadata.get("title", "?")[:30]
            for d in retriever_docs[:5]
        ]
        reranker_titles = [
            d.metadata.get("title", "?")[:30]
            for d in reranked_docs
        ]

        for i, (before, after) in enumerate(
            zip(retriever_titles, reranker_titles), 1
        ):
            changed = "←" if before != after else ""
            print(f"{i}. {before:<33} {i}. {after:<33} {changed}")

    print("\n\neranker.py verification complete!")