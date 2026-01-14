"""
Audio feature extraction using librosa
Based on research papers: mel-spectrograms + MFCC + tempo + key
"""

import librosa
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Extract audio features for type beat classification
    Based on research: mel-spectrograms work best for CNNs
    """
    
    def __init__(self, sample_rate: int = 22050, duration: int = 30):
        """
        Args:
            sample_rate: Target sample rate (22050 is standard)
            duration: Max duration in seconds to analyze (30s is enough per research)
        """
        self.sample_rate = sample_rate
        self.duration = duration
    
    def extract_features(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive audio features
        
        Returns:
            Dictionary with:
            - mel_spectrogram: (128, time_frames) - for CNN input
            - mfcc: (13, time_frames) - additional features
            - tempo: BPM
            - key: Musical key
            - chroma: Chroma features
            - spectral_centroid: Spectral centroid
            - zero_crossing_rate: ZCR
        """
        try:
            # Load audio (normalize to mono, resample)
            y, sr = librosa.load(
                audio_path,
                sr=self.sample_rate,
                mono=True,
                duration=self.duration
            )
            
            # Normalize audio (CRITICAL per research papers)
            y = librosa.util.normalize(y)
            
            # Extract mel-spectrogram (128 bins - standard for music)
            mel_spec = librosa.feature.melspectrogram(
                y=y,
                sr=sr,
                n_mels=128,
                fmax=8000
            )
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            # MFCC features (13 coefficients)
            mfcc = librosa.feature.mfcc(
                y=y,
                sr=sr,
                n_mfcc=13
            )
            
            # Tempo estimation
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            # Chroma features (harmonic content)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # Key detection (simplified - could use more advanced methods)
            # Using chroma to estimate key
            chroma_mean = np.mean(chroma, axis=1)
            key_idx = np.argmax(chroma_mean)
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key = key_names[key_idx]
            
            features = {
                'mel_spectrogram': mel_spec_db,
                'mfcc': mfcc,
                'tempo': float(tempo),
                'key': key,
                'chroma': chroma,
                'spectral_centroid': spectral_centroid.tolist(),
                'zero_crossing_rate': zero_crossing_rate.tolist(),
                'duration': len(y) / sr
            }
            
            logger.info(f"Extracted features: tempo={tempo:.1f} BPM, key={key}")
            return features
        
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            raise ValueError(f"Failed to process audio: {str(e)}")
    
    def preprocess_for_model(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Preprocess features for model input
        Returns mel-spectrogram ready for CNN
        """
        mel_spec = features['mel_spectrogram']
        
        # Normalize to [0, 1] range
        mel_spec = (mel_spec - mel_spec.min()) / (mel_spec.max() - mel_spec.min() + 1e-8)
        
        # Reshape for CNN: (1, 128, time_frames) - add channel dimension
        if len(mel_spec.shape) == 2:
            mel_spec = np.expand_dims(mel_spec, axis=0)
        
        return mel_spec
