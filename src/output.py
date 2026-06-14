# import libraries
import json
import re
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError


# Define the schema using the pydantic
class SongRecommendation(BaseModel):
    title:      str = Field(description="Exact song title")
    artist:     str = Field(description="Exact artist name")
    reason:     str = Field(description="Why this matches the user's query")
    mood_match: str = Field(description="The mood this song captures")
    best_time:  str = Field(description="Best situation or time to listen")

    # Optional
    cover_image: Optional[str] = None
    track_id:    Optional[str] = None
    energy:      Optional[str] = None


# Step1: Extract the json array from the raw text
def extract_json_array(raw_text: str) -> str:
    """
    LLMs sometimes wrap JSON in markdown code blocks or add
    extra text before/after. This extracts just the array.
    """
    text = raw_text.strip()

    # Remove markdown code fences if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    start = text.find("[")
    end = text.rfind("]") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON array found in LLM response")

    return text[start:end]


# Step2: Parse
def parse_recommendations(raw_text: str) -> List[SongRecommendation]:
    """
    Main function — converts raw LLM string output into a list
    of validated SongRecommendation objects.

    Input:
        raw_text — LLM's raw .content string (from chain.py)

    Output:
        list of SongRecommendation objects (validated)
        Returns empty list if parsing fails completely.
    """
    try:
        json_str = extract_json_array(raw_text)
        raw_list = json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"⚠️  JSON extraction/parsing failed: {e}")
        return []

    recommendations = []
    for i, item in enumerate(raw_list):
        try:
            rec = SongRecommendation(**item)
            recommendations.append(rec)
        except ValidationError as e:
            print(f"Skipping song {i} — validation error: {e}")
            continue

    print(f"Parsed {len(recommendations)} valid recommendations")
    return recommendations


# Step3: Enritched recommendation with catalog
def enrich_recommendations(
    recommendations: List[SongRecommendation],
    reranked_docs: list
) -> List[SongRecommendation]:
    """
    Adds cover_image, track_id, energy from the reranked docs
    (since the LLM doesn't return these — only title/artist/reason etc).

    Matches by title (case-insensitive).

    Input:
        recommendations — output of parse_recommendations()
        reranked_docs    — Rajdeep's reranked LangChain Documents

    Output:
        same list, with extra fields filled in where matched
    """
    # Build lookup: title (lowercase) → metadata
    lookup = {}
    for doc in reranked_docs:
        title = doc.metadata.get("title", "").strip().lower()
        if title and title not in lookup:
            lookup[title] = doc.metadata

    for rec in recommendations:
        meta = lookup.get(rec.title.strip().lower())
        if meta:
            rec.cover_image = meta.get("cover_image")
            rec.track_id = meta.get("track_id")
            rec.energy = meta.get("energy")
        else:
            print(f"No catalog match found for '{rec.title}' — leaving extra fields empty")

    return recommendations


# Step4: Recommendation to dictionaries
def recommendations_to_dicts(recommendations: List[SongRecommendation]) -> List[dict]:
    """Converts list of SongRecommendation to list of plain dicts."""
    return [rec.model_dump() for rec in recommendations]


# Testing
if __name__ == "__main__":
    print("Testing output.py...\n")

    # Simulate a clean LLM response
    sample_response = """[
    {
        "title": "Cigarette Daydreams",
        "artist": "Cage The Elephant",
        "reason": "Its nostalgic, wistful tone matches a rainy reflective night perfectly.",
        "mood_match": "Nostalgic",
        "best_time": "Late night, alone with your thoughts"
    },
    {
        "title": "Rainy Day Loop",
        "artist": "SALES",
        "reason": "The soft melancholic melody mirrors the calm sadness of rain.",
        "mood_match": "Melancholic",
        "best_time": "Rainy afternoons or quiet evenings"
    }
]"""

    print("Testing parse_recommendations() with clean JSON...")
    recs = parse_recommendations(sample_response)
    for r in recs:
        print(f"  - {r.title} by {r.artist} | mood: {r.mood_match}")
    print()

    # Simulate LLM response wrapped in markdown
    messy_response = """Here are my recommendations:

```json
    [
    {
        "title": "Test Song",
        "artist": "Test Artist",
        "reason": "Just testing markdown wrapping.",
        "mood_match": "Happy",
        "best_time": "Anytime"
    }
    ]
```

Hope you enjoy!"""

    print("Testing parse_recommendations() with markdown-wrapped JSON...")
    recs2 = parse_recommendations(messy_response)
    for r in recs2:
        print(f"  - {r.title} by {r.artist}")
    print()

    # Test broken JSON
    print("Testing parse_recommendations() with broken JSON...")
    broken = "I'm sorry, I cannot recommend songs right now."
    recs3 = parse_recommendations(broken)
    print(f"  Result: {recs3} (should be empty list)")
    print()

    # Test enrichment
    print("Testing enrich_recommendations()...")
    from langchain_core.documents import Document

    fake_docs = [
        Document(
            page_content="...",
            metadata={
                "title": "Cigarette Daydreams",
                "artist": "Cage The Elephant",
                "cover_image": "https://example.com/cover.jpg",
                "track_id": "abc123",
                "energy": "Medium"
            }
        )
    ]
    enriched = enrich_recommendations(recs, fake_docs)
    for r in enriched:
        print(f"  - {r.title} | cover: {r.cover_image} | track_id: {r.track_id}")

    print("\noutput.py complete!")