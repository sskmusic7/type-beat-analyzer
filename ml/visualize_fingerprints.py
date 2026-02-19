"""
Fingerprint Visualization Module
Creates spectral visualizations for fingerprints and training process
"""

import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import json
import base64
from io import BytesIO


class FingerprintVisualizer:
    """
    Creates visualizations for audio fingerprints
    - Mel-spectrograms
    - Embedding vectors
    - Embedding space (t-SNE/UMAP)
    - Training progress
    """
    
    def __init__(self, output_dir: str = "data/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_mel_spectrogram(self, audio_path: str, 
                                  title: Optional[str] = None) -> str:
        """
        Generate mel-spectrogram visualization from audio file
        
        Args:
            audio_path: Path to audio file
            title: Optional title for plot
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=22050, mono=True)
            
            # Generate mel-spectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, n_mels=256, fmax=8000
            )
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            # Create plot
            fig, ax = plt.subplots(figsize=(12, 6))
            img = librosa.display.specshow(
                mel_spec_db,
                x_axis='time',
                y_axis='mel',
                sr=sr,
                fmax=8000,
                cmap='viridis',
                ax=ax
            )
            
            if title:
                ax.set_title(title, fontsize=14, fontweight='bold')
            else:
                ax.set_title('Mel-Spectrogram', fontsize=14, fontweight='bold')
            
            fig.colorbar(img, ax=ax, format='%+2.0f dB')
            plt.tight_layout()
            
            # Convert to base64
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"Error generating spectrogram: {e}")
            return None
    
    def visualize_embedding_vector(self, fingerprint: np.ndarray,
                                  title: Optional[str] = None) -> str:
        """
        Visualize 128-dim fingerprint as bar chart
        
        Args:
            fingerprint: 128-dim embedding vector
            title: Optional title
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            fig, ax = plt.subplots(figsize=(14, 6))
            
            ax.bar(range(len(fingerprint)), fingerprint, alpha=0.7, color='purple')
            ax.set_xlabel('Dimension', fontsize=12)
            ax.set_ylabel('Value', fontsize=12)
            ax.set_title(title or 'Fingerprint Embedding Vector (128-dim)', 
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"Error visualizing embedding: {e}")
            return None
    
    def visualize_embedding_space(self, fingerprints: List[np.ndarray],
                                  labels: List[str],
                                  method: str = 'tsne') -> str:
        """
        Visualize fingerprints in 2D space using t-SNE or UMAP
        
        Args:
            fingerprints: List of 128-dim vectors
            labels: List of artist names (for coloring)
            method: 'tsne' or 'umap'
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            from sklearn.manifold import TSNE
            import umap
            
            # Stack fingerprints
            X = np.array(fingerprints)
            
            # Reduce dimensionality
            if method == 'tsne':
                reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(X)-1))
                X_2d = reducer.fit_transform(X)
            else:  # umap
                reducer = umap.UMAP(n_components=2, random_state=42)
                X_2d = reducer.fit_transform(X)
            
            # Create plot
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Color by artist
            unique_labels = list(set(labels))
            colors = plt.cm.tab20(np.linspace(0, 1, len(unique_labels)))
            label_to_color = dict(zip(unique_labels, colors))
            
            for label in unique_labels:
                mask = np.array(labels) == label
                ax.scatter(X_2d[mask, 0], X_2d[mask, 1], 
                          c=[label_to_color[label]], label=label, 
                          alpha=0.6, s=50)
            
            ax.set_xlabel(f'{method.upper()} Dimension 1', fontsize=12)
            ax.set_ylabel(f'{method.upper()} Dimension 2', fontsize=12)
            ax.set_title(f'Fingerprint Embedding Space ({method.upper()})', 
                        fontsize=14, fontweight='bold')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"Error visualizing embedding space: {e}")
            return None
    
    def create_training_summary(self, training_data: List[Dict]) -> Dict:
        """
        Create summary visualizations for training data
        
        Args:
            training_data: List of fingerprint dicts from training
            
        Returns:
            Dict with base64 images for various visualizations
        """
        if not training_data:
            return {}
        
        visualizations = {}
        
        # 1. Fingerprints per artist (bar chart)
        artist_counts = {}
        for item in training_data:
            artist = item.get('artist', 'Unknown')
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
        
        fig, ax = plt.subplots(figsize=(10, 6))
        artists = list(artist_counts.keys())
        counts = list(artist_counts.values())
        ax.barh(artists, counts, color='purple', alpha=0.7)
        ax.set_xlabel('Number of Fingerprints', fontsize=12)
        ax.set_title('Fingerprints per Artist', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        visualizations['artist_counts'] = f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"
        plt.close(fig)
        
        # 2. Source breakdown (pie chart)
        source_counts = {}
        for item in training_data:
            source = item.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(source_counts.values(), labels=source_counts.keys(), autopct='%1.1f%%',
               startangle=90, colors=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax.set_title('Training Data Sources', fontsize=14, fontweight='bold')
        
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        visualizations['source_breakdown'] = f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"
        plt.close(fig)
        
        # 3. Sample fingerprint vector
        if training_data:
            sample_fp = np.array(training_data[0]['fingerprint'])
            visualizations['sample_fingerprint'] = self.visualize_embedding_vector(
                sample_fp, 
                title=f'Sample Fingerprint: {training_data[0].get("track_name", "Unknown")}'
            )
        
        # 4. Embedding space (if enough data)
        if len(training_data) >= 10:
            fingerprints = [np.array(item['fingerprint']) for item in training_data]
            labels = [item.get('artist', 'Unknown') for item in training_data]
            visualizations['embedding_space'] = self.visualize_embedding_space(
                fingerprints, labels
            )
        
        return visualizations


def visualize_training_file(filename: str = "final_training_data.json"):
    """
    Quick function to visualize a training data file
    
    Args:
        filename: Name of training data JSON file
    """
    import os
    import sys
    
    data_path = Path("data/training_fingerprints") / filename
    
    if not data_path.exists():
        print(f"File not found: {data_path}")
        return
    
    with open(data_path, 'r') as f:
        training_data = json.load(f)
    
    visualizer = FingerprintVisualizer()
    visualizations = visualizer.create_training_summary(training_data)
    
    print(f"✅ Generated {len(visualizations)} visualizations")
    print(f"   - Artist counts chart")
    print(f"   - Source breakdown pie chart")
    print(f"   - Sample fingerprint vector")
    if 'embedding_space' in visualizations:
        print(f"   - Embedding space (t-SNE)")
    
    return visualizations


if __name__ == "__main__":
    visualize_training_file()
