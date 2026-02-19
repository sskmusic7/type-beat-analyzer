# Gemini 3D Visualization Generator - Dashboard Guide

## 🎉 What's New

Your Streamlit dashboard now has a **"✨ Gemini 3D Generator"** tab that lets you generate interactive 3D visualizations using Google Gemini AI!

## 🚀 How to Use

### Step 1: Start the Dashboard
```bash
cd ml
streamlit run training_dashboard.py
```

### Step 2: Navigate to Gemini Tab
1. Open the dashboard at `http://localhost:8501`
2. Click on the **"✨ Gemini 3D Generator"** tab

### Step 3: Generate a Visualization

**Option A: Use Example Prompts**
- Select a pre-written example from the dropdown
- Click "🚀 Generate 3D Visualization"

**Option B: Write Your Own Prompt**
- Select "Custom..." from the dropdown
- Type your visualization request in the text area
- Click "🚀 Generate 3D Visualization"

### Step 4: View Results
- **Generated Code**: See the Python code Gemini created
- **Visualization**: See the interactive 3D plot (if auto-execute is enabled)
- **Download**: Save the code for later use

## 📝 Example Prompts

### Basic 3D Scatter Plot
```
Create a 3D scatter plot of audio fingerprint embeddings after PCA reduction, 
colored by artist name, with hover tooltips showing track names
```

### 3D Surface Spectrogram
```
Generate a 3D surface plot of a mel-spectrogram showing time on X-axis, 
frequency on Y-axis, and magnitude as height/color
```

### Clustering Visualization
```
Make an interactive 3D scatter plot using t-SNE to visualize fingerprint clusters, 
with different colors for each artist and hover tooltips
```

### Comparison Chart
```
Create a 3D bar chart comparing fingerprint counts across different artists
```

## ⚙️ Features

### Auto-Load Training Data
- If you have training data, it's automatically loaded
- Gemini uses this context to generate better visualizations
- Your actual fingerprints, artists, and tracks are available in the code

### Code Generation
- Complete, working Python code
- Uses Plotly for interactivity
- Compatible with Streamlit
- Ready to run

### Safe Execution
- Code runs in a sandboxed environment
- Only safe libraries are available
- Your data is protected

### Download & Reuse
- Download generated code
- Use in your own scripts
- Customize as needed

## 🎨 Tips for Best Results

### ✅ Good Prompts Include:
- **Visualization type**: "scatter plot", "surface plot", "bar chart"
- **Data description**: "fingerprint embeddings", "mel-spectrogram", "training data"
- **Features**: "colored by artist", "hover tooltips", "interactive"
- **Library**: "using Plotly" (recommended)

### ❌ Avoid:
- Vague requests: "make a graph"
- Missing context: "show data" (what data?)
- Unrealistic expectations: "create a 4D plot" (not possible)

## 🔧 Advanced Options

### Show Generated Code
- ✅ Enabled by default
- See exactly what Gemini created
- Learn from the code structure

### Auto-Execute
- ✅ Enabled by default
- Automatically runs code after generation
- Shows visualization immediately

## 🐛 Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure the key is in `backend/.env`
- Format: `GEMINI_API_KEY=your_key_here`
- Restart the dashboard after adding

### "Error generating code"
- Check your internet connection
- Verify API key is valid
- Try a simpler prompt

### "Error executing code"
- Review the generated code
- Check if data is available
- Try adjusting your prompt

### Visualization doesn't show
- Make sure "Auto-execute" is enabled
- Check the error message
- Try downloading and running code manually

## 📚 Integration with Your Data

The generator automatically:
- ✅ Loads your training fingerprints
- ✅ Provides artist and track information
- ✅ Makes embeddings available as numpy arrays
- ✅ Includes metadata in context

**Available variables in generated code:**
- `embeddings`: numpy array of fingerprint embeddings
- `fingerprints`: list of fingerprint vectors
- `artists`: list of artist names
- `tracks`: list of track names
- `training_data`: full training data dictionary

## 🎯 Next Steps

1. **Try different prompts** to see what Gemini can create
2. **Download useful code** for your own projects
3. **Customize generated code** to fit your needs
4. **Share visualizations** with your team

## 💡 Pro Tips

1. **Be specific**: More details = better results
2. **Use examples**: Start with example prompts, then customize
3. **Iterate**: If first result isn't perfect, refine your prompt
4. **Save good code**: Download code that works well
5. **Combine**: Use multiple visualizations for comprehensive analysis

---

**Enjoy generating amazing 3D visualizations! 🎨✨**
