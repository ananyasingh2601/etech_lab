import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_bar_chart(df):
    if df.empty: return None
    fig = px.bar(
        df.head(10), 
        x="Topic Snippet", 
        y="Similarity",  # Changed to show similarity scores instead of just counts
        title="Top 10 Most Similar Topics",
        color="Similarity",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(xaxis_tickangle=-45, height=500)
    return fig

def create_pie_chart(df):
    if df.empty: return None
    return px.pie(
        df.head(10), 
        names="Topic Snippet", 
        values="Relevance Score", 
        title="Topic Distribution", 
        hole=0.4
    )

def create_gap_analysis_chart(gap_df):
    """Create a horizontal bar chart showing topics NOT covered (the skip list)."""
    if gap_df.empty:
        return None
    
    fig = px.barh(
        gap_df.head(15),
        y="Topic Snippet",
        x="Coverage_Pct",
        title="Gap Analysis: Topics to SKIP (Low Coverage)",
        color="Coverage_Pct",
        color_continuous_scale="Reds_r",
        labels={"Coverage_Pct": "Coverage %", "Topic Snippet": "Topic"}
    )
    fig.update_layout(height=500, yaxis_tickfont=dict(size=10))
    return fig

def create_year_over_year_heatmap(year_trends_df):
    """Create a heatmap showing how topic focus has shifted across years."""
    if year_trends_df.empty:
        return None
    
    # Ensure numeric values
    heatmap_data = year_trends_df.fillna(0).astype(float)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='YlOrRd',
        colorbar=dict(title="Avg Similarity")
    ))
    
    fig.update_layout(
        title="Year-over-Year Topic Trends (Heatmap)",
        xaxis_title="Year",
        yaxis_title="Topic",
        height=600,
        font=dict(size=10)
    )
    return fig

def create_similarity_distribution_chart(df):
    """Create a histogram showing the distribution of similarity scores."""
    if df.empty or "Similarity" not in df.columns:
        return None
    
    fig = px.histogram(
        df,
        x="Similarity",
        nbins=20,
        title="Distribution of Similarity Scores",
        labels={"Similarity": "Similarity Score", "count": "Count"},
        color_discrete_sequence=["#636EFA"]
    )
    fig.update_layout(height=400, showlegend=False)
    return fig

def create_confidence_scatter(df):
    """Create a scatter plot of Relevance vs Similarity for confidence analysis."""
    if df.empty:
        return None
    
    fig = px.scatter(
        df,
        x="Similarity",
        y="Relevance Score",
        size="Max Similarity",
        color="Similarity",
        hover_data=["Topic Snippet", "File"],
        title="Relevance vs Similarity (Bubble Size = Max Similarity)",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(height=500)
    return fig