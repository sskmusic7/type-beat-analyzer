"""
Training service for fingerprint generation
Runs training in background thread with progress tracking
"""

import sys
import os
import json
import threading
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class TrainingService:
    """
    Manages fingerprint training in background thread
    """
    
    def __init__(self):
        self.training_thread: Optional[threading.Thread] = None
        self.is_training = False
        self.training_status: Dict = {
            "status": "idle",  # idle, running, completed, failed
            "progress": 0,
            "current_artist": None,
            "artists_processed": 0,
            "total_artists": 0,
            "fingerprints_generated": 0,
            "started_at": None,
            "completed_at": None,
            "error": None,
            "logs": []
        }
        self._lock = threading.Lock()
    
    def _log(self, message: str):
        """Add log message to training status"""
        with self._lock:
            timestamp = datetime.now().isoformat()
            self.training_status["logs"].append(f"[{timestamp}] {message}")
            # Keep only last 100 logs
            if len(self.training_status["logs"]) > 100:
                self.training_status["logs"] = self.training_status["logs"][-100:]
        logger.info(f"[Training] {message}")
    
    def _get_artists_from_training_data(self) -> list:
        """Extract unique artists from existing training data"""
        project_root = Path(__file__).parent.parent.parent
        training_data_path = project_root / "ml" / "data" / "training_fingerprints" / "final_training_data_1000.json"
        
        if not training_data_path.exists():
            self._log(f"❌ Training data not found: {training_data_path}")
            return []
        
        try:
            with open(training_data_path, 'r') as f:
                data = json.load(f)
            
            artists = sorted(set(item.get('artist', 'Unknown') for item in data))
            self._log(f"📊 Found {len(artists)} unique artists in training data")
            return artists
        except Exception as e:
            self._log(f"❌ Error reading training data: {e}")
            return []
    
    def _clear_old_index(self):
        """Clear the old FAISS index to start fresh"""
        self._log("🗑️  Clearing old fingerprint index...")
        
        project_root = Path(__file__).parent.parent.parent
        index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
        metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
        
        try:
            if index_path.exists():
                index_path.unlink()
                self._log(f"   ✅ Deleted: {index_path.name}")
            
            if metadata_path.exists():
                metadata_path.unlink()
                self._log(f"   ✅ Deleted: {metadata_path.name}")
            
            self._log("   ✅ Old index cleared")
        except Exception as e:
            self._log(f"   ⚠️  Error clearing index: {e}")
    
    def _run_training(
        self,
        clear_existing: bool = True,
        max_per_artist: int = 5,
        artists: Optional[list] = None
    ):
        """Run the training process in background thread

        clear_existing:
            - True  -> wipe existing index first (full regeneration)
            - False -> append new fingerprints to whatever is already there

        artists:
            - None or [] -> load artists from training data file
            - list       -> train ONLY on the provided artists
        """
        try:
            with self._lock:
                self.is_training = True
                self.training_status = {
                    "status": "running",
                    "progress": 0,
                    "current_artist": None,
                    "artists_processed": 0,
                    "total_artists": 0,
                    "fingerprints_generated": 0,
                    "started_at": datetime.now().isoformat(),
                    "completed_at": None,
                    "error": None,
                    "logs": []
                }
            
            self._log("=" * 70)
            self._log("🔄 STARTING FINGERPRINT TRAINING")
            self._log("   Using comprehensive method (300+ features → 128-dim)")
            self._log("=" * 70)
            
            # Add paths for imports
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root / "ml"))
            sys.path.insert(0, str(project_root / "backend"))
            
            # Import here to avoid issues if not available
            from hybrid_trainer import HybridTrainer
            from app.fingerprint_service import FingerprintService
            
            # Step 1: Clear old index if requested
            if clear_existing:
                self._clear_old_index()
            
            # Step 2: Get artists
            if artists and len(artists) > 0:
                # Use explicit list provided by caller (e.g. admin batch)
                artists_list = sorted({a.strip() for a in artists if a and a.strip()})
                self._log(f"📥 Received explicit artist batch from API: {len(artists_list)} artists")
            else:
                # Fallback to training data file (legacy full regeneration mode)
                artists_list = self._get_artists_from_training_data()
                if not artists_list:
                    raise Exception("No artists found in training data")
            
            with self._lock:
                self.training_status["total_artists"] = len(artists_list)
            
            self._log(f"\n🔄 Training fingerprints for {len(artists_list)} artists...")
            self._log(f"   Max tracks per artist: {max_per_artist}")
            self._log(f"   Audio files will be deleted immediately after fingerprinting\n")
            
            # Initialize trainer and fingerprint service
            trainer = HybridTrainer()  # Uses YouTube only
            
            index_path = project_root / "backend" / "data" / "models" / "fingerprint_index.faiss"
            metadata_path = project_root / "backend" / "data" / "models" / "fingerprint_metadata.json"
            
            fingerprint_service = FingerprintService(
                index_path=str(index_path),
                metadata_path=str(metadata_path)
            )
            
            total_fingerprints = 0
            
            # Process each artist
            for i, artist in enumerate(artists_list, 1):
                if not self.is_training:  # Check if stopped
                    self._log("Training stopped by user")
                    break
                
                with self._lock:
                    self.training_status["current_artist"] = artist
                    self.training_status["artists_processed"] = i - 1
                    self.training_status["progress"] = int((i - 1) / len(artists_list) * 100)
                
                self._log(f"\n[{i}/{len(artists)}] Processing {artist}...")
                self._log("=" * 60)
                
                try:
                    # Download from YouTube and generate fingerprints
                    count = trainer.train_artist_hybrid(artist, max_items=max_per_artist)
                    
                    # Get fingerprints for this artist
                    artist_fingerprints = [
                        item for item in trainer.training_data 
                        if item.get('artist') == artist and item.get('source') == 'youtube_download'
                    ]
                    
                    before_count = total_fingerprints
                    
                    # Add fingerprints to database
                    for item in artist_fingerprints:
                        try:
                            fingerprint = item['fingerprint']
                            if isinstance(fingerprint, list):
                                embedding = np.array(fingerprint, dtype=np.float32)
                            else:
                                embedding = np.array(fingerprint, dtype=np.float32)
                            
                            if len(embedding) != 128:
                                self._log(f"   ⚠️  Skipping fingerprint with wrong dimension: {len(embedding)}")
                                continue
                            
                            embedding = embedding.reshape(1, -1)
                            fingerprint_service.index.add(embedding)
                            
                            fingerprint_id = fingerprint_service.id_counter
                            fingerprint_service.id_counter += 1
                            
                            metadata_entry = {
                                'id': fingerprint_id,
                                'artist': artist,
                                'title': item.get('track_name', 'Unknown'),
                                'audio_hash': f"youtube_{artist}_{fingerprint_id}",
                                'upload_date': None,
                                'uploader_id': 'comprehensive_youtube_training'
                            }
                            fingerprint_service.metadata.append(metadata_entry)
                            total_fingerprints += 1
                        except Exception as e:
                            self._log(f"   ⚠️  Error adding fingerprint: {e}")
                            continue
                    
                    added_this_artist = total_fingerprints - before_count
                    self._log(f"   ✅ Added {added_this_artist} fingerprints for {artist}")
                    
                    # Save periodically
                    if i % 5 == 0:
                        fingerprint_service._save_index()
                        self._log(f"   💾 Saved progress ({total_fingerprints} total so far)")
                
                except Exception as e:
                    self._log(f"   ❌ Error processing {artist}: {e}")
                    continue
            
            # Final save
            fingerprint_service._save_index()
            
            with self._lock:
                self.training_status["status"] = "completed"
                self.training_status["progress"] = 100
                self.training_status["artists_processed"] = len(artists_list)
                self.training_status["fingerprints_generated"] = total_fingerprints
                self.training_status["completed_at"] = datetime.now().isoformat()
                self.training_status["current_artist"] = None
            
            self._log(f"\n✅ Training complete!")
            self._log(f"   Total fingerprints: {total_fingerprints}")
            self._log(f"   Artists processed: {len(artists_list)}")
            
        except Exception as e:
            error_msg = str(e)
            with self._lock:
                self.training_status["status"] = "failed"
                self.training_status["error"] = error_msg
                self.training_status["completed_at"] = datetime.now().isoformat()
            
            self._log(f"\n❌ Training failed: {error_msg}")
            logger.exception("Training failed")
        
        finally:
            with self._lock:
                self.is_training = False
                self.training_status["current_artist"] = None
    
    def start_training(
        self,
        clear_existing: bool = True,
        max_per_artist: int = 5,
        artists: Optional[list] = None
    ) -> bool:
        """Start training in background thread.

        Used by API:
          - clear_existing=True, artists=None  -> full regenerate (danger)
          - clear_existing=False, artists=list -> append new artists (recommended)
        """
        if self.is_training:
            return False
        
        self.training_thread = threading.Thread(
            target=self._run_training,
            args=(clear_existing, max_per_artist, artists),
            daemon=True
        )
        self.training_thread.start()
        return True
    
    def stop_training(self):
        """Stop training (sets flag, thread will check and exit)"""
        with self._lock:
            self.is_training = False
            self.training_status["status"] = "stopping"
        self._log("Stopping training...")
    
    def get_status(self) -> Dict:
        """Get current training status"""
        with self._lock:
            return self.training_status.copy()
    
    def is_running(self) -> bool:
        """Check if training is currently running"""
        return self.is_training
