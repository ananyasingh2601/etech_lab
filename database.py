from sentence_transformers import SentenceTransformer
import chromadb
import os


def load_model():
    """Loads the Sentence-BERT model."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def init_db(db_path="./chroma_db", collection_name="lectures"):
    """Sets up the local Vector Database."""
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=collection_name)
    return collection


def store_lecture(chunks, filename, collection, model):
    """Embeds lecture chunks and saves them to the database."""
    if not chunks:
        return
    embeddings = model.encode(chunks).tolist()
    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filename} for _ in chunks]

    collection.add(
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
        ids=ids,
    )


def query_database(query_text, collection, model, n_results=3):
    """Searches the database for lecture topics similar to the query."""
    # Embed the user query and search for the most similar lecture chunks.
    query_embedding = model.encode([query_text]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
    )
    return results
