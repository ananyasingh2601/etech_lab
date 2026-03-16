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
def generate_score_dataframe(topic_scores):
    if not topic_scores: return pd.DataFrame(columns=["Topic Snippet", "Relevance Score", "Lecture Topic"])
    df = pd.DataFrame(list(topic_scores.items()), columns=["Lecture Topic", "Relevance Score"])
    df = df.sort_values(by="Relevance Score", ascending=False).reset_index(drop=True)
    df["Topic Snippet"] = df["Lecture Topic"].apply(lambda x: x[:80] + "...")
    return df[["Topic Snippet", "Relevance Score", "Lecture Topic"]]