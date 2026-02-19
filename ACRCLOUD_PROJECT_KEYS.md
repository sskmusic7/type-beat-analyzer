# Finding ACRCloud Identification API Project Keys

## ⚠️ Important Distinction

ACRCloud has **two types of credentials**:

1. **Console API Keys** (Old Access Keys) - For managing the console, projects, etc.
   - Found at: `console.acrcloud.com/account#/old-accesskeys`
   - ❌ **DO NOT USE** for Identification API

2. **Project Identification API Keys** - For identifying audio files
   - Found in: Your Base Project (AVR type) settings
   - ✅ **USE THESE** for Identification API

## How to Find Project-Specific Keys

### Step 1: Navigate to Dashboard
1. Go to: https://console.acrcloud.com/avr?region=eu-west-1#/dashboard
2. Log in with your account

### Step 2: Find or Create a Base Project
1. Look for **"Base Projects"** or **"Projects"** in the sidebar
2. If you don't have a project:
   - Click **"Create Project"** or **"New Project"**
   - Select project type: **"AVR"** (Audio/Video Recognition)
   - Give it a name (e.g., "Type Beat Identifier")
   - Create the project

### Step 3: Get Project Credentials
1. Click on your project to open it
2. Look for:
   - **"Project Settings"**
   - **"API Keys"** or **"Credentials"**
   - **"Access Key"** and **"Access Secret"**
3. These are the keys you need!

### Step 4: Note the Host
The host depends on your region:
- EU: `identify-eu-west-1.acrcloud.com`
- US West: `identify-us-west-2.acrcloud.com`
- US East: `identify-us-east-1.acrcloud.com`
- Asia: `identify-ap-southeast-1.acrcloud.com`

Check your project settings to see which region it's in.

## Testing Your Keys

The keys you provided (`rPuhqHhPN7idRMQX` / `n49m5IoqZQNmxj5gRsIYptZUFJ1kQ8G9`) might work if they're from a project, but if they're from "Old Access Keys", they won't work for Identification API.

### Quick Test
Run this to test if your keys work:

```bash
python3 scripts/test_acrcloud_api.py
```

### Full Test with Audio
To fully test, you need to make an actual API call with an audio file. The backend will do this automatically when you upload a beat.

## Current Configuration

Your `.env` currently has:
```
ACRCLOUD_ACCESS_KEY=rPuhqHhPN7idRMQX
ACRCLOUD_ACCESS_SECRET=n49m5IoqZQNmxj5gRsIYptZUFJ1kQ8G9
ACRCLOUD_HOST=identify-eu-west-1.acrcloud.com
```

If these don't work (you'll get authentication errors), you need to:
1. Navigate to your Base Project in the console
2. Copy the project's `access_key` and `access_secret`
3. Update `.env` with those values

## Reference

- [ACRCloud Identification API Docs](https://docs.acrcloud.com/reference/identification-api/identification-api#identifying-an-audio-file-or-a-fingerprint-file)
- [ACRCloud Console](https://console.acrcloud.com)
