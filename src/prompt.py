from pathlib import Path
from dotenv import load_dotenv

# ─── Load .env ────────────────────────────────────────────
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# ─── Query Rewriter Prompt ────────────────────────────────
REWRITE_PROMPT_TEMPLATE = """You are a music expert. Rewrite the user query into a detailed search query for finding matching songs.
Include mood, energy, tempo, genre, and emotion keywords.
Keep it under 30 words. Return only the rewritten query, nothing else.

User Query: {query}
Rewritten Query:"""


# ─── System Prompt ────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert music DJ and mood-based song recommender.
Your job is to recommend songs that perfectly match the user's mood, feeling, or situation.

You have been given retrieved song context below. Use ONLY these songs to make recommendations.
Do not invent songs that are not in the context.

For each recommended song explain:
- Why it matches the user mood or request
- What makes it special or unique  
- The best time or situation to listen to it

Be warm, conversational and enthusiastic like a real DJ.
Keep each song explanation to 2 sentences maximum."""


# ─── Output Format Prompt ─────────────────────────────────
OUTPUT_FORMAT = """Return ONLY a valid JSON array. No extra text before or after.

[
  {{
    "title":      "exact song title from context",
    "artist":     "exact artist name from context",
    "reason":     "why this matches the user query in 1-2 sentences",
    "mood_match": "the mood this song captures",
    "best_time":  "best situation or time to listen to this"
  }}
]

Rules:
- Return 3 songs maximum
- Only include songs that appear in the retrieved context
- No markdown, no explanation, only the JSON array"""


# ─── Build Context String from Reranked Docs ──────────────
def build_context(docs: list) -> str:
    """
    Converts list of reranked LangChain Documents
    into a clean context string for the LLM prompt.

    Called by chain.py with Rajdeep's reranked docs.
    """
    if not docs:
        return "No songs found."

    context_parts = []
    for i, doc in enumerate(docs, 1):
        title    = doc.metadata.get("title",   "Unknown")
        artist   = doc.metadata.get("artist",  "Unknown")
        mood     = doc.metadata.get("mood",    "Unknown")
        energy   = doc.metadata.get("energy",  "Unknown")
        tags     = doc.metadata.get("tags",    "")
        snippet  = doc.page_content[:300].replace("\n", " ")

        context_parts.append(f"""Song {i}:
Title:   {title}
Artist:  {artist}
Mood:    {mood}
Energy:  {energy}
Tags:    {tags}
Content: {snippet}""")

    return "\n\n".join(context_parts)


# ─── Build Final Prompt ───────────────────────────────────
def build_final_prompt(query: str, context: str, history: str) -> str:
    """
    Integration contract function.
    Called by chain.py (Rajdeep Stage 4).

    Input:
        query   — original user query string
        context — built by build_context() above
        history — formatted string from memory.py

    Output:
        complete prompt string ready for Groq LLM
    """
    history_section = ""
    if history and history != "No previous conversation.":
        history_section = f"""
Previous Conversation:
{history}
"""

    prompt = f"""{SYSTEM_PROMPT}

Retrieved Songs Context:
{context}
{history_section}
User Query: {query}

{OUTPUT_FORMAT}"""

    return prompt.strip()


# ─── Get Rewrite Prompt ───────────────────────────────────
def get_rewrite_prompt(query: str) -> str:
    """
    Returns filled rewrite prompt for query expansion.
    Called by chain.py before retrieval.
    """
    return REWRITE_PROMPT_TEMPLATE.format(query=query)


# ─── Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    from langchain_core.documents import Document

    print(" Testing prompt.py...\n")

    # Fake reranked docs to simulate Rajdeep's reranker output
    test_docs = [
        Document(
            page_content="Song: Cigarette Daydreams\nArtist: Cage The Elephant\nMood: Nostalgic\nLyrics: Did you stand there all alone...",
            metadata={
                "title": "Cigarette Daydreams",
                "artist": "Cage The Elephant",
                "mood": "Nostalgic",
                "energy": "Medium",
                "tags": "nostalgic, indie alternative rock",
                "_rerank_rank": 1,
                "_rerank_score": 3
            }
        ),
        Document(
            page_content="Song: Rainy Day Loop\nArtist: SALES\nMood: Melancholic\nLyrics: My world goes soft before the storm...",
            metadata={
                "title": "Rainy Day Loop",
                "artist": "SALES",
                "mood": "Melancholic",
                "energy": "Low",
                "tags": "melancholic, rainy day chill music",
                "_rerank_rank": 2,
                "_rerank_score": 2
            }
        )
    ]

    # Test build_context
    print(" Testing build_context()...")
    context = build_context(test_docs)
    print(context[:200])
    print("\n build_context works\n")

    # Test build_final_prompt
    print(" Testing build_final_prompt()...")
    prompt = build_final_prompt(
        query="sad songs for rainy night",
        context=context,
        history="No previous conversation."
    )
    print(prompt[:300])
    print("\n build_final_prompt works\n")

    # Test get_rewrite_prompt
    print(" Testing get_rewrite_prompt()...")
    rewrite = get_rewrite_prompt("sad songs for rainy night")
    print(rewrite)
    print("\n get_rewrite_prompt works\n")

    print(" prompt.py complete!")