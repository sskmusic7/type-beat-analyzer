"""
Artist DNA Aggregation — Phase 5

Processes multiple tracks per artist through AudioDNA,
then aggregates into a composite artist profile with
mean/std/distribution across all features.

Used for:
    - Building artist reference profiles from 20-50 tracks
    - "Your beat sounds like X" matching (Phase 6 blend engine)
    - Artist similarity clustering
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

from .audio_dna import AudioDNA

logger = logging.getLogger(__name__)


class ArtistDNA:
    """
    Aggregate multiple track DNAs into a composite artist profile.

    The profile captures the artist's "sonic signature" — what their
    typical production sounds like across many tracks.
    """

    def __init__(
        self,
        enable_stems: bool = False,
        clap_top_n: int = 15,
        output_dir: Optional[str] = None,
    ):
        """
        Args:
            enable_stems: Whether to run Demucs stem separation per track.
                          Adds ~80s per track — disable for faster batch processing.
            clap_top_n: Number of top CLAP tags to keep per track.
            output_dir: Directory to save artist DNA profiles.
                        Defaults to ``<script_dir>/../data/artist_dna/``.
        """
        self.dna = AudioDNA(
            enable_clap=True,
            enable_features=True,
            enable_stems=enable_stems,
            clap_top_n=clap_top_n,
        )
        if output_dir is None:
            base = Path(__file__).resolve().parent.parent
            self.output_dir = base / "data" / "artist_dna"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def profile_tracks(self, audio_paths: List[str], artist: str) -> List[Dict[str, Any]]:
        """
        Generate AudioDNA profiles for a list of tracks.

        Args:
            audio_paths: List of paths to audio files.
            artist: Artist name (for metadata).

        Returns:
            List of AudioDNA profile dicts (one per track).
        """
        profiles = []
        total = len(audio_paths)

        for i, path in enumerate(audio_paths, 1):
            try:
                logger.info(f"[{i}/{total}] Profiling: {Path(path).name}")
                if self.dna.enable_stems:
                    profile = self.dna.profile(path)
                else:
                    profile = self.dna.profile_fast(path)
                profile["meta"]["artist"] = artist
                profile["meta"]["track_file"] = Path(path).name
                profiles.append(profile)
            except Exception as e:
                logger.warning(f"[{i}/{total}] Failed to profile {Path(path).name}: {e}")
                continue

        logger.info(f"Profiled {len(profiles)}/{total} tracks for {artist}")
        return profiles

    def aggregate(self, profiles: List[Dict[str, Any]], artist: str) -> Dict[str, Any]:
        """
        Aggregate multiple track profiles into a composite artist DNA.

        Computes mean, std, min, max across all numeric features.
        For CLAP tags, computes average scores and identifies signature tags.

        Args:
            profiles: List of AudioDNA profiles from profile_tracks().
            artist: Artist name.

        Returns:
            Composite artist DNA dict.
        """
        if not profiles:
            raise ValueError(f"No profiles to aggregate for {artist}")

        n = len(profiles)

        # --- Aggregate DNA vectors ---
        vectors = [self.dna.to_vector(p) for p in profiles]
        vec_array = np.array(vectors, dtype=np.float32)  # (n, 83)
        centroid = vec_array.mean(axis=0).tolist()
        spread = vec_array.std(axis=0).tolist()

        # --- Aggregate tempo ---
        bpms = [p["features"]["tempo"]["bpm"] for p in profiles if "features" in p]
        tempo_agg = {
            "bpm_mean": round(float(np.mean(bpms)), 1),
            "bpm_std": round(float(np.std(bpms)), 1),
            "bpm_min": round(float(np.min(bpms)), 1),
            "bpm_max": round(float(np.max(bpms)), 1),
            "bpm_median": round(float(np.median(bpms)), 1),
        } if bpms else {}

        # --- Aggregate key ---
        keys = [p["features"]["key"]["key_label"] for p in profiles if "features" in p]
        key_counts: Dict[str, int] = {}
        for k in keys:
            key_counts[k] = key_counts.get(k, 0) + 1
        key_distribution = {k: round(v / len(keys), 3) for k, v in
                           sorted(key_counts.items(), key=lambda x: -x[1])}
        top_key = max(key_counts, key=key_counts.get) if key_counts else "unknown"

        # --- Aggregate CLAP tags ---
        # Average score per tag across all tracks
        tag_scores: Dict[str, List[float]] = {}
        for p in profiles:
            if "clap_tags" not in p:
                continue
            for tag_entry in p["clap_tags"]:
                tag = tag_entry["tag"]
                score = tag_entry["score"]
                if tag not in tag_scores:
                    tag_scores[tag] = []
                tag_scores[tag].append(score)

        tag_averages = {
            tag: round(float(np.mean(scores)), 4)
            for tag, scores in tag_scores.items()
        }
        # Signature tags: consistently high (mean > 0.65 and appears in >50% of tracks)
        signature_tags = [
            {"tag": tag, "avg_score": avg, "frequency": round(len(tag_scores[tag]) / n, 2)}
            for tag, avg in sorted(tag_averages.items(), key=lambda x: -x[1])
            if avg > 0.6 and len(tag_scores[tag]) / n > 0.5
        ][:15]

        # --- Aggregate spectral ---
        centroids = [p["features"]["spectral"]["centroid_mean"] for p in profiles if "features" in p]
        flatness = [p["features"]["spectral"]["flatness_mean"] for p in profiles if "features" in p]
        spectral_agg = {
            "centroid_mean": round(float(np.mean(centroids)), 1) if centroids else 0,
            "centroid_std": round(float(np.std(centroids)), 1) if centroids else 0,
            "flatness_mean": round(float(np.mean(flatness)), 6) if flatness else 0,
        }

        # --- Aggregate energy ---
        rms_vals = [p["features"]["energy"]["rms_mean"] for p in profiles if "features" in p]
        energy_agg = {
            "rms_mean": round(float(np.mean(rms_vals)), 6) if rms_vals else 0,
            "rms_std": round(float(np.std(rms_vals)), 6) if rms_vals else 0,
        }

        # --- Aggregate rhythm ---
        densities = [p["features"]["rhythm"]["onset_density"] for p in profiles if "features" in p]
        rhythm_agg = {
            "onset_density_mean": round(float(np.mean(densities)), 2) if densities else 0,
            "onset_density_std": round(float(np.std(densities)), 2) if densities else 0,
        }

        # --- Aggregate stems (if available) ---
        stems_agg = None
        stem_profiles = [p["stems"] for p in profiles if p.get("stems") and p["stems"].get("stems")]
        if stem_profiles:
            stem_names = list(stem_profiles[0]["stems"].keys())
            stems_agg = {}
            for name in stem_names:
                ratios = [sp["stems"][name]["mix_ratio"] for sp in stem_profiles if name in sp["stems"]]
                stems_agg[name] = {
                    "mix_ratio_mean": round(float(np.mean(ratios)), 4),
                    "mix_ratio_std": round(float(np.std(ratios)), 4),
                }

        # --- Build composite ---
        result = {
            "artist": artist,
            "track_count": n,
            "centroid_vector": centroid,
            "spread_vector": spread,
            "vector_dim": len(centroid),
            "tempo": tempo_agg,
            "key": {
                "top_key": top_key,
                "distribution": key_distribution,
            },
            "signature_tags": signature_tags,
            "tag_averages": tag_averages,
            "spectral": spectral_agg,
            "energy": energy_agg,
            "rhythm": rhythm_agg,
            "stems": stems_agg,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        return result

    def build_artist_profile(
        self, audio_paths: List[str], artist: str, save: bool = True
    ) -> Dict[str, Any]:
        """
        End-to-end: profile tracks → aggregate → optionally save.

        Args:
            audio_paths: List of audio file paths for this artist.
            artist: Artist name.
            save: If True, save profile JSON to output_dir.

        Returns:
            Composite artist DNA dict.
        """
        t0 = time.perf_counter()
        logger.info(f"Building artist DNA for '{artist}' from {len(audio_paths)} tracks ...")

        profiles = self.profile_tracks(audio_paths, artist)
        if not profiles:
            raise ValueError(f"No tracks could be profiled for {artist}")

        composite = self.aggregate(profiles, artist)
        elapsed = time.perf_counter() - t0
        composite["meta"] = {
            "processing_time_sec": round(elapsed, 1),
            "tracks_profiled": len(profiles),
            "tracks_attempted": len(audio_paths),
        }

        if save:
            safe_name = artist.lower().replace(" ", "_").replace("/", "_")
            out_path = self.output_dir / f"{safe_name}.json"
            with open(out_path, "w") as f:
                json.dump(composite, f, indent=2)
            logger.info(f"Saved artist DNA to {out_path}")

        logger.info(
            f"Artist DNA for '{artist}': {len(profiles)} tracks, "
            f"BPM {composite['tempo'].get('bpm_mean', '?')}, "
            f"Key {composite['key']['top_key']}, "
            f"{len(composite['signature_tags'])} signature tags, "
            f"{elapsed:.0f}s total"
        )

        return composite

    @staticmethod
    def load_profile(path: str) -> Dict[str, Any]:
        """Load a saved artist DNA profile from JSON."""
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def load_all_profiles(directory: str) -> Dict[str, Dict[str, Any]]:
        """Load all artist DNA profiles from a directory."""
        profiles = {}
        for p in Path(directory).glob("*.json"):
            data = ArtistDNA.load_profile(str(p))
            profiles[data["artist"]] = data
        return profiles
