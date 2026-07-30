import sys
import os
from pathlib import Path

# ─── Path Setup ───────────────────────────────────────────
# Allow backend/main.py to import from src/
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR  = ROOT_DIR / "src"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SRC_DIR))

# ─── Change working directory to project root ─────────────
# Ensures ./music_db path works correctly on Render
os.chdir(ROOT_DIR)

# ─── Imports ──────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from chain import run_pipeline
from memory import reset_memory, get_all_sessions


# ════════════════════════════════════════════════════════════
# FastAPI App
# ════════════════════════════════════════════════════════════
app = FastAPI(
    title="VibeCheck API",
    description="RAG-powered music mood recommender backend",
    version="1.0.0"
)

# ─── CORS Middleware ──────────────────────────────────────
# Allow all origins for demo project
# Covers Streamlit Cloud + localhost development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════
# Request / Response Models
# ════════════════════════════════════════════════════════════
class RecommendRequest(BaseModel):
    query:      str
    session_id: Optional[str] = "default"


class ClearMemoryRequest(BaseModel):
    session_id: Optional[str] = "default"


class RecommendResponse(BaseModel):
    found:            bool
    message:          str
    query:            str
    rewritten_query:  str
    recommendations:  list
    raw_llm_response: str


# ════════════════════════════════════════════════════════════
# Endpoints
# ════════════════════════════════════════════════════════════

# ─── Health Check ─────────────────────────────────────────
@app.get("/health")
def health_check():
    """
    UptimeRobot pings this every 5 minutes to keep
    Render free tier from spinning down.
    """
    return {
        "status":  "ok",
        "service": "VibeCheck API"
    }


# ─── Stats ────────────────────────────────────────────────
@app.get("/stats")
def get_stats():
    """
    Returns basic stats about the pipeline.
    Displayed on About page.
    """
    return {
        "total_songs":      120,
        "total_chunks":     441,
        "mood_categories":  15,
        "model":            "llama-3.1-8b-instant",
        "embedding_model":  "all-MiniLM-L6-v2",
        "retrieval_weights": "80% semantic + 20% BM25",
        "active_sessions":  len(get_all_sessions())
    }


# ─── Recommend ────────────────────────────────────────────
@app.post("/recommend")
def recommend(request: RecommendRequest):
    """
    Main endpoint. Streamlit calls this for every query.
    Runs the full 8-stage RAG pipeline and returns
    structured song recommendations.
    """
    # Validate query
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    print(f"\n📥 /recommend — session: {request.session_id}")
    print(f"   Query: '{request.query}'")

    try:
        result = run_pipeline(
            query=request.query.strip(),
            session_id=request.session_id or "default"
        )
        return result

    except Exception as e:
        print(f"Pipeline error: {e}")
        return {
            "found":            False,
            "message":          f"Pipeline error: {str(e)}. Please try again.",
            "query":            request.query,
            "rewritten_query":  request.query,
            "recommendations":  [],
            "raw_llm_response": ""
        }


# ─── Clear Memory ─────────────────────────────────────────
@app.post("/clear-memory")
def clear_memory(request: ClearMemoryRequest):
    """
    Called when user clicks Clear History in Streamlit UI.
    Resets only the memory for the given session_id.
    """
    session_id = request.session_id or "default"
    print(f"\n🗑️ /clear-memory — session: {session_id}")

    try:
        reset_memory(session_id)
        return {
            "status":     "memory cleared",
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear memory: {str(e)}"
        )


# ─── Root ─────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "🎵 VibeCheck API is running!",
        "docs":    "/docs",
        "health":  "/health",
        "stats":   "/stats"
    }
