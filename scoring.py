import pandas as pd
import numpy as np
from database import query_database

def calculate_topic_importance(exam_questions, collection, model, similarity_threshold=0.0):
    """Calculate topic importance with actual similarity scores."""
    topic_scores = {}
    for question in exam_questions:
        results = query_database(question, collection, model, n_results=5)
        
        if results and 'documents' in results and results['documents']:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            distances = results.get('distances', [[]])[0] if 'distances' in results else []
            
            # Convert distances to bounded similarity scores.
            # Chroma distance can vary by metric, so use 1/(1+d) for stable [0,1] values.
            for idx, (doc, meta) in enumerate(zip(docs, metas)):
                distance = distances[idx] if idx < len(distances) else None
                if distance is None:
                    similarity = 0.5
                else:
                    similarity = 1.0 / (1.0 + max(0.0, float(distance)))
                
                # Keep only matches above user-selected threshold.
                if similarity >= similarity_threshold:
                    if doc not in topic_scores:
                        topic_scores[doc] = {
                            "scores": [],
                            "source": meta["source"],
                            "page": meta["page"],
                            "year": extract_year_from_filename(meta["source"])
                        }
                    topic_scores[doc]["scores"].append(similarity)
    scored_df = generate_score_dataframe(topic_scores)

    # Adaptive fallback: if threshold filters everything out, return top available matches
    # from the same scored set to keep downstream analysis usable.
    if scored_df.empty and similarity_threshold > 0:
        topic_scores_no_filter = {}
        for question in exam_questions:
            results = query_database(question, collection, model, n_results=5)
            if not (results and 'documents' in results and results['documents']):
                continue

            docs = results['documents'][0]
            metas = results['metadatas'][0]
            distances = results.get('distances', [[]])[0] if 'distances' in results else []

            for idx, (doc, meta) in enumerate(zip(docs, metas)):
                distance = distances[idx] if idx < len(distances) else None
                if distance is None:
                    similarity = 0.5
                else:
                    similarity = 1.0 / (1.0 + max(0.0, float(distance)))

                if doc not in topic_scores_no_filter:
                    topic_scores_no_filter[doc] = {
                        "scores": [],
                        "source": meta["source"],
                        "page": meta["page"],
                        "year": extract_year_from_filename(meta["source"])
                    }
                topic_scores_no_filter[doc]["scores"].append(similarity)

        fallback_df = generate_score_dataframe(topic_scores_no_filter)
        return fallback_df.head(25)

    return scored_df

def extract_year_from_filename(filename):
    """Extract year from filename (e.g., 'exam_2023.pdf' -> 2023)."""
    import re
    match = re.search(r'(19|20)\d{2}', filename)
    return int(match.group()) if match else None

def calculate_gap_analysis(exam_results, all_lecture_chunks, model):
    """Identify lecture topics NOT covered in exams (topics to potentially skip)."""
    # Get all lecture topics that were matched in exam
    matched_topics = set(exam_results["Lecture Topic"].values) if not exam_results.empty else set()
    
    # In a real scenario, you'd query all lecture chunks not in matched_topics
    # For now, return low-coverage topics from the exam results
    df_copy = exam_results.copy()
    df_copy["Coverage_Pct"] = (df_copy["Relevance Score"] / df_copy["Relevance Score"].max() * 100) if not df_copy.empty else 0
    
    # Topics with near-zero similarity (below 5th percentile)
    gap_topics = df_copy[df_copy["Coverage_Pct"] < 5].copy()
    return gap_topics.sort_values(by="Coverage_Pct", ascending=True)

def calculate_year_over_year_trends(results_df):
    """Calculate trends across years for heatmap visualization."""
    if results_df.empty or "Year" not in results_df.columns:
        return pd.DataFrame()
    
    # Extract topic name (first word or main topic)
    results_df["Main_Topic"] = results_df["Topic Snippet"].str.split().str[0]
    
    # Create pivot table: years vs topics
    pivot_df = results_df.pivot_table(
        index="Main_Topic",
        columns="Year",
        values="Relevance Score",
        aggfunc="mean",
        fill_value=0
    )
    
    return pivot_df

def generate_score_dataframe(topic_scores):
    """Generate dataframe with similarity scores."""
    if not topic_scores: 
        return pd.DataFrame(columns=["Topic Snippet", "Relevance Score", "Similarity", "Max Similarity", "File", "Page", 
                                     "Lecture Topic", "Year"])
    
    data = []
    for topic, info in topic_scores.items():
        avg_similarity = np.mean(info["scores"]) if info["scores"] else 0
        max_similarity = max(info["scores"]) if info["scores"] else 0
        data.append({
            "Lecture Topic": topic,
            "Relevance Score": len(info["scores"]),  # Count of matches
            "Similarity": round(avg_similarity, 3),  # Average similarity
            "Max Similarity": round(max_similarity, 3),
            "File": info["source"],
            "Page": info["page"],
            "Year": info["year"]
        })
        
    df = pd.DataFrame(data)
    df = df.sort_values(by="Similarity", ascending=False).reset_index(drop=True)
    df["Topic Snippet"] = df["Lecture Topic"].apply(lambda x: x[:80] + "...")
    return df[["Topic Snippet", "Relevance Score", "Similarity", "Max Similarity", "File", "Page", 
               "Lecture Topic", "Year"]]