import os
import json
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import syncedlyrics
from dotenv import load_dotenv
from pathlib import Path

# ─── Load .env ────────────────────────────────────────────
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ─── Initialize Spotify ───────────────────────────────────
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

# ─── Step 1: Fetch songs from Spotify ─────────────────────
def fetch_spotify_songs(queries: list, max_songs: int = 120) -> list:
    songs = []

    query_mood_map = {
        "sad heartbreak songs":       {"mood": "Melancholic", "energy": "Low",    "danceability": 0.3},
        "happy upbeat feel good":     {"mood": "Happy",       "energy": "High",   "danceability": 0.8},
        "romantic love songs":        {"mood": "Romantic",    "energy": "Low",    "danceability": 0.4},
        "motivational workout songs": {"mood": "Energetic",   "energy": "High",   "danceability": 0.7},
        "rainy day chill music":      {"mood": "Melancholic", "energy": "Low",    "danceability": 0.2},
        "party dance hits":           {"mood": "Happy",       "energy": "High",   "danceability": 0.9},
        "late night drive songs":     {"mood": "Nostalgic",   "energy": "Low",    "danceability": 0.4},
        "focus study music":          {"mood": "Calm",        "energy": "Low",    "danceability": 0.2},
        "top pop hits 2024":          {"mood": "Happy",       "energy": "High",   "danceability": 0.7},
        "best hip hop rap songs":     {"mood": "Energetic",   "energy": "High",   "danceability": 0.8},
        "indie alternative rock":     {"mood": "Nostalgic",   "energy": "Medium", "danceability": 0.5},
        "lo-fi chill beats":          {"mood": "Calm",        "energy": "Low",    "danceability": 0.3},
        "angry breakup songs":        {"mood": "Angry",       "energy": "High",   "danceability": 0.4},
        "english acoustic songs":     {"mood": "Calm",        "energy": "Low",    "danceability": 0.3},
        "english pop ballads":        {"mood": "Romantic",    "energy": "Medium", "danceability": 0.4},
    }

    for query in queries:
        if len(songs) >= max_songs:
            break

        mood_data = query_mood_map.get(query, {
            "mood": "Neutral", "energy": "Medium", "danceability": 0.5
        })

        try:
            results = sp.search(q=query, type="track", limit=10, market="US")
            tracks = results["tracks"]["items"]

            for track in tracks:
                if len(songs) >= max_songs:
                    break
                try:
                    song = {
                        "title":        track["name"],
                        "artist":       track["artists"][0]["name"],
                        "album":        track["album"]["name"],
                        "preview_url":  track.get("preview_url", "") or "",
                        "cover_image":  track["album"]["images"][0]["url"] if track["album"]["images"] else "",
                        "track_id":     track.get("id", ""),
                        "mood":         mood_data["mood"],
                        "energy":       mood_data["energy"],
                        "danceability": mood_data["danceability"],
                        "popularity":   track.get("popularity", 0),
                        "lyrics":       "",
                        "tags":         [mood_data["mood"].lower(), query]
                    }
                    songs.append(song)
                    print(f"✅ Fetched: {song['title']} — {song['artist']} [{mood_data['mood']}]")

                except Exception as e:
                    print(f"⚠️ Skipped {track.get('name', '?')}: {e}")
                    continue

        except Exception as e:
            print(f"⚠️ Search failed for '{query}': {e}")
            continue

    return songs


# ─── Step 2: Fetch lyrics using syncedlyrics (no API key) ──
def fetch_lyrics(songs: list) -> list:
    for song in songs:
        try:
            query = f"{song['title']} {song['artist']}"
            raw = syncedlyrics.search(query)

            if raw:
                lines = raw.split("\n")
                clean_lines = []
                for line in lines:
                    # Remove LRC timestamps like [00:15.076]
                    line = re.sub(r'\[\d+:\d+\.\d+\]', '', line).strip()
                    # Skip Chinese/non-ASCII metadata lines and empty lines
                    if line and not any('\u4e00' <= c <= '\u9fff' for c in line):
                        clean_lines.append(line)

                song["lyrics"] = "\n".join(clean_lines[:50])
                print(f"🎵 Lyrics fetched: {song['title']}")
            else:
                song["lyrics"] = ""
                print(f"⚠️ No lyrics found: {song['title']}")

        except Exception as e:
            song["lyrics"] = ""
            print(f"⚠️ Skipped {song['title']}: {e}")

    return songs


# ─── Step 3: Build RAG document ───────────────────────────
def build_rag_document(song: dict) -> str:
    return f"""
Song: {song['title']}
Artist: {song['artist']}
Album: {song['album']}
Mood: {song['mood']}
Energy Level: {song['energy']}
Danceability: {song['danceability']}
Popularity: {song['popularity']}
Tags: {', '.join(song['tags'])}

Lyrics:
{song['lyrics'][:2000]}
""".strip()


# ─── Step 4: Save to JSON ─────────────────────────────────
def save_songs(songs: list, path: str = "data/songs_catalog.json"):
    os.makedirs("data", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved {len(songs)} songs to {path}")


# ─── Step 5: Print catalog summary ───────────────────────
def print_catalog(path: str = "data/songs_catalog.json"):
    with open(path, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print(f"\n{'='*60}")
    print(f"📊 CATALOG SUMMARY — {len(songs)} songs")
    print(f"{'='*60}\n")

    for i, song in enumerate(songs, 1):
        print(f"{i}. {song['title']} — {song['artist']}")
        print(f"   Mood: {song['mood']} | Energy: {song['energy']} | Popularity: {song['popularity']}")
        lyrics_preview = song['lyrics'][:80].replace('\n', ' ') if song['lyrics'] else "No lyrics"
        print(f"   Lyrics preview: {lyrics_preview}...")
        print()

    print(f"{'='*60}")
    print(f"✅ Total songs saved: {len(songs)}")
    print(f"{'='*60}")


# ─── Main ─────────────────────────────────────────────────
if __name__ == "__main__":

    SEARCH_QUERIES = [
        "sad heartbreak songs",
        "happy upbeat feel good",
        "romantic love songs",
        "motivational workout songs",
        "rainy day chill music",
        "party dance hits",
        "late night drive songs",
        "focus study music",
        "top pop hits 2024",
        "best hip hop rap songs",
        "indie alternative rock",
        "lo-fi chill beats",
        "angry breakup songs",
        "english acoustic songs",
        "english pop ballads",
    ]

    print("🎵 Fetching songs from Spotify...")
    songs = fetch_spotify_songs(SEARCH_QUERIES, max_songs=120)
    print(f"\n✅ Got {len(songs)} songs from Spotify")

    print("\n📝 Fetching lyrics via syncedlyrics...")
    songs = fetch_lyrics(songs)

    lyrics_count = sum(1 for s in songs if s['lyrics'])
    print(f"\n✅ {lyrics_count}/{len(songs)} songs have lyrics")

    print("\n📄 Building RAG documents...")
    for song in songs:
        song["rag_document"] = build_rag_document(song)

    save_songs(songs)
    print("\n🎉 fetch_songs.py complete!")

    print_catalog()