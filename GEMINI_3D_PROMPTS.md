# Quick Reference: Gemini 3D Visualization Prompts

## Copy-Paste Ready Prompts for Gemini

### For Audio Fingerprint Embeddings

1. **Basic 3D Scatter Plot**
```
Create a 3D scatter plot in Python using Plotly that visualizes audio fingerprint embeddings. 
The embeddings are 128-dimensional numpy arrays. Use PCA to reduce them to 3D, then create 
an interactive scatter plot colored by artist name. Include hover tooltips showing track 
name and artist. Make it rotatable and zoomable.
```

2. **3D Clustering with t-SNE**
```
Generate Python code using Plotly to create a 3D scatter plot of audio fingerprints. 
Use t-SNE to reduce 128-dimensional embeddings to 3D. Color points by artist, add 
hover tooltips with track information, and make the plot interactive with rotation 
and zoom controls.
```

3. **3D Surface Spectrogram**
```
Create a 3D surface plot in Python using Plotly that visualizes a mel-spectrogram. 
X-axis should be time in seconds, Y-axis should be frequency in Hz, and Z-axis 
(height/color) should be magnitude in dB. Use librosa to generate the spectrogram 
from an audio file. Make it interactive and use a Viridis color scale.
```

4. **Multi-Artist 3D Comparison**
```
Generate Python code to create an interactive 3D scatter plot showing audio 
fingerprint embeddings from multiple artists. Each artist should have a different 
color. Use PCA to reduce 128-dim embeddings to 3D. Add a legend, hover tooltips, 
and make it work in Streamlit with st.plotly_chart().
```

5. **3D Embedding Evolution**
```
Create a 3D line plot in Python using Plotly that shows how audio fingerprint 
embeddings change over time for a single track. Plot the trajectory through 
3D space (after PCA reduction) with time as a color gradient. Make it 
interactive and animated if possible.
```

### For Training Process Visualization

6. **Real-Time 3D Training Progress**
```
Generate Python code for a Streamlit dashboard that shows real-time 3D scatter 
plots of fingerprints as they're being generated during training. Update the 
plot dynamically as new fingerprints are added. Use Plotly and Streamlit's 
st.plotly_chart() with use_container_width=True.
```

7. **3D Fingerprint Statistics**
```
Create a 3D bar chart in Python using Plotly that compares fingerprint statistics 
across different artists. X-axis: artist names, Y-axis: number of fingerprints, 
Z-axis: average similarity score. Make it interactive with hover tooltips showing 
exact values.
```

8. **3D Similarity Matrix**
```
Generate Python code to create a 3D surface plot showing the similarity matrix 
between audio fingerprints. X and Y axes represent fingerprint indices, Z-axis 
(height/color) represents similarity scores. Use Plotly with a heatmap-like 
color scale.
```

### Advanced Visualizations

9. **3D Mesh Fingerprint**
```
Create a 3D mesh plot in Python using PyVista or Mayavi that visualizes an 
audio fingerprint as a 3D geometric shape. The fingerprint data should be 
converted to a mesh surface. Make it rotatable and exportable.
```

10. **Interactive 3D Dashboard**
```
Generate a complete Streamlit app with multiple 3D visualizations:
1. 3D scatter plot of embeddings (PCA reduced)
2. 3D surface plot of a spectrogram
3. 3D line plot showing training progress
All should be interactive, use Plotly, and update in real-time.
```

---

## How to Use These Prompts

1. **Copy a prompt** from above
2. **Paste into Google Gemini** (gemini.google.com or API)
3. **Gemini generates complete Python code**
4. **Copy the code** and integrate into your project
5. **Customize** as needed for your data format

---

## Example Workflow

### Step 1: Ask Gemini
```
Create a 3D scatter plot in Python using Plotly that visualizes audio fingerprint 
embeddings. The embeddings are 128-dimensional numpy arrays. Use PCA to reduce 
them to 3D, then create an interactive scatter plot colored by artist name.
```

### Step 2: Gemini Returns Code
```python
from sklearn.decomposition import PCA
import plotly.graph_objects as go
import numpy as np

# Your embeddings (128-dim)
embeddings = np.array([...])  # Your data here

# Reduce to 3D
pca = PCA(n_components=3)
embeddings_3d = pca.fit_transform(embeddings)

# Create plot
fig = go.Figure(data=[go.Scatter3d(
    x=embeddings_3d[:, 0],
    y=embeddings_3d[:, 1],
    z=embeddings_3d[:, 2],
    mode='markers',
    marker=dict(size=5, color=artist_indices, colorscale='Viridis')
)])
fig.show()
```

### Step 3: Integrate into Your Code
- Add to `ml/visualize_fingerprints.py`
- Add to `ml/training_dashboard.py`
- Test with your actual fingerprint data

---

## Tips for Best Results

1. **Be Specific**: Mention library (Plotly, Matplotlib), data format, and requirements
2. **Include Context**: "For audio fingerprinting", "in Streamlit", etc.
3. **Specify Interactivity**: "Interactive", "rotatable", "with hover tooltips"
4. **Mention Integration**: "Works with Streamlit", "compatible with my existing code"
5. **Request Customization**: "Color by artist", "show track names on hover"

---

## Common Modifications After Gemini Generates Code

1. **Update data loading** to match your format
2. **Adjust colors** to match your theme
3. **Add Streamlit integration** if needed
4. **Customize labels** and titles
5. **Add error handling** for edge cases
6. **Optimize performance** for large datasets

---

## Next Steps

1. Try a prompt with Gemini
2. Get the generated code
3. Test it with your fingerprint data
4. Integrate into your dashboard
5. Share results or ask for refinements!
