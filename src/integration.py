# integration.py
# ─────────────────────────────────────────────────────────
# This file defined the integration contracts between stages.
# All contracts have been implemented directly in:
#
#   get_top_songs()        → src/retriever.py
#   build_final_prompt()   → src/prompt.py
#   get_memory()           → src/memory.py
#   parse_recommendations()→ src/output.py
#   CHROMA_DB_PATH         → src/retriever.py + src/ingest.py
#   COLLECTION_NAME        → src/retriever.py + src/ingest.py
#
# chain.py connects all stages via direct imports.
# ─────────────────────────────────────────────────────────

CHROMA_DB_PATH  = "./music_db"
COLLECTION_NAME = "songs"