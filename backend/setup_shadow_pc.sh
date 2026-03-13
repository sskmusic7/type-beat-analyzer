#!/bin/bash

# Setup Script for Shadow PC Training Server
# This script sets up the environment to run the webhook server

set -e

echo "========================================================================"
echo "🖥️  SHADOW PC TRAINING SERVER SETUP"
echo "========================================================================"

# Check if we're in the backend directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install additional FastAPI dependencies
pip install fastapi uvicorn httpx

# Set up Google Cloud credentials
echo ""
echo "🔑 Setting up Google Cloud credentials..."

if [ ! -f "shadow-pc-key.json" ]; then
    echo "❌ Error: shadow-pc-key.json not found!"
    echo "   Please place your service account key in the backend directory"
    exit 1
fi

# Set Google Application Credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/shadow-pc-key.json"
echo "✅ GOOGLE_APPLICATION_CREDENTIALS set"

# Add to .env if it doesn't exist
if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS" .env 2>/dev/null; then
    echo "GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/shadow-pc-key.json" >> .env
    echo "✅ Added to .env file"
fi

# Check environment variables
echo ""
echo "🔍 Checking environment variables..."

required_vars=(
    "YOUTUBE_API_KEY"
    "SPOTIFY_CLIENT_ID"
    "SPOTIFY_CLIENT_SECRET"
    "FINGERPRINT_BUCKET_NAME"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if grep -q "^$var=" .env 2>/dev/null; then
        echo "✅ $var is set"
    else
        echo "⚠️  $var is missing from .env"
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: The following variables are missing:"
    printf '   %s\n' "${missing_vars[@]}"
    echo ""
    echo "   You can add them to the .env file manually"
fi

# Create systemd service file (optional)
echo ""
echo "🚀 Creating systemd service file..."
cat > shadow-pc-trainer.service <<EOF
[Unit]
Description=Shadow PC Training Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
Environment="GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/shadow-pc-key.json"
ExecStart=$(pwd)/venv/bin/python shadow_pc_webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created shadow-pc-trainer.service"
echo ""
echo "   To install as system service, run:"
echo "   sudo mv shadow-pc-trainer.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable shadow-pc-trainer"
echo "   sudo systemctl start shadow-pc-trainer"

# Create startup script
echo ""
echo "📜 Creating startup script..."
cat > start_shadow_pc_server.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/shadow-pc-key.json"
echo "🚀 Starting Shadow PC Training Server..."
python shadow_pc_webhook_server.py
EOF

chmod +x start_shadow_pc_server.sh
echo "✅ Created start_shadow_pc_server.sh"

echo ""
echo "========================================================================"
echo "✅ SETUP COMPLETE!"
echo "========================================================================"
echo ""
echo "🚀 To start the server, run:"
echo "   ./start_shadow_pc_server.sh"
echo ""
echo "🔗 The server will listen on: http://0.0.0.0:8000"
echo ""
echo "📡 Your Cloud Run backend can now trigger training on this Shadow PC!"
echo ""
