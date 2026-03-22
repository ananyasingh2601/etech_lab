# Quick Start: New Advanced Features

## What's New? (Visual Tour)

### Before vs After

#### BEFORE
- Single page layout
- Simple bar + pie charts
- Basic dataframe

#### AFTER
- 4-tab interface with advanced analytics
- Confidence slider for filtering
- 5 different chart types
- Gap analysis (skip list)
- Year-over-year trends
- Interactive sorting & export

---

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

### 3. Open Browser
```
http://localhost:8501
```

---

## First Time Using the App

### Step 1: Upload Files
1. Click **"📁 Upload Documents"** section
2. Upload 1+ lecture PDFs
3. Upload 1 exam PDF
4. *Optional: Upload exams from multiple years* (exam_2021.pdf, exam_2022.pdf, etc.)

### Step 2: Adjust Threshold (Optional)
1. See **"⚙️ Analysis Settings"** section
2. Move slider to desired confidence level:
   - 👶 **0.1-0.3**: Broad search (find everything)
   - 👤 **0.3-0.5**: Balanced (most common)
   - 🧠 **0.5-0.7**: Focused (high-confidence only)
   - 🎯 **0.7-1.0**: Strict (only the best matches)

### Step 3: Click Analyze
1. Click **"🔍 Analyze & Map Topics"** button
2. Wait 30-120 seconds for processing
3. Results appear in 4 tabs

---

## Understanding Each Tab

### Tab 1: 📈 Overview
**What You See:**
- Left: Bar chart of top 10 topics (by similarity)
- Middle: Pie chart showing topic distribution
- Right: Key statistics (count, avg score, max score)

**What To Do:**
- Identify top topics to study first
- See if most weight is on few topics or spread

**Example Reading:**
- If 3 topics take up 60% of pie → Focus on those 3
- If evenly distributed → Study all equally

---

### Tab 2: ⏭️ Gap Analysis (Skip List)
**What You See:**
- Red horizontal bar chart showing low-coverage topics
- Text list of topics below 5% coverage

**What To Do:**
- ❌ Don't study these topics (exam doesn't test them)
- ✅ Focus on the other 80% instead
- 🤔 Ask instructor if surprising gaps exist

**Example Reading:**
- "Appendix Proofs" at 2% → Can skip
- "Historical Background" at 3% → Can skip
- "Main Concepts" at 85% → MUST study

**Why It Matters:**
- Time savings: Skip 20% of lecture content
- Focus: Study what matters
- Confidence: Know what exam won't ask

---

### Tab 3: 📊 Trends & Distribution
**What You See:**
- Top-left: Histogram of similarity scores (distribution shape)
- Top-right: Scatter plot of relevance vs confidence
- Bottom: Year-over-year heatmap (if 2+ years uploaded)

**What To Do:**
- Histogram: See if matches are clustered or spread
- Scatter: Identify high-value topics (top-right quadrant)
- Heatmap: Spot rising/falling topics

**Example Reading:**
- **Histogram**: Peak at 0.6 → Most matches are moderately confident
- **Scatter**: Bubble in top-right → High relevance + high confidence (study!)
- **Heatmap**: 
  - Red→Pale = Falling topic (skip)
  - Pale→Red = Rising topic (prioritize)
  - Always red = Fundamental (always study)

**Pro Tip:**
Import multiple years to unlock heatmap predictions!

---

### Tab 4: 📋 Detailed Results
**What You See:**
- Interactive table with ALL results
- Sort buttons at top
- Export button (download CSV)

**What To Do:**
1. Click column headers to sort
2. Find specific topics you're curious about
3. Export and share with study group
4. Use in Excel/Google Sheets for more analysis

**Columns Explained:**
| Column | Meaning |
|--------|---------|
| Topic Snippet | First 80 chars of matched topic |
| Similarity | Avg match confidence (0-1) |
| Relevance Score | How many times it matched exam |
| Max Similarity | Best individual match (0-1) |
| File | Which lecture it came from |
| Page | What page in that lecture |
| Year | Which year (if extracted) |

---

## Real-World Scenarios

### Scenario 1: Quick 5-Minute Study Plan
**Goal**: Get study priorities in minutes

**Steps:**
1. Upload lecture + exam
2. Keep threshold at 0.3
3. Go to **Tab 1: Overview**
4. Identify top 5 topics in pie chart
5. Go to **Tab 2: Gap Analysis**
6. Confirm those topics aren't in "skip list"
7. **Decision**: Study top 5, skip bottom 50%

**Result**: 50% time savings!

---

### Scenario 2: Deep Trend Analysis (15 min)
**Goal**: Understand topic evolution

**Steps:**
1. Upload lecture + 3 years of exams
2. Lower threshold to 0.25 (see more data)
3. Go to **Tab 3: Trends**
4. Scroll to **"Year-over-Year Heatmap"**
5. Look for **color changes**:
   - Red→Pale = Falling (deprioritize)
   - Pale→Red = Rising (prioritize)
   - Always red = Stable (always study)
6. Create study plan based on trends

**Example Finding:**
```
2021: "Neural Networks" = 🔴 (heavily tested)
2022: "Neural Networks" = 🟡 (moderately tested)
2023: "Neural Networks" = ⚪ (rarely tested)
→ Decision: Don't spend much time on this
```

---

### Scenario 3: Group Study Organization (20 min)
**Goal**: Coordinate group study effectively

**Steps:**
1. Run full analysis (multiple lectures + exams)
2. Use threshold 0.5 (focus on high-confidence)
3. Go to **Tab 4: Detailed Results**
4. Click **"📥 Export Results as CSV"**
5. Share CSV with study group (via email/Drive)
6. Group divides topics:
   - Person A: Studies topics 1-5
   - Person B: Studies topics 6-10
   - etc.
7. Each person becomes expert on assigned topics
8. Group meets to teach each other

**Result:**
- Better coverage (everyone shares knowledge)
- Time savings (each person studies <50%)
- Higher retention (teaching others helps learning)

---

## Pro Tips & Tricks

### Trick 1: Recalibrate Threshold
Don't just use default 0.3! Try different values:
```
Run 1 at 0.1: See everything (might be noisy)
Run 2 at 0.5: See high-confidence stuff
Run 3 at 0.7: See only the best matches
→ Find your sweet spot!
```

### Trick 2: Compare Multiple Years
Filename format: Auto-detects years from file names
```
✅ exam_2021.pdf → detects 2021
✅ 2021_midterm.pdf → detects 2021
✅ exam2022.pdf → detects 2022
❌ final_exam.pdf → no year detected
```

### Trick 3: Combine Gap & Overview
1. Look at top topics in Overview (red bar chart)
2. Check if ANY of those appear in Gap Analysis (skip list)
3. If top topic is in skip list = likely data issue
4. Ask instructor why exam doesn't test main topics

### Trick 4: Export + Spreadsheet Analysis
1. Export to CSV
2. Open in Excel/Google Sheets
3. Sort however you want
4. Add your own columns (e.g., "Study Status: Done/Pending/Review")
5. Track your progress

### Trick 5: Share Insights
1. Export CSV
2. Share with professor/TA
3. Point out gaps: "Why isn't [topic] on the exam?"
4. Help improve course if disconnect exists

---

## Interpreting Edge Cases

### If "Topics Found: 0"
**Problem**: No matches found
**Causes**:
- Threshold too high (set to 0.9+)
- Lecture & exam on completely different topics
- Files are corrupted

**Solution**:
- Lower threshold to 0.2
- Check file content
- Verify PDF extract succeeded

### If All Similarities = 0.5
**Problem**: All scores identical (unusual)
**Cause**: Default fallback when distances unavailable
**Solution**:
- Check ChromaDB setup
- Restart webapp
- Try different PDFs

### If No Year Detected
**Problem**: Heatmap doesn't appear
**Cause**: Filenames don't match pattern `YYYY`
**Solution**:
- Rename to: `exam_2021.pdf`, `exam_2022.pdf`
- Or: `2021_final.pdf`, `2022_final.pdf`

### If Gap Analysis Empty
**Problem**: "All topics have good coverage" message
**Cause**: All topics tested (or threshold too high)
**Solution**:
- Either: Great! No topics to skip
- Or: Lower threshold to find weaker matches

---

## Keyboard Shortcuts

| Action | How |
|--------|-----|
| Collapse sidebar | Click arrow left of sidebar |
| Clear uploaded files | Click "x" next to filename in uploader |
| Rerun analysis | Change threshold or click button again |
| Change tabs | Click tab names |
| Sort dataframe | Click column header |
| Download CSV | In Tab 4, click CSV button |

---

## Troubleshooting

### App Won't Start
```bash
# Make sure you're in the right directory
cd c:\Users\HP\Downloads\etech_lab

# Install dependencies
pip install -r requirements.txt

# Start app
streamlit run app.py
```

### Got Error About "numpy"
```bash
pip install numpy==1.24.3
```

### Browser Says "Connection Refused"
Make sure Streamlit is running in terminal (should say "Streamlit is running...").

### Analysis Takes Too Long
- It's normal: First run trains embeddings (30-60s)
- Subsequent runs will be similar duration
- Larger files = longer processing

---

## Next Steps

1. **Try the app** with your actual course materials
2. **Export results** and organize your study plan
3. **Share with classmates** for collaborative studying
4. **Track progress** using the CSV export
5. **Provide feedback** on what's working

Good luck! 🎓
