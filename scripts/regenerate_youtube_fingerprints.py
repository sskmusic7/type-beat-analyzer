#!/usr/bin/env python3
"""
Regenerate ALL fingerprints from YouTube using NEW comprehensive method
This will:
1. Extract artists from existing training data
2. Re-download from YouTube (same as before)
3. Generate NEW comprehensive fingerprints (300+ features → 128-dim)
4. Delete audio immediately (legal compliance)
5. Load into FAISS database
"""

import sys
import os
import json
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "ml"))
sys.path.insert(0, str(project_root / "backend"))

from hybrid_trainer import HybridTrainer
from app.fingerprint_service import FingerprintService

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

def regenerate_from_youtube(artists: list, max_per_artist: int = 10):
    """Regenerate fingerprints by re-downloading from YouTube with NEW comprehensive method"""
    print(f"\n🔄 Regenerating fingerprints for {len(artists)} artists from YouTube...")
    print(f"   Max tracks per artist: {max_per_artist}")
    print(f"   Using NEW comprehensive fingerprinting method (300+ features → 128-dim)")
    print(f"   Audio files will be deleted immediately after fingerprinting\n")
    
    # Initialize hybrid trainer (YouTube-based, no Spotify needed)
    trainer = HybridTrainer()  # No Spotify credentials needed - uses YouTube only
    
    # Initialize fingerprint service for direct database access
    index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
    metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
    
    fingerprint_service = FingerprintService(
        index_path=str(index_path),
        metadata_path=str(metadata_path)
    )
    
    total_fingerprints = 0
    
    for i, artist in enumerate(artists, 1):
        print(f"\n[{i}/{len(artists)}] Processing {artist}...")
        print("=" * 60)
        
        try:
            # Download from YouTube and generate comprehensive fingerprints
            # This will automatically delete audio files after fingerprinting
            count = trainer.train_artist_hybrid(artist, max_items=max_per_artist)
            
            # Add fingerprints to database
            artist_fingerprints = [
                item for item in trainer.training_data 
                if item.get('artist') == artist and item.get('source') == 'youtube_download'
            ]
            
            for item in artist_fingerprints:
                # The fingerprint is already generated with comprehensive method
                # We need to add it to the FAISS index
                fingerprint = item['fingerprint']
                embedding = fingerprint if isinstance(fingerprint, list) else fingerprint.tolist()
                embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)
                
                fingerprint_service.index.add(embedding)
                
                fingerprint_id = fingerprint_service.id_counter
                fingerprint_service.id_counter += 1
                
                metadata_entry = {
                    'id': fingerprint_id,
                    'artist': artist,
                    'title': item.get('track_name', 'Unknown'),
                    'audio_hash': f"youtube_{artist}_{item.get('track_name', 'unknown')}",
                    'upload_date': None,
                    'uploader_id': 'comprehensive_youtube_regeneration'
                }
                fingerprint_service.metadata.append(metadata_entry)
            
            total_fingerprints += len(artist_fingerprints)
            print(f"   ✅ Generated {len(artist_fingerprints)} comprehensive fingerprints for {artist}")
            
            # Save periodically
            if i % 5 == 0:
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
    print("🔄 REGENERATING FINGERPRINTS FROM YOUTUBE")
    print("   Using NEW comprehensive method (300+ features → 128-dim)")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Clear old fingerprints (simple method)")
    print("  2. Re-download from YouTube (same as original training)")
    print("  3. Generate NEW comprehensive fingerprints")
    print("  4. Delete audio files immediately (legal compliance)")
    print("  5. Load into FAISS database")
    print()
    
    # Step 1: Clear old index
    clear_old_index()
    
    # Step 2: Get artists from training data
    artists = get_artists_from_training_data()
    if not artists:
        print("❌ No artists found. Cannot regenerate.")
        return
    
    # Step 3: Regenerate from YouTube
    print("=" * 70)
    print("REGENERATING FROM YOUTUBE (Comprehensive Method)")
    print("=" * 70)
    
    max_per_artist = 10  # Start with 10 per artist (can increase later)
    success, count = regenerate_from_youtube(artists, max_per_artist)
    
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
        print("   2. Check admin dashboard: /admin")
        print("   3. All new uploads will use comprehensive method automatically")

if __name__ == "__main__":
    import numpy as np
    main()
