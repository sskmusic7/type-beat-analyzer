# Trending Type Beat Artist Discovery

## 🎯 Purpose

Automatically discover the **top 50-100 trending artists** that people are searching for type beats, similar to how BeatStars tracks trending artists.

## 🔍 How It Works

### Method 1: YouTube Search Analysis
1. **Searches YouTube** for multiple "type beat" queries:
   - "type beat"
   - "type beat 2024"
   - "type beat 2025"
   - "free type beat"
   - "trap type beat"
   - "rap type beat"
   - etc.

2. **Extracts artist names** from video titles:
   - "Drake Type Beat" → "Drake"
   - "Travis Scott - Type Beat" → "Travis Scott"
   - "Type Beat | Artist Name" → "Artist Name"

3. **Ranks by popularity**:
   - Count: How many type beat videos found
   - Views: Total views across all videos
   - Average: Views per video

4. **Returns top artists** sorted by trending status

### Method 2: YouTube Data API (Optional)
- Uses YouTube Data API v3 for faster, more accurate results
- Requires `YOUTUBE_API_KEY` in `.env`
- Falls back to yt-dlp if API not available

## 🚀 Usage

### Option 1: Dashboard (Recommended)
1. Open Streamlit dashboard: `http://localhost:8501`
2. Go to **"🔍 Discover Trending Artists"** tab
3. Set number of artists to discover (default: 100)
4. Click **"🔍 Discover Trending Artists"**
5. View ranked results and select artists to train on

### Option 2: Command Line
```bash
cd ml
python discover_trending_artists.py --max-artists 100 --top-n 50 --save
```

### Option 3: Quick Script
```bash
./scripts/discover_trending_artists.sh
```

## 📊 Output

### Console Output
```
🎵 Top 50 Trending Type Beat Artists:

Rank   Artist                          Type Beats       Total Views      Avg Views
----------------------------------------------------------------------------------
1      Drake                           245              1,234,567,890    5,038,236
2      Travis Scott                    198              987,654,321      4,987,142
3      Metro Boomin                    187              876,543,210      4,687,395
...
```

### JSON File (`data/trending_artists.json`)
```json
{
  "discovered_at": 1707744000,
  "total_artists": 100,
  "artists": [
    {
      "name": "Drake",
      "type_beat_count": 245,
      "total_views": 1234567890,
      "avg_views": 5038236,
      "sample_videos": [...]
    },
    ...
  ]
}
```

## 🎯 Features

### Smart Artist Extraction
- Handles multiple title formats
- Filters out non-artist words
- Proper capitalization
- Removes duplicates

### Ranking Algorithm
1. **Count**: Number of type beat videos found
2. **Total Views**: Sum of all video views
3. **Average Views**: Views per video
4. **Official Status**: Prioritizes official channels

### Search Queries
- General: "type beat"
- Year-specific: "type beat 2024", "type beat 2025"
- Genre-specific: "trap type beat", "rap type beat"
- Free: "free type beat"
- Instrumental: "type beat instrumental"

## 🔧 Configuration

### Environment Variables
```bash
# Optional: For faster API-based search
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### Parameters
- `--max-artists`: Maximum artists to discover (default: 100)
- `--top-n`: Number to display (default: 50)
- `--save`: Save results to JSON file

## 📈 Use Cases

### 1. Discover Trending Artists
Find who's hot right now in the type beat market

### 2. Training Data Selection
Automatically select top artists for fingerprint training

### 3. Market Research
Understand what artists producers are making beats for

### 4. Competitive Analysis
See which artists have the most type beat content

## 🎵 Integration with Training

After discovering trending artists:

1. **View Results** in dashboard
2. **Select Artists** from the list
3. **Click "Train on Selected Artists"**
4. System automatically trains on top-performing official songs

## 🔍 Example Workflow

```bash
# 1. Discover trending artists
python ml/discover_trending_artists.py --max-artists 100 --save

# 2. Review results
cat data/trending_artists.json

# 3. Train on top artists
python ml/hybrid_trainer.py --artists "Drake" "Travis Scott" "Metro Boomin"
```

## 📊 Accuracy

The system:
- ✅ Analyzes real YouTube search data
- ✅ Ranks by actual popularity metrics
- ✅ Updates with current trends
- ✅ Similar to BeatStars trending logic

## 🚀 Next Steps

1. **Run discovery** to find trending artists
2. **Review results** in dashboard or JSON
3. **Select top artists** for training
4. **Train fingerprints** on official songs
5. **Repeat periodically** to stay current

---

**Status**: ✅ Ready to use! Discover trending artists automatically.
