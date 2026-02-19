# Spotify App Creation Form - How to Fill

## Form Fields Guide

### ✅ App name *
**Fill with:** `Type Beat Trainer`
(Or keep "Type Beat" if you prefer)

### ✅ App description *
**Fill with:** `Automated training data collection for type beat classification using audio fingerprinting`
(Or keep the existing description if you prefer)

### 🌐 Website
**Fill with:** `http://localhost:3000`
(Optional - can leave empty, but localhost is fine for development)

### 🔗 Redirect URIs *
**Important:** According to [Spotify's documentation](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri), **`localhost` is NOT allowed**. You must use explicit IP addresses.

**Requirements:**
- ❌ `localhost` is **NOT allowed**
- ✅ Use `127.0.0.1` (IPv4) or `[::1]` (IPv6) for loopback
- ✅ HTTP is allowed for loopback addresses (HTTPS not required)
- ✅ Must match exactly when used

**For local development, use:**
```
http://127.0.0.1:3000/callback
```
(Click "Add" after entering)

**If you have a deployed URL (HTTPS required):**
```
https://your-app-url.run.app/callback
```
(Click "Add" after entering)

**Note:** We use Client Credentials flow (server-to-server), so redirect URIs are never actually called - but Spotify requires at least one valid URI in the form.

### 📡 Which API/SDKs are you planning to use?
**Check:** ✅ **Web API**

**Why:** We only need the Web API for:
- `GET /search` - To search for tracks by artist
- Access to track `preview_url` fields

**Don't check:**
- ❌ Web Playback SDK (we don't play music)
- ❌ Android (we're using Python/backend)
- ❌ iOS (we're using Python/backend)
- ❌ Ads API (not needed)

### ✅ Terms Checkbox
**Check:** ✅ "I understand and agree with Spotify's Developer Terms of Service and Design Guidelines"

**Required** - You must check this to create the app.

## Important Notes from Forum

1. **Premium Account:** Only YOUR main account needs Premium (not test users)
2. **Existing Apps:** If you have existing Client IDs, they keep working until March 9
3. **New Apps (after Feb 11):** Automatically get the new restrictions:
   - Max 5 authorized users
   - Limited endpoints (but `GET /search` is still available ✅)
4. **Development Mode:** These restrictions only apply to Development Mode
   - Extended Quota Mode (requires review) has different rules

## What Happens After You Click "Save"

1. You'll see your **Client ID** (visible immediately)
2. You'll see your **Client Secret** (click "Show" to reveal)
3. Copy both to `backend/.env`:
   ```bash
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```

## Quick Checklist

- [ ] App name filled
- [ ] App description filled
- [ ] Website: `http://localhost:3000` (or empty)
- [ ] Redirect URI: `http://localhost:3000/callback` (click Add)
- [ ] ✅ Web API checked
- [ ] ✅ Terms checkbox checked
- [ ] Click "Save"
- [ ] Copy Client ID and Client Secret
- [ ] Add to `backend/.env`

## Our Use Case Summary

**What we need:**
- ✅ Web API access
- ✅ `GET /search` endpoint (still available)
- ✅ Track `preview_url` access (still available)
- ✅ Client Credentials flow (no user login needed)

**What we DON'T need:**
- ❌ User authentication (no redirect needed in practice)
- ❌ Playback SDK
- ❌ Mobile SDKs
- ❌ User playlists (we just search)

**Result:** Our streaming trainer is fully compatible! ✅
