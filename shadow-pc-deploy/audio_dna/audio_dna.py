"""
AudioDNA — Unified audio profile combining all analysis modules.

Orchestrates:
    1. CLAPScorer       → text-prompt tags (mood, genre, instruments)
    2. FeatureExtractor → tempo, key, spectral, MFCC, energy, rhythm
    3. StemSeparator    → stem breakdown (drums, bass, vocals, other)

Produces a single structured JSON profile per track.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from .clap_scorer import CLAPScorer
from .feature_extractor import FeatureExtractor
from .stem_separator import StemSeparator


class AudioDNA:
    """
    Generate a comprehensive 'DNA profile' for an audio track.

    Each module is optional — if demucs isn't installed or you want
    a faster profile, disable stems.
    """

    def __init__(
        self,
        enable_clap: bool = True,
        enable_features: bool = True,
        enable_stems: bool = True,
        clap_top_n: int = 15,
    ):
        self.enable_clap = enable_clap
        self.enable_features = enable_features
        self.enable_stems = enable_stems
        self.clap_top_n = clap_top_n

        self._clap: Optional[CLAPScorer] = None
        self._extractor: Optional[FeatureExtractor] = None
        self._separator: Optional[StemSeparator] = None

    def _get_clap(self) -> CLAPScorer:
        if self._clap is None:
            self._clap = CLAPScorer()
        return self._clap

    def _get_extractor(self) -> FeatureExtractor:
        if self._extractor is None:
            self._extractor = FeatureExtractor()
        return self._extractor

    def _get_separator(self) -> StemSeparator:
        if self._separator is None:
            self._separator = StemSeparator()
        return self._separator

    def profile(self, audio_path: str) -> Dict[str, Any]:
        """
        Generate a full AudioDNA profile for a track.

        Args:
            audio_path: Path to WAV or MP3 file.

        Returns:
            Dict with keys: clap_tags, features, stems, meta.
        """
        audio_path = str(Path(audio_path).resolve())
        t0 = time.perf_counter()
        result: Dict[str, Any] = {}

        # Phase 2: Feature extraction (fast, always run first)
        if self.enable_features:
            print(f"[AudioDNA] Extracting features ...")
            features = self._get_extractor().extract(audio_path)
            result["features"] = features

        # Phase 1: CLAP zero-shot tags
        if self.enable_clap:
            print(f"[AudioDNA] Running CLAP zero-shot scoring ...")
            tags = self._get_clap().top_tags(audio_path, n=self.clap_top_n)
            result["clap_tags"] = [
                {"tag": tag, "score": round(score, 4)} for tag, score in tags
            ]
            # Also store all scores for vector use
            all_scores = self._get_clap().score_audio(audio_path)
            result["clap_vector"] = list(all_scores.values())

        # Phase 3: Stem separation (slow on CPU, optional)
        if self.enable_stems:
            try:
                print(f"[AudioDNA] Separating stems (this takes a few minutes on CPU) ...")
                stem_data = self._get_separator().analyze_stems(audio_path)
                result["stems"] = stem_data
            except ImportError:
                print("[AudioDNA] Demucs not installed, skipping stem separation.")
                result["stems"] = None
            except Exception as e:
                print(f"[AudioDNA] Stem separation failed: {e}")
                result["stems"] = None

        elapsed = time.perf_counter() - t0
        result["meta"] = {
            "file": Path(audio_path).name,
            "processing_time_sec": round(elapsed, 1),
            "modules_used": {
                "clap": self.enable_clap,
                "features": self.enable_features,
                "stems": self.enable_stems,
            },
        }

        return result

    def profile_fast(self, audio_path: str) -> Dict[str, Any]:
        """
        Quick profile without stem separation (~60s total).
        Good for batch processing or real-time API use.
        """
        old_stems = self.enable_stems
        self.enable_stems = False
        try:
            return self.profile(audio_path)
        finally:
            self.enable_stems = old_stems

    # Feature weights — tuned from variance analysis across 92 artists.
    # CLAP dims have ~0.013 std (low discrimination in same-genre data),
    # while MFCCs have ~0.04-0.27 std and BPM/rhythm ~0.05-0.07.
    # Weights amplify discriminating features so cosine similarity spreads out.
    FEATURE_WEIGHTS = {
        "clap": 0.1,          # 52 dims — heavily downweight (low variance within genre)
        "bpm": 8.0,           # 1 dim — strong discriminator
        "key_conf": 5.0,      # 1 dim
        "spectral": 4.0,      # 2 dims
        "mfcc": 6.0,          # 20 dims — strongest discriminator
        "energy": 5.0,        # 1 dim
        "rhythm": 6.0,        # 2 dims
        "stems": 4.0,         # 4 dims
    }

    def to_vector(self, dna: Dict[str, Any]) -> List[float]:
        """
        Flatten an AudioDNA profile into a weighted 83-dim numeric vector
        suitable for FAISS indexing and similarity search.

        Features are weighted by discriminative power so that cosine
        similarity actually separates different-sounding artists.

        Vector layout (83 dims):
            [0:52]   CLAP scores × 0.3
            [52:53]  BPM normalized × 4.0
            [53:54]  Key confidence × 3.0
            [54:56]  Spectral (centroid, flatness) × 2.0
            [56:76]  MFCC means × 3.0
            [76:77]  RMS energy × 3.0
            [77:79]  Rhythm (onset density, beat regularity) × 3.0
            [79:83]  Stem mix ratios × 2.5
        """
        w = self.FEATURE_WEIGHTS
        vec: List[float] = []

        # CLAP vector (52 dims) — downweighted
        if "clap_vector" in dna and dna["clap_vector"]:
            vec.extend([v * w["clap"] for v in dna["clap_vector"]])
        else:
            vec.extend([0.0] * 52)

        # Features
        features = dna.get("features", {})
        tempo = features.get("tempo", {})
        bpm = tempo.get("bpm", 0.0)
        vec.append(max(0.0, min(1.0, (bpm - 40) / 160)) * w["bpm"])

        key_info = features.get("key", {})
        vec.append(key_info.get("confidence", 0.0) * w["key_conf"])

        spectral = features.get("spectral", {})
        vec.append(min(1.0, spectral.get("centroid_mean", 0) / 8000) * w["spectral"])
        vec.append(spectral.get("flatness_mean", 0) * w["spectral"])

        mfcc = features.get("mfcc", {})
        mfcc_means = mfcc.get("mfcc_mean", [0.0] * 20)
        vec.extend([m / 100.0 * w["mfcc"] for m in mfcc_means[:20]])
        if len(mfcc_means) < 20:
            vec.extend([0.0] * (20 - len(mfcc_means)))

        energy = features.get("energy", {})
        vec.append(energy.get("rms_mean", 0) * w["energy"])

        rhythm = features.get("rhythm", {})
        vec.append(min(1.0, rhythm.get("onset_density", 0) / 10.0) * w["rhythm"])
        vec.append(min(1.0, rhythm.get("beat_regularity", 0) / 200.0) * w["rhythm"])

        # Stems (4 dims)
        stems = dna.get("stems", {})
        if stems and "stems" in stems:
            stem_data = stems["stems"]
            vec.append(stem_data.get("drums", {}).get("mix_ratio", 0) * w["stems"])
            vec.append(stem_data.get("bass", {}).get("mix_ratio", 0) * w["stems"])
            vec.append(stem_data.get("other", {}).get("mix_ratio", 0) * w["stems"])
            vec.append(stem_data.get("vocals", {}).get("mix_ratio", 0) * w["stems"])
        else:
            vec.extend([0.0] * 4)

        return vec
