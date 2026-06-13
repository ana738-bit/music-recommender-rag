import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from chain import parse_recommendations

print("🚀 Testing full pipeline...\n")

test_queries = [
    "sad songs for rainy night",
    "party dance songs",
    "focus study music"
]

for query in test_queries:
    print(f"\n{'='*50}")
    print(f"Query: '{query}'")
    result = parse_recommendations(query)
    print(result)