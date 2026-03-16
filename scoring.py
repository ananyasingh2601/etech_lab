import pandas as pd
from database import query_database

def calculate_topic_importance(exam_questions, collection, model):
    topic_scores = {}
    for question in exam_questions:
        results = query_database(question, collection, model, n_results=3)
        if results and 'documents' in results and results['documents']:
            for chunk in results['documents'][0]:
                topic_scores[chunk] = topic_scores.get(chunk, 0) + 1
    return generate_score_dataframe(topic_scores)