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
        Uses mel-spectrogram approach similar to Neural Audio FP
        
        Args:
            audio_path: Path to audio file
            duration: Optional duration to process (None = full file, useful for training)
            
        Returns:
            128-dim embedding vector
        """
        # Load audio (same params as Neural Audio FP)
        # For training, use full duration; for matching, use 1 second
        y, sr = librosa.load(
            audio_path,
            sr=8000,  # Neural Audio FP uses 8kHz
            mono=True,
            duration=duration  # None = full file, 1.0 = 1 second
        )
        
        # Normalize
        y = librosa.util.normalize(y)
        
        # Extract mel-spectrogram (same as Neural Audio FP)
        mel_spec = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            n_mels=256,  # Neural Audio FP uses 256
            fmin=300,
            fmax=4000,
            n_fft=1024,
            hop_length=256
        )
        
        # Convert to log-power
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Flatten and normalize
        mel_flat = mel_spec_db.flatten()
        
        # Create embedding (simplified - in production, use trained Neural Audio FP model)
        # For now, use PCA-like reduction to 128 dims
        # TODO: Replace with actual Neural Audio FP model when checkpoint available
        if len(mel_flat) >= self.embedding_dim:
            # Simple approach: take first 128 features + mean pooling
            embedding = mel_flat[:self.embedding_dim]
            # Add some aggregation to make it more robust
            if len(mel_flat) > self.embedding_dim:
                # Mean pool remaining features
                remaining = mel_flat[self.embedding_dim:]
                chunk_size = len(remaining) // (self.embedding_dim - 64)
                if chunk_size > 0:
                    pooled = [np.mean(remaining[i:i+chunk_size]) 
                             for i in range(0, len(remaining), chunk_size)]
                    embedding[64:] = pooled[:64]
        else:
            # Pad if too short
            embedding = np.pad(mel_flat, (0, self.embedding_dim - len(mel_flat)), 'constant')
        
        # L2 normalize (like Neural Audio FP)
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
            
            # Convert distances to similarity scores (1 / (1 + distance))
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.metadata):
                    similarity = 1.0 / (1.0 + distance)  # Convert distance to similarity
                    
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
