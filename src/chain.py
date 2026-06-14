# Imports
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from retriever import get_top_songs
from reranker import rerank
from prompt import get_rewrite_prompt, build_context, build_final_prompt
from memory import get_memory
from output import parse_recommendations, enrich_recommendations, recommendations_to_dicts

# Load env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# setp1: Load main generation LLM
_chain_llm = None

def _get_chain_llm():
    global _chain_llm
    if _chain_llm is None:
        print("Loading Groq LLM for chain...")
        _chain_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.7,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        print("Chain LLM ready")
    return _chain_llm


# setp2: Query rewritting
def rewrite_query(query: str) -> str:
    """
    Expands user query into a richer search query using LLM.
    Falls back to original query if rewriting fails.
    """
    try:
        llm = _get_chain_llm()
        rewrite_prompt = get_rewrite_prompt(query)
        response = llm.invoke(rewrite_prompt)
        rewritten = response.content.strip()

        if not rewritten:
            return query

        print(f"   Query rewritten: '{query}' → '{rewritten}'")
        return rewritten

    except Exception as e:
        print(f"Query rewrite failed: {e} — using original query")
        return query


# Step3: Main pipeline rub
def run_pipeline(query: str, use_memory: bool = True, use_rewrite: bool = True) -> dict:
    """
    Full RAG pipeline:
    query → rewrite → retrieve → rerank → context → memory →
    prompt → LLM → parse → enrich → save memory

    Input:
        query       — raw user query string
        use_memory  — whether to inject conversation history
        use_rewrite — whether to do query expansion first

    Output:
        {
            "found":           bool,
            "message":         str (error message if not found),
            "query":           original user query,
            "rewritten_query": expanded query (or same if skipped),
            "recommendations": list of dicts (song recs),
            "raw_llm_response": raw LLM text (for debugging)
        }
    """
    print(f"\n{'='*60}")
    print(f"🎵 PIPELINE START — Query: '{query}'")
    print(f"{'='*60}")

    # Step 1: Query Rewriting
    if use_rewrite:
        print("\n[1/8] Rewriting query...")
        search_query = rewrite_query(query)
    else:
        search_query = query
        print("\n[1/8] Skipping query rewrite")

    # Step 2: Retrieval
    print("\n[2/8] Retrieving candidates (hybrid search)...")
    retriever_response = get_top_songs(search_query)

    if not retriever_response["found"]:
        print(f"{retriever_response['message']}")
        return {
            "found":           False,
            "message":         retriever_response["message"],
            "query":           query,
            "rewritten_query": search_query,
            "recommendations": [],
            "raw_llm_response": ""
        }

    retrieved_docs = retriever_response["results"]
    print(f"   Retrieved {len(retrieved_docs)} candidates")

    # Step 3: Reranking
    print("\n[3/8] Reranking with LLM...")
    reranked_docs = rerank(search_query, retrieved_docs, top_n=3)

    if not reranked_docs:
        return {
            "found":           False,
            "message":         "Reranking failed — no songs to recommend.",
            "query":           query,
            "rewritten_query": search_query,
            "recommendations": [],
            "raw_llm_response": ""
        }

    # Step 4: Build Context 
    print("\n[4/8] Building context from reranked songs...")
    context = build_context(reranked_docs)

    # Step 5: Get Memory
    print("\n[5/8] Loading conversation memory...")
    memory = get_memory()
    history = memory.format() if use_memory else "No previous conversation."
    print(f"   History: {history[:80]}...")

    # Step 6: Build Final Prompt
    print("\n[6/8] Building final prompt...")
    final_prompt = build_final_prompt(query=query, context=context, history=history)

    # Step 7: Call Groq LLM 
    print("\n[7/8] Calling Groq LLM for recommendations...")
    try:
        llm = _get_chain_llm()
        llm_response = llm.invoke(final_prompt)
        raw_text = llm_response.content
        print(f"   LLM response: {raw_text.strip()[:80]}...")
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return {
            "found":           False,
            "message":         f"LLM generation failed: {str(e)}",
            "query":           query,
            "rewritten_query": search_query,
            "recommendations": [],
            "raw_llm_response": ""
        }

    # Step 8: Parse + Enrich Output 
    print("\n[8/8] Parsing and enriching output...")
    recommendations = parse_recommendations(raw_text)

    if not recommendations:
        return {
            "found":           False,
            "message":         "Couldn't parse song recommendations. Please try again.",
            "query":           query,
            "rewritten_query": search_query,
            "recommendations": [],
            "raw_llm_response": raw_text
        }

    recommendations = enrich_recommendations(recommendations, reranked_docs)
    recommendations_dicts = recommendations_to_dicts(recommendations)

    # Save to Memory
    if use_memory:
        summary = ", ".join([r["title"] for r in recommendations_dicts])
        memory.save(query, f"Recommended: {summary}")

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE — {len(recommendations_dicts)} recommendations")
    print(f"{'='*60}\n")

    return {
        "found":           True,
        "message":         "",
        "query":           query,
        "rewritten_query": search_query,
        "recommendations": recommendations_dicts,
        "raw_llm_response": raw_text
    }


#Test
if __name__ == "__main__":
    print("🚀 Testing chain.py — Full Pipeline\n")

    test_queries = [
        "sad songs for a rainy night",
        "more upbeat please",          # tests memory continuity
        "xyzabc123 gibberish query",   # tests not-found path
    ]

    for query in test_queries:
        result = run_pipeline(query)

        print(f"\n{'#'*60}")
        print(f"QUERY: '{result['query']}'")
        print(f"REWRITTEN: '{result['rewritten_query']}'")

        if not result["found"]:
            print(f"NOT FOUND: {result['message']}")
            continue

        print(f"RECOMMENDATIONS ({len(result['recommendations'])}):")
        for i, rec in enumerate(result["recommendations"], 1):
            print(f"\n  {i}. {rec['title']} by {rec['artist']}")
            print(f"     Mood match: {rec['mood_match']}")
            print(f"     Reason: {rec['reason']}")
            print(f"     Best time: {rec['best_time']}")
            print(f"     Cover: {rec.get('cover_image')}")
            print(f"     Track ID: {rec.get('track_id')}")
        print(f"{'#'*60}")

    print("\n\nchain.py complete!")