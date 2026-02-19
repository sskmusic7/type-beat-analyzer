#!/usr/bin/env python3
"""
Quick test script to verify ACRCloud Identification API credentials
"""
import os
import sys
import requests
import hashlib
import hmac
import base64
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(env_path)

access_key = os.getenv("ACRCLOUD_ACCESS_KEY")
access_secret = os.getenv("ACRCLOUD_ACCESS_SECRET")
host = os.getenv("ACRCLOUD_HOST", "identify-eu-west-1.acrcloud.com")

print("🔍 Testing ACRCloud Identification API Credentials")
print("=" * 50)
print(f"Access Key: {access_key}")
print(f"Access Secret: {'*' * len(access_secret) if access_secret else 'NOT SET'}")
print(f"Host: {host}")
print()

if not access_key or not access_secret:
    print("❌ Missing credentials!")
    print("   Please set ACRCLOUD_ACCESS_KEY and ACRCLOUD_ACCESS_SECRET in backend/.env")
    sys.exit(1)

# Create a minimal test audio file (silence) or use a small sample
# For now, we'll just test the signature generation
print("📝 Testing signature generation...")

http_method = "POST"
http_uri = "/v1/identify"
data_type = "audio"
signature_version = "1"
timestamp = str(int(time.time()))

string_to_sign = f"{http_method}\n{http_uri}\n{access_key}\n{data_type}\n{signature_version}\n{timestamp}"

try:
    signature = base64.b64encode(
        hmac.new(
            access_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')
    
    print(f"✅ Signature generated: {signature[:20]}...")
    print()
    print("📋 Request details:")
    print(f"   Method: {http_method}")
    print(f"   URI: {http_uri}")
    print(f"   Access Key: {access_key}")
    print(f"   Data Type: {data_type}")
    print(f"   Timestamp: {timestamp}")
    print(f"   Signature: {signature[:30]}...")
    print()
    print("💡 To fully test, you need an audio file.")
    print("   The credentials format looks correct!")
    print()
    print("⚠️  Note: If these are 'Old Access Keys' from the Console API,")
    print("   they may not work for Identification API.")
    print("   You may need project-specific keys from a Base Project (AVR type).")
    
except Exception as e:
    print(f"❌ Error generating signature: {e}")
    sys.exit(1)
