# Fingerprint Visualization Guide

## 🎨 What We Built

### 1. **Fingerprint Visualizer** (`ml/visualize_fingerprints.py`)
- ✅ Mel-spectrogram generation from audio
- ✅ 128-dim embedding vector visualization
- ✅ Embedding space visualization (t-SNE/UMAP)
- ✅ Training summary charts

### 2. **Streamlit Dashboard** (`ml/training_dashboard.py`)
- ✅ Real-time training progress
- ✅ Live fingerprint visualization
- ✅ Training statistics
- ✅ Fingerprint explorer

## 🚀 Quick Start

### Install Dependencies

```bash
cd ml
pip install streamlit plotly seaborn umap-learn pandas
```

### Run Dashboard

```bash
cd ml
streamlit run training_dashboard.py
```

Dashboard opens at: `http://localhost:8501`

## 📊 Visualization Types

### 1. Mel-Spectrogram
- **What**: Frequency content over time
- **Shows**: How audio energy is distributed across frequencies
- **Use**: See the "fingerprint" of the audio visually

### 2. Embedding Vector (128-dim)
- **What**: Bar chart of fingerprint values
- **Shows**: The 128 numbers that represent the audio
- **Use**: Compare fingerprints visually

### 3. Embedding Space (t-SNE/UMAP)
- **What**: 2D projection of high-dimensional fingerprints
- **Shows**: Clusters of similar beats/artists
- **Use**: See which artists/beats are similar

### 4. Training Statistics
- **What**: Charts showing training progress
- **Shows**: Fingerprints per artist, source breakdown
- **Use**: Monitor training effectiveness

## 🎯 Features

### Live Training Tab
- Real-time progress bar
- Current artist/track display
- Live fingerprint visualization
- Automatic updates

### Training Summary Tab
- Artist counts chart
- Source breakdown (YouTube vs Spotify)
- Sample fingerprint visualization
- Embedding space plot

### Fingerprint Explorer Tab
- Browse all fingerprints
- View individual fingerprint vectors
- See metadata for each

### Statistics Tab
- Total fingerprints
- Unique artists
- Source breakdown
- Artist breakdown table

## 🔧 Integration Options

### Option 1: Standalone Streamlit (Easiest)
- Run separately from main app
- Perfect for training monitoring
- No integration needed

### Option 2: FastAPI + Next.js (Integrated)
- Add WebSocket endpoint to FastAPI
- Create React components for visualization
- Integrate with existing frontend

### Option 3: API Endpoints (Hybrid)
- FastAPI serves visualization images
- Next.js displays them
- Best of both worlds

## 📦 Dependencies

```python
# Core visualization
librosa.display    # Mel-spectrograms
matplotlib         # Static plots
plotly             # Interactive plots

# Embedding visualization
scikit-learn       # t-SNE
umap-learn         # UMAP

# UI
streamlit          # Dashboard
pandas             # Data handling
```

## 🎨 Example Usage

### Generate Single Visualization

```python
from visualize_fingerprints import FingerprintVisualizer

visualizer = FingerprintVisualizer()

# From audio file
img = visualizer.generate_mel_spectrogram("audio.wav", title="My Beat")

# From fingerprint
fp = np.array([0.23, 0.45, ...])  # 128-dim
img = visualizer.visualize_embedding_vector(fp)
```

### Visualize Training Data

```python
from visualize_fingerprints import visualize_training_file

visualizations = visualize_training_file("final_training_data.json")
# Returns dict with base64 images
```

## 🔗 Research Sources

Based on research from:
- **librosa** - Industry standard for audio visualization
- **Plotly** - Most popular interactive visualization library
- **Streamlit** - Fastest way to build Python dashboards
- **GitHub projects**: librosa, plotly, streamlit, dejavu, audfprint

## 🎯 Next Steps

1. **Run dashboard**: `streamlit run ml/training_dashboard.py`
2. **Start training**: Use "Live Training" tab
3. **View results**: Check "Training Summary" tab
4. **Explore**: Use "Fingerprint Explorer" tab

The dashboard provides real-time visualization of the entire training process!
