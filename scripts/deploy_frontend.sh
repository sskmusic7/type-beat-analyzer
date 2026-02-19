#!/bin/bash
# Deploy frontend to Netlify

set -e
cd "$(dirname "$0")/../frontend"

# Check if netlify CLI is installed
if ! command -v netlify &> /dev/null; then
  echo "📦 Installing Netlify CLI..."
  npm install -g netlify-cli
fi

# Check if logged in
if ! netlify status &> /dev/null; then
  echo "🔐 Please login to Netlify:"
  netlify login
fi

# Deploy
echo "🚀 Deploying to Netlify..."
netlify deploy --prod

echo ""
echo "✅ Frontend deployed!"
echo "📍 Check the URL above or run: netlify status"
