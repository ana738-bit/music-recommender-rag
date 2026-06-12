# src/clean_catalog.py

import json
from pathlib import Path
from langdetect import detect, LangDetectException

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "songs_catalog.json"


def is_non_english(lyrics: str) -> bool:
    if not lyrics or len(lyrics.strip()) < 20:
        return True
    try:
        sample = lyrics[:500]
        lang = detect(sample)
        return lang != "en"
    except LangDetectException:
        return True


def clean_existing_catalog(path: Path = CATALOG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print(f"📂 Loaded {len(songs)} songs from existing catalog")

    english_only = []
    removed = []

    for song in songs:
        lyrics = song.get("lyrics", "")
        if is_non_english(lyrics):
            removed.append(song["title"])
            continue
        english_only.append(song)

    print(f"\n🚫 Removed {len(removed)} non-English / no-lyrics songs:")
    for t in removed:
        print(f"   - {t}")

    print(f"\n✅ {len(english_only)} songs remain")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(english_only, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved cleaned catalog back to {path}")
    return english_only


def print_catalog(path: Path = CATALOG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print(f"\n{'='*60}")
    print(f"📊 CATALOG SUMMARY — {len(songs)} songs")
    print(f"{'='*60}\n")

    for i, song in enumerate(songs, 1):
        lyrics_preview = song.get("lyrics", "")[:80].replace("\n", " ")
        print(f"{i}. {song['title']} — {song['artist']}")
        print(f"   Mood: {song['mood']} | Energy: {song['energy']} | Popularity: {song['popularity']}")
        print(f"   Lyrics preview: {lyrics_preview}...")
        print()

    print(f"{'='*60}")
    print(f"✅ Total verified songs: {len(songs)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    clean_existing_catalog()
    print_catalog()