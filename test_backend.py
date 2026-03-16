import os
from processing import process_lecture
from database import load_model, init_db, store_lecture, query_database

print("Loading AI Model and DB...")
model = load_model()
collection = init_db()

print("Backend framework is ready for testing with real PDFs!")