# Technical Implementation Guide - Advanced Analytics

## Summary of Changes

### 1. Enhanced Scoring Module (`scoring.py`)

#### New Functions

**`calculate_topic_importance(exam_questions, collection, model, similarity_threshold=0.0)`**
- Returns actual **cosine similarity scores** (0-1) instead of just counts
- Filters results based on `similarity_threshold` parameter
- Extracts year from filename automatically
- Returns dataframe with columns: `Topic Snippet`, `Relevance Score`, `Similarity`, `Max Similarity`, `File`, `Page`, `Year`

**`extract_year_from_filename(filename)`**
- RegEx pattern: `r'(19|20)\\d{2}'`
- Finds year in format like "exam_2023.pdf" → 2023
- Used for year-over-year tracking

**`calculate_gap_analysis(exam_results, all_lecture_chunks, model)`**
- Identifies low-coverage topics (bottom 5 percentile)
- Adds `Coverage_Pct` column
- Sorted ascending by coverage (worst first)
- Returns DataFrame with topics you can safely skip

**`calculate_year_over_year_trends(results_df)`**
- Creates pivot table: rows=topics, columns=years, values=avg similarity
- Extracts first word of topic as main topic name
- Returns data ready for heatmap visualization

#### Modified Functions

**`generate_score_dataframe(topic_scores)`**
- Now processes `scores` list instead of single score
- Calculates mean and max similarity
- Includes year tracking using metadata

#### Key Changes to Data Flow
```
Old: question → query → count matches → [count, count, count]
New: question → query(include distances) → convert distances to similarity → 
     filter by threshold → aggregate → [similarity1, similarity2, ...]
```

---

### 2. Enhanced Database Module (`database.py`)

#### Modified Function

**`query_database(query_text, collection, model, n_results=3)`**
- Added `include=['embeddings', 'metadatas', 'documents', 'distances']` parameter
- **Distances** are now returned (0-2 range for cosine, lower = more similar)
- Distance to Similarity conversion: `similarity = 1 - distance`

#### Why This Change
ChromaDB returns distances by default (which are distances, not similarities). We now explicitly include them so `scoring.py` can convert to similarity scores.

---

### 3. Enhanced Visualization Module (`visualization.py`)

#### Existing Functions (Enhanced)

**`create_bar_chart(df)`**
- Changed from `y="Relevance Score"` to `y="Similarity"`
- Added color scale: `color_continuous_scale="Viridis"`
- Better visual representation of confidence

**`create_pie_chart(df)`**
- Unchanged, but now fed better data from scoring

#### New Functions

**`create_gap_analysis_chart(gap_df)`**
- Horizontal bar chart (`px.barh`)
- Shows top 15 low-coverage topics
- Red color scheme: `color_continuous_scale="Reds_r"`
- X-axis: `Coverage_Pct` (how little tested)

**`create_year_over_year_heatmap(year_trends_df)`**
- `plotly.graph_objects.Heatmap`
- X-axis: Years (columns)
- Y-axis: Topics (rows/index)
- Z-axis: Average similarity scores
- Color scale: `'YlOrRd'` (Yellow→Orange→Red = low→high)

**`create_similarity_distribution_chart(df)`**
- Histogram of similarity scores
- 20 bins for distribution shape
- Helps understand data spread

**`create_confidence_scatter(df)`**
- Scatter plot: X=`Similarity`, Y=`Relevance Score`
- Bubble size: `Max Similarity`
- Color gradient: Also `Similarity`
- Hover shows topic snippet + file

---

### 4. Enhanced App Module (`app.py`)

#### New UI Components

**Sidebar Threshold Slider**
```python
confidence_threshold = st.slider(
    "Confidence Threshold (Similarity Score)",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.05
)
```
- Default: 0.3 (moderate filtering)
- Updated in real-time as user adjusts

#### Tab Structure (4 tabs)

1. **📈 Overview**: Bar + Pie charts + Metrics
2. **⏭️ Gap Analysis**: Skip list visualization
3. **📊 Trends & Distribution**: Histograms + Heatmap
4. **📋 Detailed Results**: Interactive dataframe + export

#### Calculate Call
```python
results_df = calculate_topic_importance(
    exam_questions, 
    collection, 
    model,
    similarity_threshold=confidence_threshold  # NEW
)
```

#### Gap Analysis Call
```python
gap_df = calculate_gap_analysis(results_df, None, model)
```

#### Year-over-Year Call
```python
year_trends = calculate_year_over_year_trends(results_df)
# Check if multiple years exist
if not year_trends.empty and len(year_trends.columns) > 1:
    # Show heatmap
```

---

### 5. Updated Dependencies (`requirements.txt`)

Added:
```
numpy==1.24.3  # For np.mean() and statistical operations
```

---

## Data Flow Architecture

```
PDF Upload
   ↓
extract_pages_from_pdf()
   ↓
process_lecture() → chunk_page_text()
   ↓
store_lecture() → ChromaDB (with distances)
   ↓
extract_exam_questions()
   ↓
calculate_topic_importance(similarity_threshold=0.3)
   │
   ├─→ query_database() → get distances
   │
   ├─→ Convert distances to similarity scores (1 - distance)
   │
   ├─→ Filter by threshold
   │
   └─→ Aggregate scores → generate_score_dataframe()
   ↓
results_df (with Similarity, Max Similarity, Year columns)
   ↓
   ├─→ visualize in Overview tab
   │
   ├─→ calculate_gap_analysis() → Gap Analysis tab
   │
   └─→ calculate_year_over_year_trends() → Heatmap tab
```

---

## Similarity Score Semantics

### Cosine Similarity (0-1 scale)
- **1.0**: Identical documents/topics
- **0.8-0.99**: Highly related
- **0.5-0.79**: Moderately related
- **0.3-0.49**: Somewhat related
- **0-0.29**: Weakly related / Noise

### Typical Behavior
For academic exam matching:
- **Score > 0.7**: Very high confidence match
- **Score 0.4-0.7**: Reasonable match (recommended threshold ~0.5)
- **Score < 0.3**: Noisy/weak connection (filter out with threshold)

---

## Configuration Tuning

### To adjust default threshold
```python
# app.py line ~37
value=0.5,  # Default to stricter matching
```

### To add more visualization options
```python
# visualization.py
def create_custom_chart(df):
    # Add your custom chart here
    pass

# app.py
with st.plotly_chart(create_custom_chart(results_df), ...):
    ...
```

### To support additional file formats
```python
# In app.py, update file_uploader
lecture_files = st.file_uploader(
    "Upload Lecture Notes", 
    type=["pdf", "docx", "txt"],  # Add more types
    accept_multiple_files=True
)
```

---

## Testing the Features

### Test 1: Threshold Filtering
1. Run at threshold 0.0
2. Count results: N
3. Run at threshold 0.8
4. Count results: Should be much smaller
5. Verify: Lower threshold always ≥ higher threshold

### Test 2: Gap Analysis
1. Run analysis
2. Check gap_df is not empty
3. Verify all Coverage_Pct < 5%
4. Check that gap topics are sorted ascending

### Test 3: Year-over-Year
1. Upload: exam_2021.pdf, exam_2022.pdf, exam_2023.pdf
2. Check year column is populated
3. Verify pivot table has 3 year columns
4. Run heatmap—should show color gradient

---

## Performance Considerations

### Bottlenecks
1. **PDF extraction**: O(pages) - largest bottleneck for large PDFs
2. **Embedding**: O(chunks) - semantic search overhead (main time)
3. **ChromaDB query**: O(n_results) - typically fast

### Optimization Tips
- Chunk size in `processing.py` is 150 words (tunable)
- Query limit in `scoring.py` is `n_results=5` (tunable)
- Consider caching embeddings for repeated analysis

### Typical Benchmarks
- 50 pages lecture + 10 page exam: ~30-45 seconds
- 200 pages lecture + 20 page exam: ~90-120 seconds
- 3 year exams (10 pages each): +20% overhead

---

## Error Handling

### Common Issues

**Issue**: "Topics Found: 0"
- **Cause**: Threshold too high or no matches
- **Fix**: Lower threshold to 0.1-0.2

**Issue**: Heatmap not showing
- **Cause**: Only 1 year in filenames or no year detected
- **Fix**: Use format "exam_2023.pdf" or rerun with multi-year exams

**Issue**: Similarity values all identical
- **Cause**: Query results don't include distances properly
- **Fix**: Verify `database.py` has `include=['distances']`

---

## Future Enhancement Ideas

1. **Confidence intervals**: Show ±std dev on scores
2. **Topic clustering**: Group related topics
3. **Predictive modeling**: Forecast 2024 exam topics based on trends
4. **Custom themes**: Dark mode, colorblind-friendly palettes
5. **Export formats**: PDF reports, PowerPoint decks
6. **Real-time updates**: Watch folder for new exams
7. **ML-based recommendations**: "You should study X and skip Y"

---

## Code Quality Notes

- Uses f-strings for formatting
- Type hints not used (can be added for better IDE support)
- Error handling is basic (could be enhanced)
- No unit tests (should be added for reliability)
- Comments are descriptive but could be more detailed
