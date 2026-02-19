# Music Database API Signup Instructions

## Credentials
- **Email:** sospecial07@hotmail.com
- **Password:** SSKMUSICBABY

---

## 1. AcoustID (MusicBrainz) - FREE ⭐ START HERE

**URL:** https://acoustid.org/api-key

**Steps:**
1. Visit https://acoustid.org/api-key
2. Enter email: `sospecial07@hotmail.com`
3. Click "Request API Key"
4. Check email for confirmation link
5. Click confirmation link
6. Copy your API key
7. Add to `.env`: `ACOUSTID_API_KEY=your-key-here`

**Time:** 2 minutes
**Cost:** Free, unlimited queries

---

## 2. ACRCloud - FREE TIER

**URL:** https://www.acrcloud.com

**Steps:**
1. Visit https://www.acrcloud.com
2. Click "Sign Up" or "Free Trial"
3. Enter email: `sospecial07@hotmail.com`
4. Enter password: `SSKMUSICBABY`
5. Complete signup form
6. Verify email
7. Go to Dashboard → API Keys
8. Copy Access Key and Access Secret
9. Add to `.env`:
   ```
   ACRCLOUD_ACCESS_KEY=your-key
   ACRCLOUD_ACCESS_SECRET=your-secret
   ```

**Time:** 5 minutes
**Cost:** Free tier: 1000 requests/month

---

## 3. Audd.io - FREE TIER

**URL:** https://audd.io/

**Steps:**
1. Visit https://audd.io/
2. Click "Sign Up" or "Get Started"
3. Enter email: `sospecial07@hotmail.com`
4. Enter password: `SSKMUSICBABY`
5. Complete signup
6. Verify email
7. Go to Dashboard → API
8. Copy API Token
9. Add to `.env`: `AUDDIO_API_TOKEN=your-token`

**Time:** 5 minutes
**Cost:** Free tier: 100 requests/month

---

## After Signup

1. **Update `.env` file** with all API keys
2. **Restart backend:**
   ```bash
   pkill -f uvicorn
   cd backend
   /opt/miniconda3/envs/typebeat/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
3. **Test it:**
   ```bash
   curl -X POST http://localhost:8000/api/analyze -F "file=@test_beat.wav"
   ```

---

## Priority Order

1. **AcoustID** - Do this first (free, unlimited, easiest)
2. **ACRCloud** - Optional backup (higher accuracy)
3. **Audd.io** - Optional (includes Spotify links)

You only NEED AcoustID to get started. The others are optional backups.
