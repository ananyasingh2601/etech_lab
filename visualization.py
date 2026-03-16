import plotly.express as px

def create_bar_chart(df):
    if df.empty: return None
    fig = px.bar(df.head(10), x="Topic Snippet", y="Relevance Score", title="Top 10 Topics", color="Relevance Score")
    fig.update_layout(xaxis_tickangle=-45)
    return fig
def create_pie_chart(df):
    if df.empty: return None
    return px.pie(df.head(10), names="Topic Snippet", values="Relevance Score", title="Topic Distribution", hole=0.4)