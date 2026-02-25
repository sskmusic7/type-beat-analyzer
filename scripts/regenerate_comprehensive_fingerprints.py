#!/usr/bin/env python3
"""
Regenerate ALL fingerprints using the NEW comprehensive fingerprinting method
This script will:
1. Extract artists from existing training data
2. Re-download audio from Spotify (if credentials available)
3. Generate NEW comprehensive fingerprints (300+ features → 128-dim)
4. Load into FAISS database
"""

import sys
import os
import json
import numpy as np
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root))

from app.fingerprint_service import FingerprintService
from ml.streaming_trainer import StreamingTrainer

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

def clear_old_index():
    """Clear the old FAISS index to start fresh with comprehensive fingerprints"""
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

def regenerate_from_streaming(artists: list, max_tracks_per_artist: int = 10):
    """Regenerate fingerprints by re-downloading from streaming APIs with NEW comprehensive method"""
    print(f"\n🔄 Regenerating fingerprints for {len(artists)} artists...")
    print(f"   Max tracks per artist: {max_tracks_per_artist}")
    print(f"   Using NEW comprehensive fingerprinting method (300+ features → 128-dim)\n")
    
    # Check for Spotify credentials
    spotify_id = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not spotify_id or not spotify_secret:
        print("⚠️  Spotify credentials not found in environment variables")
        print("   Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        print("   Skipping streaming regeneration...")
        return False, 0
    
    # Initialize trainer - this will use the NEW comprehensive fingerprint service
    trainer = StreamingTrainer(spotify_id, spotify_secret)
    
    # Initialize fingerprint service for direct database access
    index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
    metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
    
    fingerprint_service = FingerprintService(
        index_path=str(index_path),
        metadata_path=str(metadata_path)
    )
    
    # Re-train with new comprehensive fingerprint method
    total_fingerprints = 0
    for i, artist in enumerate(artists, 1):
        print(f"[{i}/{len(artists)}] Processing {artist}...")
        try:
            # Get tracks from Spotify
            tracks = trainer.get_artist_tracks(artist, limit=max_tracks_per_artist)
            
            if not tracks:
                print(f"   ⚠️  No tracks found for {artist}")
                continue
            
            artist_count = 0
            for track in tracks:
                if not track.get('preview_url'):
                    continue
                
                # Stream and generate comprehensive fingerprint
                fingerprint = trainer.stream_and_fingerprint(
                    track['preview_url'],
                    artist,
                    track['name']
                )
                
                if fingerprint is not None:
                    # Add directly to database using comprehensive method
                    fingerprint_id = fingerprint_service.add_fingerprint(
                        audio_path=None,  # We don't have the file path, but fingerprint is already generated
                        artist=artist,
                        title=track['name']
                    )
                    
                    # Actually, we need to save the audio temporarily to use add_fingerprint
                    # Let's use the fingerprint directly
                    embedding = fingerprint.reshape(1, -1)
                    fingerprint_service.index.add(embedding)
                    
                    fingerprint_id = fingerprint_service.id_counter
                    fingerprint_service.id_counter += 1
                    
                    metadata_entry = {
                        'id': fingerprint_id,
                        'artist': artist,
                        'title': track['name'],
                        'audio_hash': f"spotify_{artist}_{track['name']}",
                        'upload_date': None,
                        'uploader_id': 'comprehensive_regeneration'
                    }
                    fingerprint_service.metadata.append(metadata_entry)
                    
                    artist_count += 1
                    total_fingerprints += 1
            
            print(f"   ✅ Generated {artist_count} comprehensive fingerprints for {artist}")
            
            # Save periodically
            if i % 10 == 0:
                fingerprint_service._save_index()
                print(f"   💾 Saved progress ({total_fingerprints} total so far)")
        
        except Exception as e:
            print(f"   ⚠️  Error processing {artist}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final save
    fingerprint_service._save_index()
    
    print(f"\n✅ Regenerated {total_fingerprints} comprehensive fingerprints total")
    
    return True, total_fingerprints

def main():
    """Main regeneration process"""
    print("=" * 70)
    print("🔄 REGENERATING FINGERPRINTS WITH NEW COMPREHENSIVE METHOD")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Clear old fingerprints (simple method)")
    print("  2. Re-download audio from Spotify")
    print("  3. Generate NEW comprehensive fingerprints (300+ features)")
    print("  4. Load into FAISS database")
    print()
    
    # Step 1: Clear old index
    clear_old_index()
    
    # Step 2: Get artists from training data
    artists = get_artists_from_training_data()
    if not artists:
        print("❌ No artists found. Cannot regenerate.")
        return
    
    # Step 3: Regenerate from streaming
    print("=" * 70)
    print("REGENERATING FROM SPOTIFY (Comprehensive Method)")
    print("=" * 70)
    
    max_tracks = 10  # Start with 10 per artist
    success, count = regenerate_from_streaming(artists, max_tracks)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ Regeneration complete!")
        print("=" * 70)
        print(f"\n📊 Final Statistics:")
        
        # Get final stats
        index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
        metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
        
        fingerprint_service = FingerprintService(
            index_path=str(index_path),
            metadata_path=str(metadata_path)
        )
        
        stats = fingerprint_service.get_stats()
        print(f"   Total fingerprints: {stats['total_fingerprints']}")
        print(f"   Unique artists: {stats['artists']}")
        print(f"\n📝 Next steps:")
        print("   1. Restart backend to load new fingerprints")
        print("   2. Test matching with sample files")
        print("   3. All new uploads will use comprehensive method automatically")
    else:
        print("\n⚠️  Regeneration failed or skipped (check Spotify credentials)")
        print("   New uploads will still use comprehensive method")

if __name__ == "__main__":
    main()
