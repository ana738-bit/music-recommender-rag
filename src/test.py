import chromadb
from chromadb.utils import embedding_functions

CHROMA_DB_PATH = "./music_db"
COLLECTION_NAME = "songs"

def inspect_vectors():
    print("🔍 Inspecting ChromaDB Embeddings and Documents...\n")
    
    ef = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

    # Fetch 2 items from the database, explicitly requesting embeddings
    results = collection.get(
        limit=2, 
        include=["documents", "metadatas", "embeddings"]
    )

    if not results["ids"]:
        print("No documents found in the database.")
        return

    for i in range(len(results["ids"])):
        doc_id = results["ids"][i]
        meta = results["metadatas"][i]
        doc = results["documents"][i]
        embedding = results["embeddings"][i]
        
        print(f"ID: {doc_id}")
        print(f"Title: {meta['title']} — {meta['artist']}")
        print(f"Document Snippet: {doc[:100].replace('\n', ' ')}...")
        
        # Displaying the mathematical representation
        print(f"Embedding Vector Length: {len(embedding)} dimensions")
        
        # Round the floats for cleaner display
        rounded_vector = [round(val, 5) for val in embedding[:5]]
        print(f"Embedding Preview: {rounded_vector} ...")
        print("-" * 60)

if __name__ == "__main__":
    inspect_vectors()