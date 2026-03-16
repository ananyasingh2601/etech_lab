from sentence_transformers import SentenceTransformer
import chromadb
import os

def load_model():
    """Loads the Sentence-BERT model."""
    return SentenceTransformer('all-MiniLM-L6-v2')