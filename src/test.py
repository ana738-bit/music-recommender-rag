# quick_check.py
import chromadb
from chromadb.utils import embedding_functions

ef = embedding_functions.DefaultEmbeddingFunction()
client = chromadb.PersistentClient(path="./music_db")
collection = client.get_collection(name="songs", embedding_function=ef)

result = collection.get(limit=1, include=["metadatas"])
print(result["metadatas"][0])