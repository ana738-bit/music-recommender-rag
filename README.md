# 🎵 VibeCheck — Music Mood Recommender

> Drop your mood. We drop the playlist. No algorithm. Just pure vibe science. ✨

A RAG (Retrieval Augmented Generation) powered music recommender system that recommends songs based on your mood, feeling, or situation using hybrid semantic search, LLM reranking, and conversational memory.

---

## 🎯 What Is This?

Most music apps recommend songs based on what you've listened to before. VibeCheck is different — you describe how you **feel**, and it finds songs that match that feeling.

**You type:** *"songs for a rainy night when you can't sleep"*  
**VibeCheck does:**
1. Rewrites your query into a rich semantic description
2. Searches 120 songs using hybrid BM25 + semantic search
3. Reranks the results using an LLM
4. Generates a personalized explanation for each recommendation
5. Returns 3 songs with Spotify playback — in under 10 seconds

---

## 🏗️ System Architecture

```
User Query
    │
    ▼
Query Rewriter (Groq LLM)
    │
    ▼
Hybrid Retrieval
    ├── BM25 Keyword Search      (20 candidates)
    └── ChromaDB Semantic Search (20 candidates)
    │
    ▼
Weighted Merge (80% semantic + 20% BM25)
    │
    ▼
LLM Reranker (Groq — top 3 selected)
    │
    ▼
Prompt Builder (context + conversation memory)
    │
    ▼
Groq LLM Generation (personalized explanations)
    │
    ▼
Pydantic Output Parser
    │
    ▼
Streamlit UI (song cards + Spotify embed)
```

---

## 🗂️ Project Structure

```
music-recommender-rag/
│
├── data/
│   └── songs_catalog.json       # 120 songs with lyrics + metadata
│
├── music_db/                    # ChromaDB vector store (441 chunks)
│
├── src/
│   ├── fetch_songs.py           # Stage 1 — Spotify + syncedlyrics data collection
│   ├── ingest.py                # Stage 1 — ChromaDB indexing pipeline
│   ├── retriever.py             # Stage 2 — Hybrid BM25 + semantic search
│   ├── reranker.py              # Stage 2 — LLM-based reranking
│   ├── prompt.py                # Stage 3 — Prompt engineering + context builder
│   ├── memory.py                # Stage 3 — Conversation memory (last 5 exchanges)
│   ├── chain.py                 # Stage 4 — Full RAG pipeline orchestration
│   └── output.py                # Stage 4 — Pydantic structured output parser
│
├── app.py                       # Streamlit UI
├── .env                         # API keys (create manually)
├── .env.example                 # API key template
├── requirements.txt
└── README.md
```

---

## ⚙️ RAG Pipeline — 4 Stages

### Stage 1 — Indexing (Ananya)
- Fetches 120 songs from Spotify API across 15 mood-based search queries
- Retrieves lyrics using `syncedlyrics` (no API key required)
- Cleans lyrics — removes timestamps, LRC metadata, non-English characters
- Assembles rich RAG documents combining title, artist, mood, energy, lyrics, tags
- Chunks documents using `RecursiveCharacterTextSplitter` (500 tokens, 50 overlap)
- Embeds and stores 441 chunks in ChromaDB using `DefaultEmbeddingFunction`

### Stage 2 — Retrieval (Rajdeep)
- Loads all 441 chunks and builds a BM25 index for keyword search
- Implements ChromaDB semantic search using cosine similarity
- Merges results using weighted hybrid scoring (80% semantic + 20% BM25)
- LLM reranker (Groq `llama-3.1-8b-instant`) selects top 3 from top 10 candidates

### Stage 3 — Augmentation (Ananya)
- Query rewriter expands user mood into natural language semantic description
- Context builder formats reranked songs into structured prompt context
- Conversation memory stores last 5 exchanges for multi-turn refinement

### Stage 4 — Generation (Rajdeep)
- Full RAG chain orchestrates all 8 pipeline steps end-to-end
- Groq LLM (`llama-3.1-8b-instant`) generates personalized explanations per song
- Pydantic parser validates and structures LLM JSON output
- Enriches recommendations with catalog metadata (cover image, Spotify track ID)

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| LLM | Groq (`llama-3.1-8b-instant`) — free tier |
| Vector Database | ChromaDB (local persistent) |
| Embeddings | ChromaDB DefaultEmbeddingFunction |
| Keyword Search | BM25 (`rank-bm25`) |
| RAG Framework | LangChain + LangChain Community |
| Data Sources | Spotify API + syncedlyrics |
| Output Validation | Pydantic |
| UI | Streamlit |
| Environment | python-dotenv |

---

## 📊 By The Numbers

| Metric | Value |
|---|---|
| Songs in catalog | 120 |
| Chunks in ChromaDB | 441 |
| Mood categories | 15 |
| LLM calls per query | 2 (reranker + generator) |
| Conversation memory | 5 exchanges |
| Average response time | ~8 seconds |
| Songs with lyrics | 93 / 120 |

---

## 🚀 Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/ana738-bit/music-recommender-rag.git
cd music-recommender-rag
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```

Fill in your `.env` file:
```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
GROQ_API_KEY=your_groq_api_key
```

**Get your API keys:**
- Spotify → https://developer.spotify.com/dashboard
- Groq → https://console.groq.com

### 5. Build the data pipeline (one-time setup)
```bash
# Fetch 120 songs from Spotify + lyrics
python src/fetch_songs.py

# Embed and store in ChromaDB
python src/ingest.py
```

### 6. Run the app
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 🧪 Testing Individual Components

```bash
# Test retrieval pipeline
python src/retriever.py

# Test reranker
python src/reranker.py

# Test full RAG chain
python src/chain.py

# Test output parser
python src/output.py
```

---

## 💡 Example Queries

| Query | What VibeCheck Does |
|---|---|
| `sad songs for a rainy night` | Returns melancholic, low-energy tracks with reflective lyrics |
| `something to get me pumped for the gym` | Returns high-energy, motivational hip-hop and pop |
| `music for late night studying` | Returns calm, instrumental or lo-fi tracks |
| `heartbreak but make it angry` | Distinguishes angry-sad from plain sad |
| `more upbeat please` | Uses conversation memory to shift vibe from previous query |

---

## 👥 Team

### Ananya Manna — Data Science Noob · Stage 1 & 3 Architect
Built the complete data ingestion pipeline — collecting 120 songs across Spotify and syncedlyrics, cleaning lyrics, and assembling rich RAG documents. Designed the ChromaDB indexing strategy with 441 chunks and engineered the prompt templates and conversation memory system that powers every recommendation.

### Rajdeep Bose — Data Science Noob · Stage 2 & 4 Architect
Built the complete retrieval pipeline — hybrid search combining BM25 keyword matching and ChromaDB semantic search, fused using weighted scoring. Designed the LLM-based reranker using Groq, structured output parsing with Pydantic, and the RAG chain that orchestrates all 8 pipeline stages from query to final recommendation.

---

## 🎓 About This Project

Built as a Semester 4 project at MAKAUT. We wanted to build something that used real RAG, real LLMs, and real APIs — not another CRUD app. VibeCheck is the result.

---

*Made with ☕ + 🎧 + way too many late nights by Ananya & Rajdeep*  
*Data Science Students · 2026*