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


def store_lecture(chunks_data, filename, collection, model):
    """Embeds chunks and saves them along with file and page metadata."""
    if not chunks_data: return
    
    # Extract just the text strings for the AI model
    chunks = [item["chunk"] for item in chunks_data]
    embeddings = model.encode(chunks).tolist()
    
    # Create unique IDs and save the page/source info
    ids = [f"{filename}_p{item['page']}_{i}" for i, item in enumerate(chunks_data)]
    metadatas = [{"source": filename, "page": item["page"]} for item in chunks_data]
    
    collection.add(
        embeddings=embeddings, 
        documents=chunks, 
        metadatas=metadatas, 
        ids=ids
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
