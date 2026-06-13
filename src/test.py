import json

# Load the catalog
with open('data/songs_catalog.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)

# Debugging Arijit
arijit = [s for s in songs if 'arijit' in s.get('artist', '').lower()]
print(f'Arijit songs in catalog: {len(arijit)}')

# Debugging Bollywood
bollywood = [s for s in songs if 'bollywood' in ' '.join(s.get('tags', [])).lower()]
print(f'Bollywood songs in catalog: {len(bollywood)}')

# Print first 5 matches to verify structure
for s in bollywood[:5]:
    print(f'  - {s.get("title")} — {s.get("artist")}')