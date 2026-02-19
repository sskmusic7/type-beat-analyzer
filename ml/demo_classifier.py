"""
🎵 Type Beat Classifier Demo
Upload a song and see which artists it sounds like!

Usage:
    python demo_classifier.py <audio_file.mp3>
    
Or run interactively:
    python demo_classifier.py
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
import argparse
from typing import List, Dict, Tuple

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.fingerprint_service import FingerprintService

def load_trained_fingerprints(data_path: str) -> Dict:
    """Load trained fingerprints from JSON file"""
    with open(data_path, 'r') as f:
        return json.load(f)

def classify_audio(audio_file: str, training_data_path: str = None) -> List[Tuple[str, float]]:
    """
    Classify an audio file by comparing against trained fingerprints
    
    Args:
        audio_file: Path to audio file to classify
        training_data_path: Path to training fingerprints JSON
        
    Returns:
        List of (artist, similarity_score) tuples, sorted by similarity
    """
    # Load training data
    if training_data_path is None:
        training_data_path = "data/training_fingerprints/final_training_data_1000.json"
    
    if not Path(training_data_path).exists():
        print(f"❌ Training data not found at {training_data_path}")
        print("   Please run training first!")
        return []
    
    print(f"📚 Loading trained fingerprints from {training_data_path}...")
    training_data = load_trained_fingerprints(training_data_path)
    print(f"   ✅ Loaded {len(training_data)} fingerprints from {len(set(d.get('artist') for d in training_data))} artists")
    
    # Initialize fingerprint service
    fingerprint_service = FingerprintService()
    
    # Generate fingerprint for input audio
    print(f"\n🎵 Analyzing: {audio_file}")
    try:
        query_fingerprint = fingerprint_service._generate_fingerprint(audio_file)
    except Exception as e:
        print(f"❌ Error generating fingerprint: {e}")
        return []
    
    # Compare against all training fingerprints
    print(f"🔍 Comparing against {len(training_data)} trained fingerprints...")
    
    similarities = []
    for item in training_data:
        artist = item.get('artist', 'Unknown')
        trained_fp = np.array(item.get('fingerprint', []))
        
        if len(trained_fp) == len(query_fingerprint):
            # Compute cosine similarity
            dot_product = np.dot(query_fingerprint, trained_fp)
            norm_query = np.linalg.norm(query_fingerprint)
            norm_trained = np.linalg.norm(trained_fp)
            
            if norm_query > 0 and norm_trained > 0:
                similarity = dot_product / (norm_query * norm_trained)
                similarities.append((artist, similarity, item.get('title', 'Unknown')))
    
    # Aggregate by artist (average similarity)
    artist_scores = {}
    artist_counts = {}
    
    for artist, similarity, title in similarities:
        if artist not in artist_scores:
            artist_scores[artist] = 0.0
            artist_counts[artist] = 0
        
        artist_scores[artist] += similarity
        artist_counts[artist] += 1
    
    # Average similarity per artist
    results = []
    for artist in artist_scores:
        avg_similarity = artist_scores[artist] / artist_counts[artist]
        results.append((artist, avg_similarity, artist_counts[artist]))
    
    # Sort by similarity (descending)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Type Beat Classifier Demo')
    parser.add_argument('audio_file', nargs='?', help='Path to audio file to classify')
    parser.add_argument('--training-data', default='data/training_fingerprints/final_training_data_1000.json',
                       help='Path to training fingerprints JSON')
    parser.add_argument('--top-k', type=int, default=10, help='Number of top matches to show')
    
    args = parser.parse_args()
    
    # If no audio file provided, prompt interactively
    if not args.audio_file:
        print("🎵 Type Beat Classifier Demo")
        print("=" * 60)
        audio_file = input("\nEnter path to audio file: ").strip()
        if not audio_file:
            print("❌ No file provided")
            return
        args.audio_file = audio_file
    
    # Check if file exists
    if not Path(args.audio_file).exists():
        print(f"❌ File not found: {args.audio_file}")
        return
    
    # Classify
    results = classify_audio(args.audio_file, args.training_data)
    
    if not results:
        print("\n❌ No matches found. Make sure training data exists.")
        return
    
    # Display results
    print(f"\n{'='*60}")
    print(f"🎯 TOP {min(args.top_k, len(results))} ARTIST MATCHES")
    print(f"{'='*60}\n")
    
    for i, (artist, similarity, count) in enumerate(results[:args.top_k], 1):
        percentage = similarity * 100
        bar_length = int(percentage / 2)  # Scale to 50 chars max
        bar = "█" * bar_length + "░" * (50 - bar_length)
        
        print(f"{i:2}. {artist:<35} {percentage:5.1f}% [{bar}] ({count} fingerprints)")
    
    print(f"\n{'='*60}")
    print(f"✅ Top match: {results[0][0]} ({results[0][1]*100:.1f}% similarity)")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
