#!/usr/bin/env python3
"""
Fetch ACRCloud project credentials using Personal Access Token
"""
import os
import sys
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
from app.acrcloud_console_api import ACRCloudConsoleAPI

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(env_path)

token = os.getenv("ACRCLOUD_PERSONAL_ACCESS_TOKEN")

print("🔍 ACRCloud Credential Fetcher")
print("=" * 50)
print(f"Token: {token[:30]}..." if token else "❌ No token found")
print()

if not token:
    print("❌ ACRCLOUD_PERSONAL_ACCESS_TOKEN not set in .env")
    sys.exit(1)

console_api = ACRCloudConsoleAPI(token)

print("📋 Step 1: Listing Base Projects...")
projects = console_api.list_base_projects()

if projects:
    print(f"✅ Found {len(projects)} project(s):")
    for i, project in enumerate(projects, 1):
        project_id = project.get("id") or project.get("project_id") or project.get("_id", "unknown")
        name = project.get("name") or project.get("title", "Unnamed")
        print(f"   {i}. {name} (ID: {project_id})")
    print()
    
    print("📋 Step 2: Fetching credentials from first project...")
    credentials = console_api.get_project_credentials()
    
    if credentials:
        print("✅ Successfully fetched credentials!")
        print()
        print("📝 Credentials:")
        print(f"   Access Key: {credentials['access_key']}")
        print(f"   Access Secret: {'*' * len(credentials['access_secret'])}")
        print(f"   Host: {credentials['host']}")
        print(f"   Project ID: {credentials['project_id']}")
        print()
        
        # Update .env file
        env_file = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
        
        # Read current .env
        env_content = ""
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_content = f.read()
        
        # Remove old ACRCloud credentials
        lines = env_content.split('\n')
        new_lines = []
        for line in lines:
            if not line.startswith('ACRCLOUD_ACCESS_KEY=') and \
               not line.startswith('ACRCLOUD_ACCESS_SECRET=') and \
               not line.startswith('ACRCLOUD_HOST='):
                new_lines.append(line)
        
        # Add new credentials
        new_lines.append(f"ACRCLOUD_ACCESS_KEY={credentials['access_key']}")
        new_lines.append(f"ACRCLOUD_ACCESS_SECRET={credentials['access_secret']}")
        new_lines.append(f"ACRCLOUD_HOST={credentials['host']}")
        
        with open(env_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ Saved to {env_file}")
        print()
        print("🎉 ACRCloud is now fully configured!")
        
    else:
        print("❌ Could not fetch credentials")
        print("   Trying to get project details manually...")
        
        if projects:
            project = projects[0]
            project_id = project.get("id") or project.get("project_id") or project.get("_id")
            if project_id:
                print(f"\n📋 Project details for {project_id}:")
                details = console_api.get_project(project_id)
                if details:
                    print(json.dumps(details, indent=2))
else:
    print("❌ No projects found")
    print()
    print("💡 You need to:")
    print("   1. Go to https://console.acrcloud.com/avr?region=eu-west-1#/dashboard")
    print("   2. Create a Base Project (AVR type)")
    print("   3. Run this script again")
    print()
    print("🔍 Trying to debug API connection...")
    
    # Try a simple API call to see what happens
    result = console_api._make_request("GET", "/base-projects")
    if result:
        print(f"API Response: {json.dumps(result, indent=2)}")
