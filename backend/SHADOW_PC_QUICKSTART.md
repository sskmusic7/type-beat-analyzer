# Shadow PC Quick Start

## What You Need to Do

### 1. On Your Shadow PC

#### Copy files to Shadow PC:
```bash
# From your Mac, run this in the Type beat directory
scp -r "Type beat/backend" your-shadow-pc-user@your-shadow-pc-ip:~/
```

#### On Shadow PC, run setup:
```bash
cd backend
bash setup_shadow_pc.sh
```

#### Start the server:
```bash
bash start_shadow_pc_server.sh
```

### 2. Get Your Shadow PC IP

```bash
# On Shadow PC, run:
curl ifconfig.me
```

### 3. Update Cloud Run Environment

In Google Cloud Console:
1. Go to Cloud Run → your service
2. Click "Edit & Deploy New Revision"
3. Add variable: `SHADOW_PC_WEBHOOK_URL=http://YOUR_IP:8000`
4. Deploy

### 4. Test It

From your Mac:
```bash
curl http://YOUR_SHADOW_PC_IP:8000/health
```

Expected response:
```json
{"status":"healthy","timestamp":"..."}
```

## That's It!

Your app will now send training requests to your Shadow PC instead of timing out on Cloud Run!

## File Checklist

Make sure these are on your Shadow PC in `/backend/`:
- ✅ `shadow_pc_webhook_server.py`
- ✅ `ml/hybrid_trainer.py`
- ✅ `app/fingerprint_service_cloud_storage.py`
- ✅ `shadow-pc-key.json`
- ✅ `.env` (with API keys)
- ✅ `requirements.txt`

## Environment Variables Needed

Create `.env` file:
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/shadow-pc-key.json
FINGERPRINT_BUCKET_NAME=type-beat-fingerprints
YOUTUBE_API_KEY=your_key_here
SPOTIFY_CLIENT_ID=your_id (optional)
SPOTIFY_CLIENT_SECRET=your_secret (optional)
```

## Troubleshooting

**Server won't start?**
```bash
# Check if port 8000 is in use
lsof -i :8000
```

**Can't connect from Cloud Run?**
- Check firewall: Allow port 8000
- Check IP: `curl ifconfig.me` on Shadow PC
- Test locally: `curl http://localhost:8000/health`

**YouTube failing?**
- Check YOUTUBE_API_KEY in `.env`
- Verify internet connection on Shadow PC

---

**🚀 Once setup is complete, your app can trigger training on demand!**
