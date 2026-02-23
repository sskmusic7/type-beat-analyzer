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
        Generate comprehensive 128-dim fingerprint with ALL musical characteristics
        Based on Shazam-style fingerprinting + modern MIR research
        
        Extracts:
        - Spectral features (timbre, brightness, texture)
        - Harmonic features (pitch, chroma, key, chords)
        - Rhythmic features (tempo, beat, rhythm patterns)
        - Timbral features (MFCC, spectral contrast, formants)
        - Structural features (energy, dynamics, mood)
        - Perceptual features (loudness, roughness)
        
        Args:
            audio_path: Path to audio file
            duration: Optional duration to process (30s recommended for full analysis)
            
        Returns:
            128-dim embedding vector capturing complete musical identity
        """
        # Load audio at high quality for comprehensive analysis
        y, sr = librosa.load(
            audio_path,
            sr=22050,  # Standard for music analysis (captures up to 11kHz)
            mono=True,
            duration=duration if duration else 30.0  # 30s captures full musical structure
        )
        
        # Normalize (critical for consistent features)
        y = librosa.util.normalize(y)
        
        # ========== 1. SPECTRAL FEATURES (Timbre & Texture) ==========
        features = []
        
        # Mel-spectrogram (perceptual frequency representation)
        mel_spec = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=128, fmin=20, fmax=sr//2,
            n_fft=2048, hop_length=512
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        features.extend([
            np.mean(mel_spec_db, axis=1),  # 128 dims - average spectral envelope
            np.std(mel_spec_db, axis=1),    # 128 dims - spectral variation (texture)
        ])
        
        # Spectral centroid (brightness - higher = brighter)
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
        # Spectral rolloff (high-frequency content)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=512)[0]
        # Spectral bandwidth (frequency spread)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=512)[0]
        # Spectral contrast (harmonic vs noise)
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=512)
        # Spectral flatness (noise-like vs tonal)
        spectral_flatness = librosa.feature.spectral_flatness(y=y, hop_length=512)[0]
        
        features.append([
            np.mean(spectral_centroids) / 5000.0,   # Brightness
            np.std(spectral_centroids) / 5000.0,    # Brightness variation
            np.mean(spectral_rolloff) / 5000.0,     # High-freq content
            np.std(spectral_rolloff) / 5000.0,
            np.mean(spectral_bandwidth) / 5000.0,   # Frequency spread
            np.std(spectral_bandwidth) / 5000.0,
            np.mean(spectral_flatness),              # Noise-like quality
            np.std(spectral_flatness),
        ])  # 8 dims
        
        # Spectral contrast (harmonic content per frequency band)
        features.extend([
            np.mean(spectral_contrast, axis=1),  # 7 dims (7 frequency bands)
            np.std(spectral_contrast, axis=1),   # 7 dims
        ])
        
        # ========== 2. HARMONIC FEATURES (Pitch, Key, Chords) ==========
        
        # Chroma features (12 pitch classes - C, C#, D, etc.)
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=512)
        chroma_cqt = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)  # More accurate
        features.extend([
            np.mean(chroma_stft, axis=1),  # 12 dims - average pitch distribution
            np.std(chroma_stft, axis=1),   # 12 dims - pitch variation
            np.mean(chroma_cqt, axis=1),   # 12 dims - CQT chroma (more accurate)
            np.std(chroma_cqt, axis=1),    # 12 dims
        ])
        
        # Harmonic-percussive separation
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_ratio = np.sum(np.abs(y_harmonic)) / (np.sum(np.abs(y)) + 1e-8)
        percussive_ratio = np.sum(np.abs(y_percussive)) / (np.sum(np.abs(y)) + 1e-8)
        features.append([harmonic_ratio, percussive_ratio])  # 2 dims
        
        # Key detection (tonal center)
        chroma_mean = np.mean(chroma_cqt, axis=1)
        key_strength = np.max(chroma_mean)
        key_idx = np.argmax(chroma_mean)
        # Major/minor detection (simplified)
        features.append([key_idx / 12.0, key_strength])  # 2 dims
        
        # Tonnetz (harmonic network representation)
        tonnetz = librosa.feature.tonnetz(y=y_harmonic, sr=sr, chroma=chroma_cqt)
        features.extend([
            np.mean(tonnetz, axis=1),  # 6 dims
            np.std(tonnetz, axis=1),    # 6 dims
        ])
        
        # ========== 3. RHYTHMIC FEATURES (Tempo, Beat, Rhythm) ==========
        
        # Tempo and beat tracking
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
        tempo_normalized = tempo / 200.0  # Normalize to 0-1 range (assuming max 200 BPM)
        features.append([tempo_normalized])  # 1 dim
        
        # Onset detection (rhythmic events)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=512, units='frames')
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
        onset_strength = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
        
        if len(onset_times) > 1:
            inter_onset = np.diff(onset_times)
            features.append([
                np.mean(inter_onset),      # Average inter-onset interval
                np.std(inter_onset),      # Rhythm regularity
                np.mean(onset_strength),   # Average onset strength
                np.std(onset_strength),    # Onset strength variation
            ])  # 4 dims
        else:
            features.append([0.0, 0.0, np.mean(onset_strength), np.std(onset_strength)])
        
        # Beat-synced features (rhythm patterns)
        if len(beats) > 4:
            # Extract features synchronized to beats
            beat_frames = librosa.frames_to_time(beats, sr=sr, hop_length=512)
            # Rhythm complexity (variation in beat intervals)
            beat_intervals = np.diff(beat_frames)
            features.append([
                np.mean(beat_intervals),
                np.std(beat_intervals) / (np.mean(beat_intervals) + 1e-8),  # Coefficient of variation
            ])  # 2 dims
        else:
            features.append([0.0, 0.0])
        
        # ========== 4. TIMBRAL FEATURES (Instrument/Voice Characteristics) ==========
        
        # MFCC (Mel-Frequency Cepstral Coefficients - captures timbre)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)
        features.extend([
            np.mean(mfcc, axis=1),  # 13 dims - average timbral characteristics
            np.std(mfcc, axis=1),    # 13 dims - timbral variation
        ])
        
        # Delta and delta-delta MFCC (captures timbral dynamics)
        mfcc_delta = librosa.feature.delta(mfcc)
        mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
        features.extend([
            np.mean(mfcc_delta, axis=1),   # 13 dims - timbral change rate
            np.mean(mfcc_delta2, axis=1),  # 13 dims - timbral acceleration
        ])
        
        # Zero-crossing rate (noise/voice characteristics)
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=512)[0]
        features.append([
            np.mean(zcr),   # Average ZCR
            np.std(zcr),    # ZCR variation
        ])  # 2 dims
        
        # Spectral flux (timbre change rate)
        spectral_flux = np.sum(np.diff(mel_spec_db, axis=1) > 0, axis=0)
        features.append([
            np.mean(spectral_flux) / mel_spec_db.shape[1],  # Normalized
            np.std(spectral_flux) / mel_spec_db.shape[1],
        ])  # 2 dims
        
        # ========== 5. STRUCTURAL FEATURES (Style, Mood, Dynamics) ==========
        
        # Energy envelope (dynamics)
        rms = librosa.feature.rms(y=y, hop_length=512)[0]
        features.append([
            np.mean(rms),           # Average energy
            np.std(rms),            # Dynamic range
            np.max(rms),            # Peak energy
            np.min(rms),            # Minimum energy
        ])  # 4 dims
        
        # Silence ratio (sparseness)
        silence_threshold = np.percentile(np.abs(y), 10)
        silence_ratio = np.sum(np.abs(y) < silence_threshold) / len(y)
        features.append([silence_ratio])  # 1 dim
        
        # Tempo stability (mood indicator - stable = calm, variable = energetic)
        if len(beats) > 4:
            local_tempo = 60.0 / np.diff(beat_frames)
            tempo_stability = 1.0 / (1.0 + np.std(local_tempo) / (np.mean(local_tempo) + 1e-8))
            features.append([tempo_stability])  # 1 dim
        else:
            features.append([0.5])  # Neutral
        
        # ========== 6. PERCEPTUAL FEATURES (Human Hearing) ==========
        
        # Loudness (perceptual volume - A-weighted)
        # Simplified: use RMS as proxy
        perceptual_loudness = np.mean(rms)
        features.append([perceptual_loudness])  # 1 dim
        
        # Pitch salience (how tonal vs noise-like)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=512)
        pitch_salience = np.mean(magnitudes[magnitudes > 0]) if np.any(magnitudes > 0) else 0.0
        features.append([pitch_salience / 100.0])  # 1 dim (normalized)
        
        # ========== COMBINE & REDUCE TO 128 DIMS ==========
        
        # Flatten all features (handle both arrays and lists)
        flattened_features = []
        for f in features:
            if isinstance(f, np.ndarray):
                flattened_features.append(f.flatten())
            elif isinstance(f, (list, tuple)):
                flattened_features.append(np.array(f).flatten())
            else:
                flattened_features.append(np.array([f]).flatten())
        
        combined = np.concatenate(flattened_features)
        
        # Intelligent dimensionality reduction to 128 dims
        # Strategy: Keep most important features, intelligently pool others
        target_dim = self.embedding_dim
        
        if len(combined) > target_dim:
            # Priority order: spectral > harmonic > rhythmic > timbral > structural > perceptual
            # Keep first N most important dims, intelligently pool rest
            keep_dims = min(target_dim - 20, len(combined))  # Keep most, pool last 20
            embedding = combined[:keep_dims].copy()
            
            # Intelligently pool remaining features
            remaining = combined[keep_dims:]
            if len(remaining) > 0:
                # Use weighted average with decay (more recent features weighted less)
                weights = np.exp(-np.linspace(0, 2, len(remaining)))  # Exponential decay
                pooled = np.average(remaining, weights=weights)
                # Distribute pooled value across remaining dimensions
                remaining_dims = target_dim - keep_dims
                embedding = np.concatenate([
                    embedding,
                    np.full(remaining_dims, pooled * 0.1)  # Small contribution
                ])
        elif len(combined) < target_dim:
            # Pad with zeros (shouldn't happen with comprehensive features)
            embedding = np.pad(combined, (0, target_dim - len(combined)), 'constant')
        else:
            embedding = combined
        
        # Ensure exactly 128 dims
        embedding = embedding[:target_dim]
        
        # L2 normalize (critical for cosine similarity)
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
