# Training Data Storage & Information

## 📦 File Storage Location

**Directory:** `data/training_fingerprints/`

**Files Created:**
- `training_fingerprints_<timestamp>.json` - Incremental saves after each artist
- `final_training_data.json` - Final combined file

## 💾 File Sizes

**Per Fingerprint:**
- ~0.9 KB per fingerprint entry
- Contains: 128-dim vector + metadata (artist, track name, track ID, timestamp)

**Total Storage:**
- 100 fingerprints: ~90 KB
- 1,000 fingerprints: ~0.88 MB  
- 10,000 fingerprints: ~8.78 MB
- 100,000 fingerprints: ~87.8 MB

**Very efficient!** Only storing mathematical fingerprints, not audio files.

## 📊 Preview Availability

### Development Mode Limitations

**API Limits:**
- Max 10 tracks per search request (Development Mode restriction)
- Trainer paginates to get up to 50 tracks per artist
- Only processes tracks WITH preview URLs

### Preview Availability

**Not all tracks have previews:**
- Depends on licensing agreements
- Varies by track, not by artist
- Some artists may have 0% previews, others 50%+

**The trainer automatically:**
- ✅ Searches through many tracks
- ✅ Filters for ones with preview URLs
- ✅ Only processes tracks that have previews
- ✅ Skips tracks without previews

### Checking Preview Availability

To check which artists have previews:

```bash
cd ml
python -c "
from streaming_trainer import StreamingTrainer
import os
from dotenv import load_dotenv

load_dotenv('../backend/.env')
trainer = StreamingTrainer(
    os.getenv('SPOTIFY_CLIENT_ID'),
    os.getenv('SPOTIFY_CLIENT_SECRET')
)

# Check preview availability
for artist in ['Drake', 'Travis Scott', 'Metro Boomin']:
    tracks = trainer.get_artist_tracks(artist, limit=50)
    print(f'{artist}: {len(tracks)} tracks with previews')
"
```

## 🌍 Region Information

**Note:** Spotify API doesn't expose region-specific preview availability in search results.

**What we know:**
- Preview availability is track-specific (licensing dependent)
- Not region-specific in the API response
- Some tracks have previews globally, some don't
- The trainer will find tracks with previews automatically

**To see region info:**
- Would need to check individual track objects
- Not exposed in search API
- Would require additional API calls per track

## 🚀 Running Training

```bash
# Test with 2 artists (small test)
./scripts/run_streaming_trainer.sh "Drake" "Travis Scott"

# Full training with default artists
./scripts/run_streaming_trainer.sh

# Custom artists
./scripts/run_streaming_trainer.sh "Artist1" "Artist2" "Artist3"
```

## 📈 Expected Results

**If artist has previews:**
- Trainer will find and process them
- Generates fingerprints for each
- Saves incrementally

**If artist has no previews:**
- Trainer will search through tracks
- Report "0 tracks with previews"
- Move to next artist

**Output:**
- Fingerprints saved to `data/training_fingerprints/`
- JSON format (easy to load/process)
- Ready for model training

## 🔍 Viewing Results

```bash
# List all training files
ls -lh data/training_fingerprints/

# View a file
cat data/training_fingerprints/final_training_data.json | jq '.[0]'

# Count fingerprints
cat data/training_fingerprints/final_training_data.json | jq 'length'
```

## ⚠️ Development Mode Notes

**Current Restrictions (Feb 2026):**
- Max 10 tracks per search request
- Limited to 5 authorized users
- Smaller set of endpoints available
- But `GET /search` is still available ✅

**Impact:**
- Training will be slower (more API calls needed)
- But still works - just paginates more
- Preview availability is the main factor
