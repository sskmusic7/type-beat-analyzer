#!/usr/bin/env python3
"""
Test ACRCloud Identification API with provided credentials
"""
import os
import sys
import requests
import hashlib
import hmac
import base64
import time
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(env_path)

access_key = os.getenv("ACRCLOUD_ACCESS_KEY")
access_secret = os.getenv("ACRCLOUD_ACCESS_SECRET")
host = os.getenv("ACRCLOUD_HOST", "identify-eu-west-1.acrcloud.com")

print("🧪 Testing ACRCloud Identification API")
print("=" * 50)
print(f"Access Key: {access_key}")
print(f"Access Secret: {'*' * len(access_secret) if access_secret else 'NOT SET'}")
print(f"Host: {host}")
print()

if not access_key or not access_secret:
    print("❌ Missing credentials!")
    sys.exit(1)

# Create a minimal test audio file (1 second of silence)
# WAV format: 44.1kHz, 16-bit, mono
print("📝 Creating test audio file...")
wav_header = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
# Add 1 second of silence (44100 samples * 2 bytes = 88200 bytes)
silence = b'\x00\x00' * 44100
wav_data = wav_header + silence

# Update WAV header with correct file size
file_size = len(wav_data) - 8
wav_data = wav_data[:4] + file_size.to_bytes(4, 'little') + wav_data[8:]

# Save to temp file
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    f.write(wav_data)
    temp_file = f.name

print(f"✅ Created test file: {temp_file} ({len(wav_data)} bytes)")
print()

# Generate signature
print("🔐 Generating signature...")
timestamp = str(int(time.time()))
string_to_sign = f"POST\n/v1/identify\n{access_key}\naudio\n1\n{timestamp}"

signature = base64.b64encode(
    hmac.new(
        access_secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha1
    ).digest()
).decode('utf-8')

print(f"✅ Signature: {signature[:30]}...")
print()

# Make request
print(f"🌐 Making request to https://{host}/v1/identify...")
files = [
    ('sample', ('test.wav', wav_data, 'audio/wav'))
]
data = {
    'access_key': access_key,
    'sample_bytes': str(len(wav_data)),
    'timestamp': timestamp,
    'signature': signature,
    'data_type': 'audio',
    'signature_version': '1'
}

try:
    response = requests.post(
        f"https://{host}/v1/identify",
        files=files,
        data=data,
        timeout=30
    )
    
    print(f"📊 Response Status: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS! API is working!")
        print()
        print("Response:")
        print(f"   Status: {result.get('status', {}).get('msg', 'Unknown')}")
        print(f"   Code: {result.get('status', {}).get('code', 'Unknown')}")
        
        if result.get('status', {}).get('code') == 0:
            music = result.get('metadata', {}).get('music', [])
            if music:
                print(f"   Found {len(music)} match(es)")
                for track in music:
                    artist = track.get('artists', [{}])[0].get('name', 'Unknown')
                    title = track.get('title', 'Unknown')
                    score = track.get('score', 0)
                    print(f"   - {artist} - {title} (score: {score})")
            else:
                print("   No matches found (expected for silence)")
        else:
            print(f"   Error: {result.get('status', {}).get('msg', 'Unknown error')}")
    
    elif response.status_code == 401:
        print("❌ AUTHENTICATION FAILED")
        print("   The access_key/access_secret are invalid or not for Identification API")
        print("   You may need project-specific keys from a Base Project")
        print()
        print("Response:", response.text[:200])
    
    elif response.status_code == 403:
        print("❌ FORBIDDEN")
        print("   The credentials don't have permission for Identification API")
        print()
        print("Response:", response.text[:200])
    
    else:
        print(f"❌ Request failed with status {response.status_code}")
        print("Response:", response.text[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Clean up
    try:
        os.unlink(temp_file)
    except:
        pass

print()
print("=" * 50)
