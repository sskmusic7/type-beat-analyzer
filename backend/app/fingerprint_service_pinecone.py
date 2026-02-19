"""
Fingerprint Service using Pinecone (Managed Vector Database)
Free tier: 1 index, 100K vectors
"""

import numpy as np
import librosa
import hashlib
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not installed. Install with: pip install pinecone-client")


class FingerprintServicePinecone:
    """
    Fingerprint service using Pinecone managed vector database
    No local storage - everything in cloud
    """
    
    def __init__(self, api_key: Optional[str] = None, index_name: str = "type-beat-fingerprints"):
        """
        Initialize Pinecone service
        
        Args:
            api_key: Pinecone API key (or set PINECONE_API_KEY env var)
            index_name: Name of Pinecone index
        """
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone not installed. Install with: pip install pinecone-client")
        
        api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("Pinecone API key required. Set PINECONE_API_KEY env var or pass api_key")
        
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.embedding_dim = 128
        
        # Create or connect to index
        self._setup_index()
        
        # Metadata storage (Pinecone stores vectors, we need metadata)
        # Option 1: Store in Pinecone metadata (limited to 40KB per vector)
        # Option 2: Store in separate PostgreSQL table (recommended)
        self._metadata_db = None  # Could connect to PostgreSQL for metadata
    
    def _setup_index(self):
        """Create or connect to Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dim,
                    metric="cosine",  # Cosine similarity
                    spec=ServerlessSpec(
                        cloud="aws",  # or "gcp"
                        region="us-east-1"  # Choose your region
                    )
                )
                logger.info("Index created successfully")
            else:
                logger.info(f"Connecting to existing index: {self.index_name}")
            
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Index ready with {self.index.describe_index_stats().total_vector_count} vectors")
        except Exception as e:
            logger.error(f"Error setting up Pinecone index: {e}")
            raise
    
    def _generate_fingerprint(self, audio_path: str) -> np.ndarray:
        """Generate 128-dim fingerprint (same as other implementations)"""
        y, sr = librosa.load(audio_path, sr=8000, mono=True, duration=1.0)
        y = librosa.util.normalize(y)
        
        mel_spec = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=256, fmin=300, fmax=4000,
            n_fft=1024, hop_length=256
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_flat = mel_spec_db.flatten()
        
        if len(mel_flat) >= self.embedding_dim:
            embedding = mel_flat[:self.embedding_dim]
            if len(mel_flat) > self.embedding_dim:
                remaining = mel_flat[self.embedding_dim:]
                chunk_size = len(remaining) // (self.embedding_dim - 64)
                if chunk_size > 0:
                    pooled = [np.mean(remaining[i:i+chunk_size]) 
                             for i in range(0, len(remaining), chunk_size)]
                    embedding[64:] = pooled[:64]
        else:
            embedding = np.pad(mel_flat, (0, self.embedding_dim - len(mel_flat)), 'constant')
        
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding.astype(np.float32).tolist()  # Pinecone needs list
    
    def _compute_audio_hash(self, audio_path: str) -> str:
        """Compute SHA256 hash"""
        hasher = hashlib.sha256()
        with open(audio_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def add_fingerprint(self, audio_path: str, artist: str, 
                       title: Optional[str] = None, 
                       uploader_id: Optional[str] = None) -> str:
        """Add fingerprint to Pinecone"""
        try:
            embedding = self._generate_fingerprint(audio_path)
            audio_hash = self._compute_audio_hash(audio_path)
            
            # Use hash as vector ID
            vector_id = audio_hash[:16]  # Pinecone ID limit
            
            # Store metadata with vector
            metadata = {
                "artist": artist,
                "title": title or os.path.basename(audio_path),
                "audio_hash": audio_hash,
                "upload_date": datetime.now().isoformat(),
                "uploader_id": uploader_id or ""
            }
            
            # Upsert to Pinecone
            self.index.upsert(vectors=[(vector_id, embedding, metadata)])
            
            logger.info(f"Added fingerprint {vector_id} for {artist}")
            return vector_id
        except Exception as e:
            logger.error(f"Error adding fingerprint: {e}", exc_info=True)
            raise
    
    def search_similar(self, audio_path: str, top_k: int = 5, 
                      threshold: float = 0.7) -> List[Dict]:
        """Search for similar beats using Pinecone"""
        try:
            query_embedding = self._generate_fingerprint(audio_path)
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            matches = []
            for i, match in enumerate(results.matches):
                if match.score >= threshold:
                    matches.append({
                        'id': match.id,
                        'artist': match.metadata.get('artist', 'Unknown'),
                        'title': match.metadata.get('title', 'Unknown'),
                        'audio_hash': match.metadata.get('audio_hash', ''),
                        'upload_date': match.metadata.get('upload_date'),
                        'uploader_id': match.metadata.get('uploader_id'),
                        'similarity': float(match.score),
                        'distance': 1.0 - float(match.score),  # Cosine distance
                        'rank': i + 1
                    })
            
            logger.info(f"Found {len(matches)} similar beats")
            return matches
        except Exception as e:
            logger.error(f"Error searching: {e}", exc_info=True)
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            stats = self.index.describe_index_stats()
            
            # Get unique artists from metadata (would need to query or maintain separate list)
            # For now, return basic stats
            return {
                'total_fingerprints': stats.total_vector_count,
                'artists': 0,  # Would need to query metadata
                'artist_list': []  # Would need to query metadata
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'total_fingerprints': 0, 'artists': 0, 'artist_list': []}
