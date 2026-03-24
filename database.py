import hashlib
import math

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

import chromadb
import os


class LocalFallbackEmbedder:
    """Small deterministic embedder used when sentence-transformers is unavailable."""

    def __init__(self, dim=384):
        self.dim = dim

    def _embed_text(self, text):
        vec = [0.0] * self.dim
        if not text:
            return vec

        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def encode(self, texts):
        try:
            import numpy as np

            return np.array([self._embed_text(text) for text in texts], dtype=float)
        except ImportError:
            # Return a tiny list-like object with .tolist() compatibility.
            class _SimpleArray(list):
                def tolist(self):
                    return list(self)

            return _SimpleArray([self._embed_text(text) for text in texts])


def load_model():
    """Loads the embedding model with a local fallback when transformers are unavailable."""
    if SentenceTransformer is not None:
        return SentenceTransformer("all-MiniLM-L6-v2")
    return LocalFallbackEmbedder()


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
        include=['embeddings', 'metadatas', 'documents', 'distances']
    )
    return results
