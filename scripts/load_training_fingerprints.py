#!/usr/bin/env python3
"""
Load the 697 training fingerprints from JSON into the backend FAISS index
"""

import sys
import os
import json
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.fingerprint_service import FingerprintService

def load_training_fingerprints():
    """Load fingerprints from training data JSON into FAISS index"""
    
    # Paths
    project_root = Path(__file__).parent.parent
    training_data_path = project_root / "ml" / "data" / "training_fingerprints" / "final_training_data_1000.json"
    
    if not training_data_path.exists():
        print(f"❌ Training data not found: {training_data_path}")
        return False
    
    print(f"📂 Loading training data from: {training_data_path}")
    
    # Load JSON
    with open(training_data_path, 'r') as f:
        training_data = json.load(f)
    
    print(f"✅ Loaded {len(training_data)} fingerprints from JSON")
    
    # Initialize fingerprint service (will create data/models directory)
    index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
    metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
    
    fingerprint_service = FingerprintService(
        index_path=str(index_path),
        metadata_path=str(metadata_path)
    )
    
    print(f"📊 Current index size: {fingerprint_service.index.ntotal}")
    
    if fingerprint_service.index.ntotal > 0:
        print(f"⚠️  Index already has {fingerprint_service.index.ntotal} fingerprints")
        response = input("Continue and add more? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return False
    
    # Add each fingerprint
    added = 0
    skipped = 0
    
    print(f"\n🔄 Adding fingerprints to FAISS index...")
    
    for i, item in enumerate(training_data):
        try:
            fingerprint = np.array(item['fingerprint'], dtype=np.float32)
            artist = item.get('artist', 'Unknown')
            title = item.get('track_name', item.get('title', f'Track {i+1}'))
            
            # Check if fingerprint dimension matches
            if len(fingerprint) != fingerprint_service.embedding_dim:
                print(f"⚠️  Skipping item {i}: wrong dimension ({len(fingerprint)} != {fingerprint_service.embedding_dim})")
                skipped += 1
                continue
            
            # Add to index
            embedding = fingerprint.reshape(1, -1)
            fingerprint_service.index.add(embedding)
            
            # Add metadata
            fingerprint_id = fingerprint_service.id_counter
            fingerprint_service.id_counter += 1
            
            metadata_entry = {
                'id': fingerprint_id,
                'artist': artist,
                'title': title,
                'audio_hash': f"training_{i}",  # Placeholder hash
                'upload_date': None,
                'uploader_id': 'training_data'
            }
            fingerprint_service.metadata.append(metadata_entry)
            
            added += 1
            
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(training_data)}... ({added} added, {skipped} skipped)")
        
        except Exception as e:
            print(f"⚠️  Error processing item {i}: {e}")
            skipped += 1
    
    # Save index
    print(f"\n💾 Saving index to {index_path}...")
    fingerprint_service._save_index()
    
    print(f"\n✅ Complete!")
    print(f"   Added: {added} fingerprints")
    print(f"   Skipped: {skipped} fingerprints")
    print(f"   Total in index: {fingerprint_service.index.ntotal}")
    
    # Count unique artists
    artists = set(item['artist'] for item in fingerprint_service.metadata)
    print(f"   Artists: {len(artists)}")
    
    return True

if __name__ == "__main__":
    success = load_training_fingerprints()
    sys.exit(0 if success else 1)
