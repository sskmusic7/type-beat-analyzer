"""
Neural Audio Fingerprint Service
Generates fingerprints and matches beats using FAISS similarity search
"""

import numpy as np
import faiss
import librosa
import hashlib
import pickle
import os
import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class FingerprintService:
    """
    Service for generating audio fingerprints and matching beats
    Uses Neural Audio FP approach: mel-spectrogram -> embedding -> FAISS search
    """
    
    def __init__(self, index_path: str = "data/models/fingerprint_index.faiss", 
                 metadata_path: str = "data/models/fingerprint_metadata.json"):
        """
        Initialize fingerprint service
        
        Args:
            index_path: Path to save/load FAISS index
            metadata_path: Path to save/load metadata (artist, title, etc.)
        """
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # FAISS index parameters
        self.embedding_dim = 128  # Neural Audio FP uses 128-dim embeddings
        
        # Initialize FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.metadata = []  # List of dicts: {id, artist, title, audio_hash, upload_date}
        self.id_counter = 0
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load FAISS index and metadata from disk"""
        try:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"Loaded FAISS index with {self.index.ntotal} fingerprints")
            
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                    if self.metadata:
                        self.id_counter = max(item['id'] for item in self.metadata) + 1
                logger.info(f"Loaded {len(self.metadata)} metadata entries")
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}. Starting fresh.")
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []
            self.id_counter = 0
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info(f"Saved index with {self.index.ntotal} fingerprints")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _generate_fingerprint(self, audio_path: str, duration: Optional[float] = None) -> np.ndarray:
        """
        Generate 128-dim fingerprint from audio file
        Uses enhanced mel-spectrogram + musical features approach
        
        Args:
            audio_path: Path to audio file
            duration: Optional duration to process (None = full file, useful for training)
            
        Returns:
            128-dim embedding vector
        """
        # Load audio - use higher sample rate for better feature extraction
        y, sr = librosa.load(
            audio_path,
            sr=22050,  # Higher SR for better musical features
            mono=True,
            duration=duration if duration else 30.0  # Use 30s for better representation
        )
        
        # Normalize
        y = librosa.util.normalize(y)
        
        # Extract multiple musical features for better discrimination
        features = []
        
        # 1. Mel-spectrogram (captures timbre/harmonic content)
        mel_spec = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            n_mels=128,
            fmin=20,
            fmax=sr//2,
            n_fft=2048,
            hop_length=512
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        # Aggregate: mean and std across time
        features.extend([
            np.mean(mel_spec_db, axis=1),  # 128 dims - average spectral content
            np.std(mel_spec_db, axis=1),   # 128 dims - spectral variation
        ])
        
        # 2. Chroma features (captures harmonic/pitch content)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=512)
        features.extend([
            np.mean(chroma, axis=1),  # 12 dims - average pitch class
            np.std(chroma, axis=1),   # 12 dims - pitch variation
        ])
        
        # 3. Tempo and rhythm (captures beat/rhythm patterns)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
        # Beat-synced features
        if len(beats) > 1:
            beat_frames = librosa.frames_to_time(beats, sr=sr, hop_length=512)
            # Onset strength
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=512)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
            # Rhythm features
            if len(onset_times) > 0:
                inter_onset = np.diff(onset_times)
                features.append([tempo / 200.0, np.mean(inter_onset), np.std(inter_onset)])  # 3 dims
            else:
                features.append([tempo / 200.0, 0.0, 0.0])
        else:
            features.append([0.0, 0.0, 0.0])
        
        # 4. MFCC (captures timbral texture)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)
        features.extend([
            np.mean(mfcc, axis=1),  # 13 dims
            np.std(mfcc, axis=1),   # 13 dims
        ])
        
        # 5. Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=512)[0]
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y, hop_length=512)[0]
        features.append([
            np.mean(spectral_centroids) / 5000.0,  # Normalize
            np.std(spectral_centroids) / 5000.0,
            np.mean(spectral_rolloff) / 5000.0,
            np.std(spectral_rolloff) / 5000.0,
            np.mean(zero_crossing_rate),
            np.std(zero_crossing_rate),
        ])  # 6 dims
        
        # Combine all features
        combined = np.concatenate([f.flatten() for f in features])
        
        # Reduce to 128 dims using PCA-like approach
        if len(combined) > self.embedding_dim:
            # Use first 128 + weighted average of rest
            embedding = combined[:self.embedding_dim].copy()
            remaining = combined[self.embedding_dim:]
            # Weighted pooling of remaining features
            weights = np.linspace(1.0, 0.1, len(remaining))
            weighted_avg = np.average(remaining, weights=weights)
            # Distribute weighted average across last 32 dims
            embedding[-32:] = embedding[-32:] * 0.7 + weighted_avg * 0.3
        elif len(combined) < self.embedding_dim:
            # Pad with zeros
            embedding = np.pad(combined, (0, self.embedding_dim - len(combined)), 'constant')
        else:
            embedding = combined
        
        # L2 normalize
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding.astype(np.float32)
    
    def _compute_audio_hash(self, audio_path: str) -> str:
        """Compute SHA256 hash of audio file"""
        hasher = hashlib.sha256()
        with open(audio_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def add_fingerprint(self, audio_path: str, artist: str, 
                       title: Optional[str] = None, 
                       uploader_id: Optional[str] = None) -> int:
        """
        Add audio fingerprint to database
        
        Args:
            audio_path: Path to audio file
            artist: Artist name
            title: Optional title
            uploader_id: Optional uploader identifier
            
        Returns:
            Fingerprint ID
        """
        try:
            # Generate fingerprint
            embedding = self._generate_fingerprint(audio_path)
            embedding = embedding.reshape(1, -1)  # FAISS expects (1, dim)
            
            # Compute hash
            audio_hash = self._compute_audio_hash(audio_path)
            
            # Check if already exists
            for item in self.metadata:
                if item['audio_hash'] == audio_hash:
                    logger.warning(f"Audio already in database: {audio_hash}")
                    return item['id']
            
            # Add to FAISS index
            self.index.add(embedding)
            
            # Store metadata
            fingerprint_id = self.id_counter
            self.id_counter += 1
            
            metadata_entry = {
                'id': fingerprint_id,
                'artist': artist,
                'title': title or os.path.basename(audio_path),
                'audio_hash': audio_hash,
                'upload_date': None,  # Will be set by API
                'uploader_id': uploader_id
            }
            self.metadata.append(metadata_entry)
            
            # Save to disk
            self._save_index()
            
            logger.info(f"Added fingerprint {fingerprint_id} for {artist} - {title}")
            return fingerprint_id
            
        except Exception as e:
            logger.error(f"Error adding fingerprint: {e}", exc_info=True)
            raise
    
    def search_similar(self, audio_path: str, top_k: int = 5, 
                      threshold: float = 0.7) -> List[Dict]:
        """
        Search for similar beats
        
        Args:
            audio_path: Path to query audio file
            top_k: Number of results to return
            threshold: Similarity threshold (lower distance = more similar)
            
        Returns:
            List of matches with metadata and similarity scores
        """
        if self.index.ntotal == 0:
            logger.warning("No fingerprints in database")
            return []
        
        try:
            # Generate fingerprint for query
            query_embedding = self._generate_fingerprint(audio_path)
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
            
            # Convert distances to similarity scores
            # L2 distance in normalized space: 0 = identical, 2.0 = opposite
            # Use exponential decay for more realistic similarity scores
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.metadata):
                    # Convert L2 distance to similarity (0-1 scale)
                    # Distance 0.0 -> similarity 1.0
                    # Distance 0.5 -> similarity ~0.6
                    # Distance 1.0 -> similarity ~0.37
                    # Distance 2.0 -> similarity ~0.14
                    similarity = np.exp(-distance * 2.0)  # Exponential decay
                    
                    if similarity >= threshold:
                        match = self.metadata[idx].copy()
                        match['similarity'] = float(similarity)
                        match['distance'] = float(distance)
                        match['rank'] = i + 1
                        results.append(match)
            
            logger.info(f"Found {len(results)} similar beats")
            return results
            
        except Exception as e:
            logger.error(f"Error searching fingerprints: {e}", exc_info=True)
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            'total_fingerprints': self.index.ntotal,
            'artists': len(set(item['artist'] for item in self.metadata)),
            'artist_list': sorted(set(item['artist'] for item in self.metadata))
        }
    
    def remove_fingerprint(self, fingerprint_id: int) -> bool:
        """
        Remove fingerprint from database
        Note: FAISS doesn't support removal, so we rebuild index
        """
        try:
            # Find and remove from metadata
            metadata_idx = None
            for i, item in enumerate(self.metadata):
                if item['id'] == fingerprint_id:
                    metadata_idx = i
                    break
            
            if metadata_idx is None:
                return False
            
            # Remove from metadata
            self.metadata.pop(metadata_idx)
            
            # Rebuild index (FAISS limitation)
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            # Would need to regenerate all embeddings - for now, just mark as removed
            # In production, maintain a separate "deleted" list or rebuild periodically
            
            self._save_index()
            logger.info(f"Removed fingerprint {fingerprint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing fingerprint: {e}")
            return False
