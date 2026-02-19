# Music Database APIs Integration

## Overview

Instead of manually uploading songs, query existing music fingerprint databases that already have millions of songs indexed.

## Available Services

### 1. AcoustID (MusicBrainz) ⭐ FREE & OPEN SOURCE

**Best for:** Free, unlimited queries, huge database

**Setup:**
```bash
# 1. Get free API key: https://acoustid.org/api-key
# 2. Install:
pip install pyacoustid

# 3. Set env var:
export ACOUSTID_API_KEY=your-key-here
```

**Database Size:** Millions of songs
**Cost:** Free
**Rate Limits:** None (be reasonable)

### 2. ACRCloud ⭐ COMMERCIAL BUT FREE TIER

**Best for:** High accuracy, commercial use

**Setup:**
```bash
# 1. Sign up: https://www.acrcloud.com
# 2. Get access key & secret from dashboard
# 3. Set env vars:
export ACRCLOUD_ACCESS_KEY=your-key
export ACRCLOUD_ACCESS_SECRET=your-secret
```

**Database Size:** Millions of songs
**Cost:** Free tier: 1000 requests/month
**Rate Limits:** 1000/month on free tier

### 3. Audd.io ⭐ SIMPLE API

**Best for:** Easy integration, Spotify links included

**Setup:**
```bash
# 1. Sign up: https://audd.io/
# 2. Get API token from dashboard
# 3. Set env var:
export AUDDIO_API_TOKEN=your-token
```

**Database Size:** Large commercial database
**Cost:** Free tier: 100 requests/month
**Rate Limits:** 100/month on free tier

## How It Works

The system queries all available services and aggregates results:

1. **User uploads beat** → System generates fingerprint
2. **Queries databases** → AcoustID, ACRCloud, Audd.io
3. **Searches local DB** → Your uploaded fingerprints
4. **Combines results** → Returns best matches with confidence scores

## API Endpoints

### Analyze Beat (Uses All Databases)
```bash
POST /api/analyze
Content-Type: multipart/form-data

Form fields:
- file: (audio file)
```

**Returns:** Matches from both external databases and local fingerprint DB

## Configuration

Set environment variables in `.env`:

```bash
# AcoustID (free, recommended)
ACOUSTID_API_KEY=your-key

# ACRCloud (optional, free tier)
ACRCLOUD_ACCESS_KEY=your-key
ACRCLOUD_ACCESS_SECRET=your-secret

# Audd.io (optional, free tier)
AUDDIO_API_TOKEN=your-token
```

## Recommended Setup

**For MVP:**
1. Get AcoustID API key (free, unlimited)
2. That's it! You now have access to millions of songs

**For Production:**
1. AcoustID (primary, free)
2. ACRCloud (backup, higher accuracy)
3. Local fingerprint DB (your custom beats)

## Advantages

✅ **No manual uploads** - Millions of songs already indexed
✅ **Real artist data** - Actual song titles and artists
✅ **Free options** - AcoustID is completely free
✅ **Combined search** - Queries multiple databases
✅ **Fallback to local** - Still uses your uploaded beats

## Example Response

```json
{
  "matches": [
    {
      "artist": "Drake",
      "confidence": 0.95,
      "trending": {
        "velocity": 150.5,
        "total_views": 5000,
        "trend_direction": "up"
      }
    }
  ],
  "processing_time_ms": 1250
}
```

## Next Steps

1. **Get AcoustID key** (5 minutes, free)
2. **Set env var** in `.env`
3. **Test**: Upload a beat and see it match against millions of songs!

No more manual uploads needed! 🎉
