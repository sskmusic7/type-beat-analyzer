# System Flow & Architecture

## 🏗️ Architecture Overview

**NOT Google App Scripts** - This is a modern web application:

- **Frontend**: Next.js (React) running on `localhost:3000`
- **Backend**: FastAPI (Python) running on `localhost:8000`
- **Communication**: REST API (HTTP requests)

## 📱 What You Have

### ✅ Full Web Interface
- **URL**: `http://localhost:3000`
- **Features**:
  - Drag & drop audio upload
  - Real-time analysis results
  - Trending artists sidebar
  - Beautiful UI with TailwindCSS

### ✅ Backend API
- **URL**: `http://localhost:8000`
- **Endpoints**:
  - `POST /api/analyze` - Analyze uploaded beat
  - `GET /api/trending` - Get trending artists
  - `GET /api/processing/{job_id}` - Check processing status

## 🔄 Complete Flow: What Happens When You Upload a Beat

```
┌─────────────────────────────────────────────────────────────┐
│ 1. FRONTEND (Next.js - localhost:3000)                       │
│    - User drags/drops audio file                            │
│    - AudioUploader component captures file                  │
│    - Creates FormData with audio file                       │
└──────────────────────┬──────────────────────────────────────┘
                      │
                      │ POST /api/analyze
                      │ multipart/form-data
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. BACKEND (FastAPI - localhost:8000)                       │
│    /api/analyze endpoint receives file                      │
│                                                              │
│    Step 1: Save file to /tmp/typebeat_*.wav                │
│    Step 2: Create processing job (tracking)                │
└──────────────────────┬──────────────────────────────────────┘
                      │
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌──────────────────┐      ┌──────────────────────┐
│ 3A. MUSIC DBs    │      │ 3B. LOCAL FINGERPRINT│
│                  │      │                      │
│ Query all APIs:  │      │ Search FAISS index:  │
│                  │      │                      │
│ • AcoustID ──────┼──────┼─> Generate fingerprint│
│   (MusicBrainz)  │      │   from audio         │
│                  │      │                      │
│ • ACRCloud ──────┼──────┼─> Compare with       │
│   (Commercial)   │      │   stored fingerprints│
│                  │      │                      │
│ • AudD.io ───────┼──────┼─> Return top matches │
│   (Simple API)   │      │   with similarity    │
└────────┬─────────┘      └──────────┬───────────┘
         │                           │
         └─────────────┬─────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. COMBINE RESULTS                                           │
│    - Merge database matches + local matches                  │
│    - Deduplicate by artist                                   │
│    - Sort by confidence score                                │
└──────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. FETCH TRENDING DATA                                       │
│    For each matched artist:                                 │
│    - Query YouTube Data API v3                              │
│    - Search "[Artist] type beat"                           │
│    - Calculate velocity (views/day)                          │
│    - Determine trend direction (up/down/stable)             │
└──────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. RETURN RESULTS                                            │
│    JSON Response:                                            │
│    {                                                         │
│      "matches": [                                            │
│        {                                                      │
│          "artist": "Drake",                                  │
│          "confidence": 0.85,                                 │
│          "trending": {                                        │
│            "velocity": 1250,                                 │
│            "direction": "up",                                │
│            "total_views": 50000                              │
│          }                                                   │
│        }                                                      │
│      ],                                                      │
│      "processing_time_ms": 2345.67                          │
│    }                                                         │
└──────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. FRONTEND DISPLAYS                                         │
│    - ResultsDisplay component shows matches                  │
│    - TrendingArtists sidebar updates                         │
│    - User sees: "85% Drake type beat (🔥 Trending #2)"     │
└─────────────────────────────────────────────────────────────┘
```

## 🔌 API Integration Details

### Music Database APIs (Step 3A)

**AcoustID** (Free, Unlimited)
- Endpoint: `https://api.acoustid.org/v2/lookup`
- Method: POST with fingerprint
- Returns: Artist, title, MusicBrainz IDs

**ACRCloud** (1000/month free)
- Endpoint: `https://identify-eu-west-1.acrcloud.com/v1/identify`
- Method: POST with audio file + HMAC signature
- Returns: Artist, title, album, score

**AudD.io** (100/month free)
- Endpoint: `https://api.audd.io/`
- Method: POST with audio file
- Returns: Artist, title, Spotify links

### Local Fingerprint Database (Step 3B)

**FAISS Index**
- Location: `backend/data/fingerprints.faiss`
- Method: Neural Audio Fingerprint (ICASSP 2021)
- Returns: Similar beats from your uploaded database

## 🧪 How to Test

### 1. Start Backend
```bash
cd backend
/opt/miniconda3/envs/typebeat/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Open Browser
- Go to: `http://localhost:3000`
- You'll see the upload interface

### 4. Upload a Beat
- Drag & drop an audio file (MP3, WAV, etc.)
- Watch the processing happen
- See results with artist matches and trending data

## 📊 Processing Stages

When you upload, you can track progress via `/api/processing/{job_id}`:

1. **Uploading file** (10%)
2. **Saving file** (20%)
3. **Querying music databases** (40%)
   - AcoustID
   - ACRCloud
   - AudD.io
4. **Searching local database** (60%)
5. **Fetching trending data** (80%)
6. **Complete** (100%)

## 🎯 Key Points

- **No Google App Scripts** - Pure Next.js + FastAPI
- **All APIs configured** - AcoustID, ACRCloud, AudD.io
- **Full UI** - Drag & drop, results display, trending sidebar
- **Real-time tracking** - Processing monitor shows progress
- **No fake predictions** - Only returns actual matches
