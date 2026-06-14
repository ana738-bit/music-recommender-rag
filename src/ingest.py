import os
import json
import re
import shutil
from pathlib import Path
from dotenv import load_dotenv

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Load .env 
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Paths 
CATALOG_PATH = "data/songs_catalog.json"
CHROMA_DB_PATH = "./music_db"
COLLECTION_NAME = "songs"

# Step 1: Load songs
def load_songs(path: str = CATALOG_PATH) -> list:
    with open(path, "r", encoding="utf-8") as f:
        songs = json.load(f)
    print(f" Loaded {len(songs)} songs from {path}")
    return songs


# Step 2: Clean lyrics 
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\[ar:.*?\]', '', text)
    text = re.sub(r'\[ti:.*?\]', '', text)
    text = re.sub(r'\[al:.*?\]', '', text)
    text = re.sub(r'\[length:.*?\]', '', text)
    text = re.sub(r'\[re:.*?\]', '', text)
    text = re.sub(r'\[ve:.*?\]', '', text)
    text = re.sub(r'\[\d+:\d+\.\d+\]', '', text)
    text = re.sub(r'[\u4e00-\u9fff]+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# Step 3: Build Documents
def build_documents(songs: list) -> list:
    documents = []
    for song in songs:
        clean_lyrics = clean_text(song.get("lyrics", ""))
        content = f"""Song: {song['title']}
Artist: {song['artist']}
Album: {song['album']}
Mood: {song['mood']}
Energy Level: {song['energy']}
Danceability: {song['danceability']}
Popularity: {song['popularity']}
Tags: {', '.join(song.get('tags', []))}

Lyrics:
{clean_lyrics[:2000] if clean_lyrics else 'No lyrics available'}""".strip()

        metadata = {
            "title":        song["title"],
            "artist":       song["artist"],
            "album":        song["album"],
            "mood":         song["mood"],
            "energy":       song["energy"],
            "danceability": str(song["danceability"]),
            "popularity":   str(song["popularity"]),
            "cover_image":  song.get("cover_image", ""),
            "track_id":     song.get("track_id", ""),
            "tags":         ", ".join(song.get("tags", []))
        }
        documents.append(Document(page_content=content, metadata=metadata))

    print(f" Built {len(documents)} documents")
    return documents


# Step 4: Chunk 
def chunk_documents(documents: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    print(f"  Split into {len(chunks)} chunks")
    return chunks


# Step 5: Embed and Store 
def embed_and_store(chunks: list):
    print("\n Setting up ChromaDB...")

    # Clean existing DB
    if os.path.exists(CHROMA_DB_PATH):
        try:
            shutil.rmtree(CHROMA_DB_PATH)
            print("  Cleared existing ChromaDB")
        except PermissionError:
            print("  Delete music_db folder manually and rerun")
            exit()

    # Use ChromaDB's built-in default embedding function
    ef = embedding_functions.DefaultEmbeddingFunction()

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef
    )

    # Store in batches of 50
    batch_size = 50
    total = len(chunks)

    print(f" Storing {total} chunks in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = chunks[i:i+batch_size]
        collection.add(
            documents=[c.page_content for c in batch],
            metadatas=[c.metadata for c in batch],
            ids=[f"chunk_{i+j}" for j in range(len(batch))]
        )
        print(f"    Stored {min(i+batch_size, total)}/{total} chunks")

    final_count = collection.count()
    print(f"\n ChromaDB ready — {final_count} chunks stored at {CHROMA_DB_PATH}")
    return collection


# Step 6: Verify 
def verify_store():
    print("\n🔍 Verifying ChromaDB with test query...")

    ef = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=ef
    )

    results = collection.query(
        query_texts=["sad songs for rainy night"],
        n_results=3
    )

    print(f"\n Test query: 'sad songs for rainy night'")
    print(f"Top 3 results:\n")
    for i, (doc, meta) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0]
    ), 1):
        print(f"{i}. {meta['title']} — {meta['artist']}")
        print(f"   Mood: {meta['mood']} | Energy: {meta['energy']}")
        print(f"   Preview: {doc[:100]}...")
        print()

    total = collection.count()
    print(f" Total chunks in ChromaDB: {total}")


# Main 
if __name__ == "__main__":
    print(" Starting ingestion pipeline...\n")

    songs    = load_songs()
    documents = build_documents(songs)
    chunks   = chunk_documents(documents)
    embed_and_store(chunks)
    verify_store()

    print("\n ingest.py complete! ChromaDB is ready.")