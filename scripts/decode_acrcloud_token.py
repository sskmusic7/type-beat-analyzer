#!/usr/bin/env python3
"""
Decode ACRCloud Personal Access Token (JWT) to understand its structure
"""
import os
import sys
import json
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(env_path)

token = os.getenv("ACRCLOUD_PERSONAL_ACCESS_TOKEN")

if not token:
    print("❌ No token found")
    sys.exit(1)

print("🔍 Decoding ACRCloud Personal Access Token")
print("=" * 50)

# JWT has 3 parts: header.payload.signature
parts = token.split('.')

if len(parts) != 3:
    print("❌ Invalid JWT format")
    sys.exit(1)

# Decode header
try:
    header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
    print("\n📋 Header:")
    print(json.dumps(header, indent=2))
except Exception as e:
    print(f"❌ Error decoding header: {e}")

# Decode payload
try:
    # Add padding if needed
    payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_padded))
    print("\n📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    # Extract useful info
    print("\n🔑 Extracted Information:")
    print(f"   Subject (User ID): {payload.get('sub', 'N/A')}")
    print(f"   Issued At: {payload.get('iat', 'N/A')}")
    print(f"   Expires At: {payload.get('exp', 'N/A')}")
    print(f"   Scopes: {', '.join(payload.get('scopes', [])[:5])}...")
    
    # Check if there's project info
    if 'project_id' in payload:
        print(f"   Project ID: {payload.get('project_id')}")
    if 'region' in payload:
        print(f"   Region: {payload.get('region')}")
        
except Exception as e:
    print(f"❌ Error decoding payload: {e}")

print("\n" + "=" * 50)
print("\n💡 Next steps:")
print("   1. Use this token with Console API to fetch project credentials")
print("   2. Or navigate to console and get project keys manually")
