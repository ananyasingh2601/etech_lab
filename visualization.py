import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Custom color schemes
COLOR_MAIN = "#0D47A1"
COLOR_ACCENT = "#FF6F00"
COLOR_SUCCESS = "#4CAF50"
COLOR_WARNING = "#FFC107"

def create_bar_chart(df):
    """Top topics bar chart with enhanced styling."""
    if df.empty: return None
    fig = px.bar(
        df.head(10), 
        x="Topic Snippet", 
        y="Similarity",
        title="<b>📈 Top 10 Most Exam-Relevant Topics</b>",
        color="Similarity",
        color_continuous_scale="Viridis",
        hover_data={"Similarity": ":.3f", "Relevance Score": True}
    )
    fig.update_layout(
        xaxis_tickangle=-45, 
        height=550,
        template="plotly_white",
        font=dict(size=11),
        xaxis_title="Topic",
        yaxis_title="Average Similarity Score",
        coloraxis_colorbar=dict(title="Similarity"),
        hovermode="closest"
    )
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Similarity: %{customdata[0]:.3f}<br>Matches: %{customdata[1]}<extra></extra>")
    return fig

def create_pie_chart(df):
    """Topic distribution pie chart with better formatting."""
    if df.empty: return None
    fig = px.pie(
        df.head(10), 
        names="Topic Snippet", 
        values="Relevance Score", 
        title="<b>🥧 Topic Distribution (Top 10)</b>",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Exam Relevance: %{value}<extra></extra>",
        textinfo="label+percent"
    )
    fig.update_layout(
        height=500,
        template="plotly_white",
        font=dict(size=11)
    )
    return fig

def create_gap_analysis_chart(gap_df):
    """Horizontal bar chart showing topics with low exam coverage."""
    if gap_df.empty:
        return None
    
    fig = px.barh(
        gap_df.head(15),
        y="Topic Snippet",
        x="Coverage_Pct",
        title="<b>🚫 Gap Analysis: Low-Coverage Topics (Study Less)</b>",
        color="Coverage_Pct",
        color_continuous_scale="Reds_r",
        labels={"Coverage_Pct": "Coverage %", "Topic Snippet": "Topic"}
    )
    fig.update_layout(
        height=550, 
        yaxis_tickfont=dict(size=10),
        template="plotly_white",
        xaxis_title="Coverage Percentage (%)",
        yaxis_title="Topic",
        hovermode="closest"
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Coverage: %{x:.1f}%<extra></extra>"
    )
    return fig

def create_year_over_year_heatmap(year_trends_df):
    """Heatmap showing how topic focus shifts across exam years."""
    if year_trends_df.empty:
        return None
    
    heatmap_data = year_trends_df.fillna(0).astype(float)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='YlOrRd',
        colorbar=dict(title="Avg Similarity"),
        hovertemplate="<b>%{y}</b><br>Year: %{x}<br>Similarity: %{z:.3f}<extra></extra>"
    ))
    
    fig.update_layout(
        title="<b>📅 Year-over-Year Topic Trends</b>",
        xaxis_title="Exam Year",
        yaxis_title="Topic",
        height=600,
        template="plotly_white",
        font=dict(size=11)
    )
    return fig

def create_similarity_distribution_chart(df):
    """Histogram showing similarity score distribution with statistics."""
    if df.empty or "Similarity" not in df.columns:
        return None
    
    mean_sim = df["Similarity"].mean()
    median_sim = df["Similarity"].median()
    
    fig = px.histogram(
        df,
        x="Similarity",
        nbins=25,
        title="<b>📊 Similarity Score Distribution</b>",
        labels={"Similarity": "Similarity Score", "count": "Number of Topics"},
        color_discrete_sequence=[COLOR_MAIN],
        marginal="box"
    )
    
    # Add mean and median lines
    fig.add_vline(x=mean_sim, line_dash="dash", line_color="red", 
                  annotation_text=f"Mean: {mean_sim:.3f}", annotation_position="top right")
    fig.add_vline(x=median_sim, line_dash="dot", line_color="green", 
                  annotation_text=f"Median: {median_sim:.3f}", annotation_position="top left")
    
    fig.update_layout(
        height=450, 
        template="plotly_white",
        showlegend=False,
        hovermode="x unified"
    )
    return fig

def create_confidence_scatter(df):
    """Bubble chart: Relevance vs Similarity with detailed hover info."""
    if df.empty:
        return None
    
    fig = px.scatter(
        df,
        x="Similarity",
        y="Relevance Score",
        size="Max Similarity",
        color="Similarity",
        hover_data={"Topic Snippet": True, "File": True, "Similarity": ":.3f", "Relevance Score": True},
        title="<b>🎯 Relevance vs Similarity Analysis</b>",
        color_continuous_scale="Viridis",
        size_max=50
    )
    
    fig.update_layout(
        height=500,
        template="plotly_white",
        xaxis_title="Average Similarity Score",
        yaxis_title="Exam Relevance (Match Count)",
        hovermode="closest"
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>" +
                      "Source: %{customdata[1]}<br>" +
                      "Similarity: %{customdata[2]:.3f}<br>" +
                      "Relevance: %{customdata[3]}<extra></extra>"
    )
    return fig

def create_topic_ranking_sunburst(df):
    """Sunburst chart showing topic hierarchy and rankings."""
    if df.empty or len(df) < 5:
        return None
    
    top_topics = df.head(15).copy()
    top_topics["Rank"] = range(1, len(top_topics) + 1)
    top_topics["Priority"] = pd.cut(top_topics["Similarity"], 
                                     bins=3, 
                                     labels=["High Priority", "Medium Priority", "Low Priority"])
    
    fig = px.sunburst(
        top_topics,
        labels="Topic Snippet",
        parents=["All Topics"] * len(top_topics),
        values="Relevance Score",
        color="Similarity",
        color_continuous_scale="RdYlGn",
        title="<b>🌟 Topic Priority Sunburst</b>"
    )
    
    fig.update_layout(height=600, font=dict(size=10))
    return fig

def create_file_contribution_bar(df):
    """Bar chart showing which lecture files contribute most to exam topics."""
    if df.empty or "File" not in df.columns:
        return None
    
    file_contrib = df.groupby("File").agg({
        "Similarity": "mean",
        "Relevance Score": "sum"
    }).reset_index().sort_values("Relevance Score", ascending=True)
    
    fig = px.barh(
        file_contrib,
        x="Relevance Score",
        y="File",
        title="<b>📚 Lecture File Contribution to Exam</b>",
        color="Similarity",
        color_continuous_scale="Turbo",
        hover_data={"Similarity": ":.3f"}
    )
    
    fig.update_layout(
        height=max(400, 50 + len(file_contrib) * 30),
        template="plotly_white",
        xaxis_title="Total Exam Relevance Score",
        yaxis_title="Lecture File"
    )
    return fig

def create_topic_card(topic_snippet, similarity, relevance, max_similarity):
    """HTML card for individual topic display."""
    percentage = min(100, int(similarity * 100))
    return f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; color: white; margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="font-weight: bold; font-size: 14px; margin-bottom: 10px;">{topic_snippet}</div>
        <div style="display: flex; justify-content: space-between; font-size: 12px;">
            <div>Similarity: <b>{similarity:.3f}</b></div>
            <div>Relevance: <b>{int(relevance)}</b></div>
            <div>Confidence: <b>{percentage}%</b></div>
        </div>
        <div style="background: rgba(255,255,255,0.3); height: 6px; border-radius: 3px; margin-top: 8px;">
            <div style="background: #4CAF50; height: 100%; border-radius: 3px; width: {percentage}%;"></div>
        </div>
    </div>
    """