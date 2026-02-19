# Gemini API Setup Guide

## 🔑 Getting Your API Key

### Step 1: Create API Key
1. Go to **[Google AI Studio](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your API key

### Step 2: Enable Models
When creating your API key, make sure these models are enabled (February 2026):
- ✅ **gemini-2.5-flash** (Latest stable - Recommended)
- ✅ **gemini-2.5-flash-image** (Latest with enhanced image capabilities)
- ✅ **gemini-3-flash-preview** (Latest preview - faster)
- ✅ **gemini-3-pro-preview** (Latest preview - best quality)
- ✅ **gemini-1.5-pro** (Fallback)
- ✅ **gemini-1.5-flash** (Fallback)

**Note:** New API keys usually have all models enabled by default, but check your API key settings to confirm.

### Step 3: Add to Your Project
Add your API key to `backend/.env`:
```bash
GEMINI_API_KEY=your_api_key_here
```

## 🎯 Which Model to Use?

The dashboard will automatically detect and use the best available model (February 2026):
1. **gemini-2.5-flash** - Latest stable, recommended (if available)
2. **gemini-2.5-flash-image** - Latest with image capabilities (if available)
3. **gemini-3-flash-preview** - Latest preview, fastest (if available)
4. **gemini-3-pro-preview** - Latest preview, best quality (if available)
5. **gemini-1.5-pro** - Fallback (if available)
6. **gemini-1.5-flash** - Fallback (if available)

## ✅ Verify Your Setup

After adding your API key, restart the dashboard:
```bash
cd ml
streamlit run training_dashboard.py
```

Then go to the **"✨ Gemini 3D Generator"** tab. If you see:
- ✅ "Loaded X fingerprints for context" - You're good!
- ❌ "GEMINI_API_KEY not found" - Check your `.env` file
- ❌ "404 models/gemini-pro is not found" - Your API key doesn't have access to that model

## 🔧 Troubleshooting

### "404 models/gemini-pro is not found"
**Solution:** Your API key might not have access to `gemini-pro`. The code will automatically try:
1. `gemini-1.5-pro`
2. `gemini-1.5-flash`
3. `gemini-pro`

If none work, check your API key permissions in Google AI Studio.

### "API key is invalid"
**Solution:**
1. Verify the key is correct in `backend/.env`
2. Make sure there are no extra spaces
3. Regenerate the key if needed

### "Rate limit exceeded"
**Solution:**
- Free tier has rate limits
- Wait a few minutes and try again
- Consider upgrading to paid tier for higher limits

## 📚 Resources

- [Google AI Studio](https://aistudio.google.com/) - Create/manage API keys
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs) - Official documentation
- [Gemini Cookbook](https://github.com/google-gemini/cookbook) - Examples and guides

## 🚀 Next Steps

Once your API key is set up:
1. Restart the Streamlit dashboard
2. Go to "✨ Gemini 3D Generator" tab
3. Try generating a visualization!

---

**Need help?** Check the error message in the dashboard - it will tell you exactly what's wrong!
