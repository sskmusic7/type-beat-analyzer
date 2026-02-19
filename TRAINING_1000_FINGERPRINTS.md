# Training 1000 Fingerprints - Top 100 Artists

## 🎯 Goal
Generate **1,000+ accurate fingerprints** from **top 100 trending artists** using:
- ✅ Top-performing official songs (high views + comments)
- ✅ Official channels prioritized
- ✅ 10 fingerprints per artist

## 📋 Artist List

Using curated list of **108 real artists** including:
- Drake, Travis Scott, Lil Baby, Metro Boomin, 21 Savage
- Future, Lil Uzi Vert, Playboi Carti, Kendrick Lamar, J. Cole
- Kanye West, The Weeknd, Post Malone, Juice WRLD, Lil Wayne
- And 98 more top artists...

**Source**: `data/top_100_real_artists.json`

## 🚀 Training Process

### What Happens:
1. **For each artist** (108 total):
   - Searches YouTube for "Artist Name official music"
   - Gets video info (views, comments, likes)
   - Sorts by engagement: `views + (comments × 100) + (likes × 10)`
   - Prioritizes official channels (VEVO, Official, artist name)
   - Downloads top 10 videos
   - Generates fingerprints
   - Deletes audio files immediately

2. **Result**:
   - 108 artists × 10 fingerprints = **1,080 fingerprints**
   - All from top-performing official songs
   - High engagement (views + comments)

### Video Selection Criteria:
- ✅ **Official channels** first (VEVO, Official, artist name)
- ✅ **High views** (millions preferred)
- ✅ **High comments** (shows engagement)
- ✅ **High likes** (quality indicator)
- ❌ Excludes covers, remixes, reactions

## 📊 Progress Monitoring

### Check if Training is Running:
```bash
./scripts/check_training_progress.sh
```

### View Live Log:
```bash
tail -f ml/training_log.txt
```

### Check Results:
```bash
# Count fingerprints
python -c "import json; data=json.load(open('ml/data/training_fingerprints/final_training_data_1000.json')); print(f'Total: {len(data)} fingerprints')"

# List artists
python -c "import json; data=json.load(open('ml/data/training_fingerprints/final_training_data_1000.json')); artists=set(d['artist'] for d in data); print(f'Artists: {len(artists)}'); print(', '.join(sorted(artists)[:20]))"
```

## 📁 Output Files

### Main Output:
- `ml/data/training_fingerprints/final_training_data_1000.json`
  - All 1,080 fingerprints
  - Metadata: artist, track, source, timestamp

### Checkpoints:
- `ml/data/training_fingerprints/training_batch_10.json` (after 10 artists)
- `ml/data/training_fingerprints/training_batch_20.json` (after 20 artists)
- ... (every 10 artists)

## ⏱️ Estimated Time

- **Per artist**: ~2-5 minutes (download + fingerprint)
- **Total (108 artists)**: ~4-9 hours
- **Depends on**: Network speed, YouTube availability

## ✅ Verification

### Data Quality Checks:
1. **No duplicates**: Each fingerprint is unique
2. **High engagement**: Videos have millions of views
3. **Official sources**: VEVO, Official channels prioritized
4. **Full audio**: Complete songs (not just previews)

### Expected Stats:
- **Total fingerprints**: ~1,080
- **Unique artists**: 108
- **Average views per video**: Millions
- **Official channels**: >80%

## 🔍 What Gets Stored

### ✅ Stored:
- Fingerprint embeddings (128-dim vectors)
- Artist name
- Track name
- Source (youtube_download)
- Timestamp

### ❌ NOT Stored:
- Audio files (deleted immediately)
- Video files
- Copyrighted content

## 🎯 Result

**1,080 high-quality fingerprints** from:
- ✅ Top 100 trending artists
- ✅ Top-performing official songs
- ✅ High engagement (views + comments)
- ✅ Verified data sources

---

**Status**: 🚀 Training in progress...

**Check progress**: `./scripts/check_training_progress.sh`
