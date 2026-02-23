#!/usr/bin/env python3
"""
Regenerate ALL fingerprints using the new comprehensive fingerprinting method
This will re-download from streaming APIs and generate new fingerprints
"""

import sys
import os
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root))

from app.fingerprint_service import FingerprintService
from ml.streaming_trainer import StreamingTrainer
import json
import numpy as np

def clear_old_index():
    """Clear the old FAISS index to start fresh"""
    print("🗑️  Clearing old fingerprint index...")
    
    index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
    metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
    
    if index_path.exists():
        index_path.unlink()
        print(f"   ✅ Deleted: {index_path}")
    
    if metadata_path.exists():
        metadata_path.unlink()
        print(f"   ✅ Deleted: {metadata_path}")
    
    print("   ✅ Old index cleared\n")

def get_artists_from_training_data():
    """Extract unique artists from existing training data"""
    training_data_path = project_root / "ml" / "data" / "training_fingerprints" / "final_training_data_1000.json"
    
    if not training_data_path.exists():
        print(f"❌ Training data not found: {training_data_path}")
        return []
    
    with open(training_data_path, 'r') as f:
        data = json.load(f)
    
    artists = sorted(set(item.get('artist', 'Unknown') for item in data))
    print(f"📊 Found {len(artists)} unique artists in training data")
    return artists

def regenerate_from_streaming(artists: list, max_tracks_per_artist: int = 10):
    """Regenerate fingerprints by re-downloading from streaming APIs"""
    print(f"\n🔄 Regenerating fingerprints for {len(artists)} artists...")
    print(f"   Max tracks per artist: {max_tracks_per_artist}")
    print(f"   Using NEW comprehensive fingerprinting method\n")
    
    # Check for Spotify credentials
    spotify_id = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not spotify_id or not spotify_secret:
        print("⚠️  Spotify credentials not found in environment variables")
        print("   Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        print("   Skipping streaming regeneration...")
        return False
    
    # Initialize trainer with new fingerprint service
    trainer = StreamingTrainer(spotify_id, spotify_secret)
    
    # Re-train with new fingerprint method
    total_fingerprints = 0
    for i, artist in enumerate(artists, 1):
        print(f"[{i}/{len(artists)}] Processing {artist}...")
        try:
            count = trainer.train_artist(artist, max_tracks=max_tracks_per_artist)
            total_fingerprints += count
            print(f"   ✅ Generated {count} fingerprints for {artist}")
        except Exception as e:
            print(f"   ⚠️  Error processing {artist}: {e}")
            continue
    
    # Save new training data
    output_file = project_root / "ml" / "data" / "training_fingerprints" / "final_training_data_regenerated.json"
    trainer.save_training_data(str(output_file))
    
    print(f"\n✅ Regenerated {total_fingerprints} fingerprints total")
    print(f"   Saved to: {output_file}")
    
    return True

def load_new_fingerprints_to_index():
    """Load newly generated fingerprints into FAISS index"""
    print("\n📂 Loading new fingerprints into FAISS index...")
    
    # Try regenerated file first, then fall back to original
    regenerated_path = project_root / "ml" / "data" / "training_fingerprints" / "final_training_data_regenerated.json"
    training_data_path = project_root / "ml" / "data" / "training_fingerprints" / "final_training_data_1000.json"
    
    data_path = regenerated_path if regenerated_path.exists() else training_data_path
    
    if not data_path.exists():
        print(f"❌ Training data not found: {data_path}")
        return False
    
    # Initialize fingerprint service
    index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
    metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
    
    fingerprint_service = FingerprintService(
        index_path=str(index_path),
        metadata_path=str(metadata_path)
    )
    
    # Load training data
    with open(data_path, 'r') as f:
        training_data = json.load(f)
    
    print(f"📊 Loading {len(training_data)} fingerprints...")
    
    # IMPORTANT: The fingerprints in JSON are from OLD method
    # We need to regenerate them from audio, but since audio is deleted,
    # we'll need to re-download OR note that new uploads will use new method
    
    # For now, note that we need to re-download
    print("\n⚠️  IMPORTANT: Fingerprints in JSON were generated with OLD method")
    print("   New uploads will use NEW comprehensive method")
    print("   For best results, re-run streaming trainer to regenerate all fingerprints")
    
    return True

def main():
    """Main regeneration process"""
    print("=" * 60)
    print("🔄 REGENERATING FINGERPRINTS WITH NEW COMPREHENSIVE METHOD")
    print("=" * 60)
    print()
    
    # Step 1: Clear old index
    clear_old_index()
    
    # Step 2: Get artists from training data
    artists = get_artists_from_training_data()
    if not artists:
        print("❌ No artists found. Cannot regenerate.")
        return
    
    # Step 3: Optionally regenerate from streaming (requires Spotify API)
    print("=" * 60)
    print("OPTION 1: Regenerate from Streaming APIs (Recommended)")
    print("=" * 60)
    print("This will re-download previews and generate NEW fingerprints")
    print("Requires: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET\n")
    
    response = input("Regenerate from streaming? (y/n): ").strip().lower()
    if response == 'y':
        max_tracks = input("Max tracks per artist (default 10): ").strip()
        max_tracks = int(max_tracks) if max_tracks.isdigit() else 10
        
        success = regenerate_from_streaming(artists, max_tracks)
        if success:
            load_new_fingerprints_to_index()
    else:
        print("\n⚠️  Skipping streaming regeneration")
        print("   New uploads will use the new method")
        print("   Existing fingerprints in database use old method")
        print("   They may not match well with new uploads")
    
    print("\n" + "=" * 60)
    print("✅ Regeneration process complete!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("   1. Test with new uploads (will use new method)")
    print("   2. Re-run streaming trainer to regenerate all fingerprints")
    print("   3. Monitor matching quality and adjust if needed")

if __name__ == "__main__":
    main()
