# Shadow PC Training Server - Quick Setup

**Complete setup package for Shadow PC webhook training server**

---

## 🎯 What This Does

Runs a webhook server on Shadow PC that:
- Receives training requests from your admin panel
- Downloads from YouTube (residential IP = no blocking!)
- Generates fingerprints
- Uploads to Google Cloud Storage
- Your app reads from Cloud Storage

---

## 📋 Setup Instructions

### Step 1: Install Python 3.10

**Download from:** https://www.python.org/downloads/release/python-31011/
- Download "Windows installer (64-bit)"
- Run installer
- ✅ Check "Add Python to PATH"
- Click "Install Now"

**Verify:**
```powershell
python --version
# Should output: Python 3.10.x
```

### Step 2: Extract Files

Extract this entire folder to: `C:\Users\Shadow\Type-beat`

### Step 3: Install Dependencies

```powershell
cd C:\Users\Shadow\Type-beat

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies (takes 5-10 minutes)
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```powershell
# Copy example file
copy .env.example .env

# Edit with your actual values
notepad .env
```

**Add your API keys to .env:**
```bash
YOUTUBE_API_KEY=your-youtube-api-key-here
SPOTIFY_CLIENT_ID=your-spotify-client-id-here
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret-here
```

### Step 5: Download Service Account Key

**Get from Google Cloud Console:**
1. Go to: https://console.cloud.google.com/
2. Navigate to your project
3. IAM & Admin → Service Accounts
4. Find "shadow-pc-trainer"
5. Keys → Add Key → Create JSON
6. Download and save to: `C:\Users\Shadow\Type-beat\shadow-pc-key.json`

### Step 6: Start Webhook Server!

```powershell
cd C:\Users\Shadow\Type-beat
.\venv\Scripts\activate
python shadow_pc_webhook_server.py
```

**Expected output:**
```
🚀 Starting Shadow PC Training Webhook Server
   Listening on: http://0.0.0.0:8000
   Shadow PC IP: 46.247.137.210

Endpoints:
  GET  /              - Health check
  GET  /health        - Health check
  POST /train/start   - Start training
  GET  /train/status  - Get training status
  POST /train/stop    - Stop training

INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Test Webhook Server

**From your Mac terminal:**
```bash
curl http://46.247.137.210:8000/health
```

**Expected response:**
```json
{
  "status": "ok",
  "message": "Shadow PC Training Server is running",
  "is_training": false,
  "shadow_pc_ip": "46.247.137.210"
}
```

---

## 🧪 Testing from Admin Panel

**Your Cloud Run backend will auto-deploy soon. Once deployed:**

1. Open your Type Beat website
2. Go to Admin Panel → Training
3. Enter artist: "Drake"
4. Click "Start Training"

**What happens:**
1. Admin panel sends request to Shadow PC ✅
2. Shadow PC downloads from YouTube ✅
3. Fingerprints uploaded to Cloud Storage ✅
4. App reads new fingerprints ✅

---

## 🔄 Auto-Start on Boot (Optional)

**Create batch script:** `start_webhook_server.bat`
```powershell
@echo off
cd C:\Users\Shadow\Type-beat
call venv\Scripts\activate.bat
python shadow_pc_webhook_server.py
```

**Add to Windows startup:**
- Press `Win + R`
- Type: `shell:startup`
- Copy `start_webhook_server.bat` there

---

## 📊 Architecture

```
Admin Panel (Cloud Run)
    ↓ HTTP
Shadow PC Webhook Server
    ↓ YouTube Downloads
Fingerprint Generation
    ↓ Upload
Google Cloud Storage
    ↓ Read
Your App
```

---

## ✅ Success Checklist

- [ ] Python 3.10 installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env configured with API keys
- [ ] Service account key downloaded
- [ ] Webhook server running
- [ ] Health check successful
- [ ] Ready for training!

---

## 🆘 Troubleshooting

**"Python not found"**
- Make sure Python 3.10 is in PATH
- Reboot Shadow PC

**"Module not found"**
- Activate venv: `.\venv\Scripts\activate`
- Reinstall: `pip install -r requirements.txt`

**"Cannot connect"**
- Check firewall allows port 8000
- Make sure webhook server is running

**"Service account error"**
- Verify key file exists: `dir shadow-pc-key.json`
- Check path in .env is correct

---

## 🎉 Once Running

Your webhook server will:
- ✅ Listen for training requests from admin panel
- ✅ Download from YouTube (no blocking!)
- ✅ Generate fingerprints
- ✅ Upload to Cloud Storage
- ✅ Keep your app updated with new fingerprints

**Your Type Beat analyzer is now fully functional!** 🎵🚀
