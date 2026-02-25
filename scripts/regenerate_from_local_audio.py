#!/usr/bin/env python3
"""
Regenerate fingerprints from local audio files using NEW comprehensive method
This will use any audio files found in the project to generate comprehensive fingerprints
"""

import sys
import os
from pathlib import Path
import glob

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.fingerprint_service import FingerprintService

def find_audio_files():
    """Find all audio files in the project"""
    audio_extensions = ['*.mp3', '*.wav', '*.m4a', '*.flac', '*.ogg']
    audio_files = []
    
    # Search in common locations
    search_paths = [
        project_root / "ref docs" / "tstt tracks",
        project_root / "test_audio",
        project_root / "ml" / "data" / "audio",
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            for ext in audio_extensions:
                audio_files.extend(search_path.glob(ext))
                audio_files.extend(search_path.glob(ext.upper()))
    
    # Also search recursively in ref docs
    ref_docs = project_root / "ref docs"
    if ref_docs.exists():
        for ext in audio_extensions:
            audio_files.extend(ref_docs.rglob(ext))
            audio_files.extend(ref_docs.rglob(ext.upper()))
    
    return list(set(audio_files))  # Remove duplicates

def clear_and_regenerate():
    """Clear old index and regenerate from local audio files"""
    print("=" * 70)
    print("🔄 REGENERATING FINGERPRINTS FROM LOCAL AUDIO")
    print("   Using NEW comprehensive method (300+ features → 128-dim)")
    print("=" * 70)
    print()
    
    # Find audio files
    print("🔍 Searching for audio files...")
    audio_files = find_audio_files()
    
    if not audio_files:
        print("❌ No audio files found!")
        print("   Searched in:")
        print("     - ref docs/tstt tracks/")
        print("     - test_audio/")
        print("     - ml/data/audio/")
        return False
    
    print(f"✅ Found {len(audio_files)} audio files")
    print()
    
    # Clear old index
    print("🗑️  Clearing old fingerprint index...")
    index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
    metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
    
    if index_path.exists():
        index_path.unlink()
        print(f"   ✅ Deleted: {index_path}")
    
    if metadata_path.exists():
        metadata_path.unlink()
        print(f"   ✅ Deleted: {metadata_path}")
    
    print()
    
    # Initialize fingerprint service (will use comprehensive method)
    fingerprint_service = FingerprintService(
        index_path=str(index_path),
        metadata_path=str(metadata_path)
    )
    
    print("🔄 Generating comprehensive fingerprints...")
    print()
    
    added = 0
    failed = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        try:
            # Extract artist and title from filename
            filename = audio_file.stem
            # Try to parse "Artist - Title" or "Title - Prod by Artist" format
            if " - " in filename:
                parts = filename.split(" - ", 1)
                if "Prod" in parts[1] or "prod" in parts[1]:
                    artist = parts[1].replace("Prod by ", "").replace("Prod. by ", "").strip()
                    title = parts[0].strip()
                else:
                    artist = parts[0].strip()
                    title = parts[1].strip()
            else:
                artist = "Unknown"
                title = filename
            
            print(f"[{i}/{len(audio_files)}] Processing: {audio_file.name}")
            
            # Generate comprehensive fingerprint and add to database
            fingerprint_id = fingerprint_service.add_fingerprint(
                audio_path=str(audio_file),
                artist=artist,
                title=title,
                uploader_id="comprehensive_regeneration"
            )
            
            added += 1
            print(f"   ✅ Added fingerprint {fingerprint_id} for {artist} - {title}")
            
            # Save periodically
            if i % 10 == 0:
                fingerprint_service._save_index()
                print(f"   💾 Saved progress ({added} total so far)")
        
        except Exception as e:
            failed += 1
            print(f"   ❌ Error processing {audio_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final save
    fingerprint_service._save_index()
    
    print()
    print("=" * 70)
    print("✅ REGENERATION COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Results:")
    print(f"   ✅ Added: {added} comprehensive fingerprints")
    print(f"   ❌ Failed: {failed} files")
    
    # Get final stats
    stats = fingerprint_service.get_stats()
    print(f"\n📈 Database Statistics:")
    print(f"   Total fingerprints: {stats['total_fingerprints']}")
    print(f"   Unique artists: {stats['artists']}")
    print(f"   Artists: {', '.join(stats['artist_list'][:10])}{'...' if len(stats['artist_list']) > 10 else ''}")
    
    print(f"\n📝 Next steps:")
    print("   1. Restart backend: pkill -f uvicorn && cd backend && python -m uvicorn main:app --port 8000")
    print("   2. Test with: curl http://localhost:8000/api/fingerprint/stats")
    print("   3. All new uploads will automatically use comprehensive method")
    
    return True

if __name__ == "__main__":
    success = clear_and_regenerate()
    sys.exit(0 if success else 1)
