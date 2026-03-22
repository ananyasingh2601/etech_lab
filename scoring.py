import pandas as pd
from database import query_database

def calculate_topic_importance(exam_questions, collection, model):
    topic_scores = {}
    for question in exam_questions:
        results = query_database(question, collection, model, n_results=3)
        
        if results and 'documents' in results and results['documents']:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            
            # Zip allows us to loop through the text and its metadata simultaneously
            for doc, meta in zip(docs, metas):
                if doc not in topic_scores:
                    topic_scores[doc] = {"score": 0, "source": meta["source"], "page": meta["page"]}
                topic_scores[doc]["score"] += 1

    return generate_score_dataframe(topic_scores)

def generate_score_dataframe(topic_scores):
    if not topic_scores: 
        return pd.DataFrame(columns=["Topic Snippet", "Relevance", "File", "Page", "Lecture Topic"])
    
    data = []
    for topic, info in topic_scores.items():
        data.append({
            "Lecture Topic": topic,
            "Relevance": info["score"],
            "File": info["source"],
            "Page": info["page"]
        })
        
    df = pd.DataFrame(data)
    df = df.sort_values(by="Relevance", ascending=False).reset_index(drop=True)
    df["Topic Snippet"] = df["Lecture Topic"].apply(lambda x: x[:80] + "...")
    return df[["Topic Snippet", "Relevance", "File", "Page", "Lecture Topic"]]