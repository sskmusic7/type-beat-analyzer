"""
Audio Feature Extractor for type beat analysis.

Uses librosa to extract structured audio features:
- Tempo (BPM) with confidence
- Musical key detection (Krumhansl-Schmuckler algorithm)
- Spectral features (centroid, rolloff, contrast, bandwidth, flatness)
- MFCC statistics (timbre profile)
- Energy profile (RMS over time)
- Rhythm features (onset strength, beat regularity)

Replaces essentia-tensorflow (incompatible with Python 3.14).
"""

import numpy as np
import librosa
from pathlib import Path
from typing import Dict, Any, Optional


# Krumhansl-Schmuckler key profiles for major and minor keys
_MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
_KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _detect_key(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Detect musical key using chroma features + Krumhansl-Schmuckler algorithm.

    Returns dict with key name, mode (major/minor), and confidence.
    """
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_avg = chroma.mean(axis=1)  # shape: (12,)

    best_corr = -2.0
    best_key = 0
    best_mode = "major"

    for shift in range(12):
        rolled = np.roll(chroma_avg, -shift)
        corr_major = np.corrcoef(rolled, _MAJOR_PROFILE)[0, 1]
        corr_minor = np.corrcoef(rolled, _MINOR_PROFILE)[0, 1]

        if corr_major > best_corr:
            best_corr = corr_major
            best_key = shift
            best_mode = "major"
        if corr_minor > best_corr:
            best_corr = corr_minor
            best_key = shift
            best_mode = "minor"

    return {
        "key": _KEY_NAMES[best_key],
        "mode": best_mode,
        "key_label": f"{_KEY_NAMES[best_key]} {best_mode}",
        "confidence": round(float(max(best_corr, 0.0)), 4),
    }


def _spectral_features(y: np.ndarray, sr: int) -> Dict[str, float]:
    """Extract summary statistics of spectral features."""
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    flatness = librosa.feature.spectral_flatness(y=y)[0]

    return {
        "centroid_mean": round(float(centroid.mean()), 2),
        "centroid_std": round(float(centroid.std()), 2),
        "rolloff_mean": round(float(rolloff.mean()), 2),
        "bandwidth_mean": round(float(bandwidth.mean()), 2),
        "flatness_mean": round(float(flatness.mean()), 6),
        "contrast_mean": [round(float(c), 2) for c in contrast.mean(axis=1)],
    }


def _mfcc_stats(y: np.ndarray, sr: int, n_mfcc: int = 20) -> Dict[str, list]:
    """Extract MFCC mean and std for timbre profiling."""
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return {
        "mfcc_mean": [round(float(m), 4) for m in mfcc.mean(axis=1)],
        "mfcc_std": [round(float(s), 4) for s in mfcc.std(axis=1)],
    }


def _energy_profile(y: np.ndarray, sr: int, n_segments: int = 16) -> Dict[str, Any]:
    """RMS energy profile split into n_segments for dynamics analysis."""
    rms = librosa.feature.rms(y=y)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)

    # Split into segments for an energy curve
    seg_len = max(1, len(rms) // n_segments)
    segments = [float(rms[i * seg_len:(i + 1) * seg_len].mean()) for i in range(n_segments)]

    return {
        "rms_mean": round(float(rms.mean()), 6),
        "rms_std": round(float(rms.std()), 6),
        "rms_db_mean": round(float(rms_db.mean()), 2),
        "dynamic_range_db": round(float(rms_db.max() - rms_db.min()), 2),
        "energy_curve": [round(s, 6) for s in segments],
    }


def _rhythm_features(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """Extract rhythm-related features beyond basic BPM."""
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

    # Beat regularity: std of inter-beat intervals (lower = more regular)
    if len(beats) > 1:
        beat_times = librosa.frames_to_time(beats, sr=sr)
        ibis = np.diff(beat_times)
        regularity = round(float(1.0 / (ibis.std() + 1e-6)), 4)
    else:
        regularity = 0.0

    # Onset density (onsets per second)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    duration = librosa.get_duration(y=y, sr=sr)
    onset_density = round(len(onsets) / max(duration, 0.1), 2)

    return {
        "onset_density": onset_density,
        "beat_regularity": regularity,
        "num_beats": len(beats),
    }


class FeatureExtractor:
    """
    Extract structured audio features from a WAV/MP3 file using librosa.

    Replaces Essentia TF models (incompatible with Python 3.14) with
    librosa equivalents for tempo, key, spectral, MFCC, energy, and rhythm.
    """

    def __init__(self, sr: int = 22050, duration: Optional[float] = None):
        """
        Args:
            sr: Target sample rate for loading audio.
            duration: Max seconds to load. None = full track.
        """
        self.sr = sr
        self.duration = duration

    def extract(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract all features from an audio file.

        Args:
            audio_path: Path to WAV or MP3 file.

        Returns:
            Dict with keys: tempo, key, spectral, mfcc, energy, rhythm, meta.
        """
        audio_path = str(Path(audio_path).resolve())
        y, sr = librosa.load(audio_path, sr=self.sr, duration=self.duration, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)

        # Tempo
        tempo_val, _ = librosa.beat.beat_track(y=y, sr=sr)
        # librosa may return array; extract scalar
        if hasattr(tempo_val, '__len__'):
            tempo_val = float(tempo_val[0]) if len(tempo_val) > 0 else 0.0
        else:
            tempo_val = float(tempo_val)

        return {
            "tempo": {
                "bpm": round(tempo_val, 1),
                "half_time": round(tempo_val / 2, 1),
                "double_time": round(tempo_val * 2, 1),
            },
            "key": _detect_key(y, sr),
            "spectral": _spectral_features(y, sr),
            "mfcc": _mfcc_stats(y, sr),
            "energy": _energy_profile(y, sr),
            "rhythm": _rhythm_features(y, sr),
            "meta": {
                "duration_sec": round(duration, 2),
                "sample_rate": sr,
            },
        }
