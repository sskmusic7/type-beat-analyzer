# Spotify Redirect URI - Why It Doesn't Matter for Us

## 🔍 The Key Point

**We use Client Credentials flow** - which means:
- ✅ **No user login required**
- ✅ **No redirects happen**
- ✅ **Server-to-server authentication only**

## 📚 OAuth Flow Types

### Client Credentials Flow (What We Use)
```
Your Server → Spotify API
(No user involved, no redirects)
```

**Used for:**
- Server-to-server API calls
- No user authentication needed
- Just need Client ID + Secret

**Redirect URI:** Required by form, but **never actually used**

### Authorization Code Flow (What We DON'T Use)
```
User → Spotify Login → Redirect back to your app
```

**Used for:**
- User login features
- Accessing user's playlists, saved tracks, etc.
- Requires redirect URI to work

**Redirect URI:** Actually used to send user back after login

## 🎯 For Our Streaming Trainer

We only need:
- ✅ Search for tracks (`GET /search`)
- ✅ Get track preview URLs
- ✅ No user data needed

So we use **Client Credentials** - the simplest flow.

## 🌐 Redirect URI Options

### Option 1: Use Your Deployed URL
If you have Cloud Run deployment:
```
https://your-app-name-xxxxx.run.app/callback
```

### Option 2: Use Loopback IP (Local Development)
**Important:** `localhost` is NOT allowed by Spotify. Use explicit IP:

If only running locally:
```
http://127.0.0.1:3000/callback
```

**Why:** According to [Spotify's documentation](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri), `localhost` is not allowed - you must use `127.0.0.1` (IPv4) or `[::1]` (IPv6).

### Option 3: Use Both
For flexibility (can work locally and deployed):
```
http://127.0.0.1:3000/callback
https://your-deployed-url.com/callback
```

## ⚠️ Important: localhost is NOT Allowed

According to [Spotify's redirect URI documentation](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri):
- ❌ **`localhost` is NOT allowed**
- ✅ Use `http://127.0.0.1:PORT` (IPv4) or `http://[::1]:PORT` (IPv6)
- ✅ HTTP is allowed for loopback addresses (HTTPS not required for local)

## ✅ Bottom Line

**Any valid URL works** - it's just a form requirement. Since we use Client Credentials flow, the redirect URI is never called.

**Recommendation:** 
- For local development: Use `http://127.0.0.1:3000/callback` (NOT localhost)
- For production: Use `https://your-deployed-url.com/callback`
