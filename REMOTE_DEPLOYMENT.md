# 📱 Remote Deployment Guide

Access your Type Beat demos from anywhere on your network (phones, tablets, other computers).

---

## 🚀 Quick Start

### Option A: Streamlit Training Dashboard (Port 8501)

```bash
cd "/Users/sskmusic/Type beat"
./scripts/start_streamlit_remote.sh
```

### Option B: Full Web App - Upload Beats (Ports 3000 + 8000)

```bash
cd "/Users/sskmusic/Type beat"
./scripts/start_webapp_remote.sh
```

---

## 📍 Access URLs

| Service | This Machine | Other Devices |
|---------|--------------|---------------|
| **Streamlit Dashboard** | http://localhost:8501 | http://YOUR_IP:8501 |
| **Web App (Frontend)** | http://localhost:3000 | http://YOUR_IP:3000 |
| **Backend API** | http://localhost:8000 | http://YOUR_IP:8000 |

### Find Your IP

```bash
# Mac (WiFi)
ipconfig getifaddr en0

# Mac (Ethernet)
ipconfig getifaddr en1

# Linux
hostname -I | awk '{print $1}'
```

Example: If your IP is `192.168.1.100`, others can access:
- Streamlit: `http://192.168.1.100:8501`
- Web App: `http://192.168.1.100:3000`

---

## 🛡️ Firewall

If remote devices can't connect, allow these ports:

```bash
# Mac - allow incoming
sudo pfctl -d  # Disable firewall temporarily for testing

# Or add rules for ports 3000, 8000, 8501 in System Preferences > Security > Firewall
```

---

## 📋 Requirements

- **Streamlit**: Python + conda env `typebeat`
- **Web App**: Python (backend) + Node.js (frontend)
- All devices must be on same WiFi/network

---

## 🛑 Stop Services

Press **Ctrl+C** in the terminal where the script is running.

For web app, both backend and frontend will stop together.
