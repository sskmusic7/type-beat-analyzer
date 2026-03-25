"""
Blend Engine — Phase 6

FAISS-based similarity search over 83-dim AudioDNA vectors.
Given a user's beat, finds the closest artist matches and computes
blend percentages (e.g., "70% Drake / 20% Travis Scott / 10% Metro Boomin").

Features:
    - Build FAISS index from artist DNA profiles
    - Query with a beat's DNA vector
    - Multi-artist blend decomposition
    - Artist similarity matrix
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import faiss

logger = logging.getLogger(__name__)

# DNA vector dimension (must match AudioDNA.to_vector output)
DNA_DIM = 83


class BlendEngine:
    """
    Similarity search engine using FAISS over AudioDNA vectors.

    Supports two modes:
    1. **Artist centroids**: One vector per artist (fast, coarse).
       Good for "your beat sounds like Artist X".
    2. **Track-level**: One vector per track across all artists (detailed).
       Good for finding the single closest reference track.
    """

    def __init__(self, index_path: Optional[str] = None):
        """
        Args:
            index_path: Path to load a saved FAISS index + metadata.
                        If None, starts with an empty index.
        """
        self.index = faiss.IndexFlatIP(DNA_DIM)  # Inner product (cosine after normalization)
        self.metadata: List[Dict[str, Any]] = []  # Parallel list: one entry per vector
        self._artist_centroids: Dict[str, np.ndarray] = {}

        if index_path and Path(index_path).exists():
            self.load(index_path)

    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        """L2-normalize a vector for cosine similarity via inner product."""
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec

    def add_artist(self, artist_profile: Dict[str, Any]) -> None:
        """
        Add an artist's centroid vector to the index.

        Args:
            artist_profile: Output from ArtistDNA.build_artist_profile().
        """
        artist = artist_profile["artist"]
        centroid = np.array(artist_profile["centroid_vector"], dtype=np.float32)
        centroid_norm = self._normalize(centroid).reshape(1, -1)

        self.index.add(centroid_norm)
        self.metadata.append({
            "artist": artist,
            "type": "centroid",
            "track_count": artist_profile.get("track_count", 0),
            "top_key": artist_profile.get("key", {}).get("top_key", ""),
            "bpm_mean": artist_profile.get("tempo", {}).get("bpm_mean", 0),
        })
        self._artist_centroids[artist] = centroid

        logger.info(f"Added artist centroid: {artist} ({artist_profile.get('track_count', '?')} tracks)")

    def add_artists_from_dir(self, directory: str) -> int:
        """
        Load all artist DNA profiles from a directory and add to index.

        Returns number of artists added.
        """
        count = 0
        for p in sorted(Path(directory).glob("*.json")):
            try:
                with open(p) as f:
                    profile = json.load(f)
                if "centroid_vector" in profile:
                    self.add_artist(profile)
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to load {p.name}: {e}")
        logger.info(f"Loaded {count} artist profiles from {directory}")
        return count

    def query(
        self, beat_vector: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the top-k most similar artists/tracks to a beat.

        Args:
            beat_vector: 83-dim DNA vector from AudioDNA.to_vector().
            top_k: Number of results.

        Returns:
            List of dicts with artist, similarity score, and metadata.
        """
        vec = np.array(beat_vector, dtype=np.float32)
        vec = self._normalize(vec).reshape(1, -1)

        k = min(top_k, self.index.ntotal)
        if k == 0:
            return []

        scores, indices = self.index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx].copy()
            meta["similarity"] = round(float(score), 4)
            results.append(meta)

        return results

    def blend(
        self, beat_vector: List[float], top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Decompose a beat into a blend of artist influences.

        Returns:
            Dict with:
                - matches: top-k artist matches with similarity scores
                - blend: percentage breakdown (sums to 100%)
                - primary: the dominant artist match
        """
        matches = self.query(beat_vector, top_k=top_k)
        if not matches:
            return {"matches": [], "blend": {}, "primary": None}

        # Convert similarity scores to percentages
        # Use softmax-style normalization for smooth blend
        scores = np.array([m["similarity"] for m in matches], dtype=np.float32)
        # Shift to positive range and apply temperature
        shifted = scores - scores.min() + 0.1
        exp_scores = np.exp(shifted * 3.0)  # temperature=3 for sharper distribution
        percentages = exp_scores / exp_scores.sum()

        blend = {}
        for m, pct in zip(matches, percentages):
            artist = m["artist"]
            m["blend_pct"] = round(float(pct) * 100, 1)
            blend[artist] = m["blend_pct"]

        primary = matches[0]["artist"] if matches else None

        return {
            "matches": matches,
            "blend": blend,
            "primary": primary,
        }

    def artist_similarity_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Compute pairwise similarity between all artist centroids.

        Returns:
            Nested dict: matrix[artist_a][artist_b] = similarity score.
        """
        artists = list(self._artist_centroids.keys())
        if len(artists) < 2:
            return {}

        vecs = np.array([
            self._normalize(self._artist_centroids[a])
            for a in artists
        ], dtype=np.float32)

        # Cosine similarity matrix
        sim_matrix = vecs @ vecs.T

        result = {}
        for i, a in enumerate(artists):
            result[a] = {}
            for j, b in enumerate(artists):
                if a != b:
                    result[a][b] = round(float(sim_matrix[i, j]), 4)

        return result

    def blend_stems(
        self,
        stem_profiles: Dict[str, Dict[str, Any]],
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Per-stem matching: compare each stem (drums/bass/other/vocals)
        against artist profiles that have stem data.

        Args:
            stem_profiles: Dict of stem_name -> {mix_ratio, rms, spectral_centroid, ...}
                           from AudioDNA.profile() with enable_stems=True.
            top_k: Number of top artist matches per stem.

        Returns:
            Dict with per-stem top matches:
            {
                "drums": [{"artist": "Metro Boomin", "similarity": 0.92}, ...],
                "bass": [{"artist": "Southside", "similarity": 0.87}, ...],
                ...
            }
        """
        if not stem_profiles or not stem_profiles.get("stems"):
            return {"error": "No stem data provided. Run analysis with enable_stems=True."}

        stems_data = stem_profiles["stems"]
        results = {}

        # Load artist profiles that have stem data
        dna_dir = Path(__file__).parent.parent / "data" / "artist_dna"
        artist_stems = {}
        for p in dna_dir.glob("*.json"):
            try:
                with open(p) as f:
                    profile = json.load(f)
                if profile.get("stems"):
                    artist_stems[profile["artist"]] = profile["stems"]
            except Exception:
                continue

        if not artist_stems:
            return {"error": "No artist profiles with stem data found. Train with --stems flag."}

        # For each stem, compare mix ratios
        for stem_name, stem_info in stems_data.items():
            if not isinstance(stem_info, dict) or "mix_ratio" not in stem_info:
                continue

            query_ratio = stem_info["mix_ratio"]
            matches = []

            for artist, artist_stem_data in artist_stems.items():
                if stem_name not in artist_stem_data:
                    continue
                artist_ratio = artist_stem_data[stem_name].get("mix_ratio_mean", 0)
                # Similarity = 1 - abs(difference)
                diff = abs(query_ratio - artist_ratio)
                sim = max(0, 1.0 - diff * 5)  # Scale: 0.2 diff = 0 similarity
                matches.append({"artist": artist, "similarity": round(sim, 4)})

            matches.sort(key=lambda x: -x["similarity"])
            results[stem_name] = matches[:top_k]

        return {"stem_matches": results}

    def save(self, path: str) -> None:
        """Save FAISS index + metadata to disk."""
        base = Path(path)
        base.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(base / "dna_index.faiss"))
        with open(base / "dna_metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)

        # Save centroids separately for rebuilding
        centroids = {k: v.tolist() for k, v in self._artist_centroids.items()}
        with open(base / "dna_centroids.json", "w") as f:
            json.dump(centroids, f, indent=2)

        logger.info(f"Saved blend engine to {base} ({self.index.ntotal} vectors)")

    def load(self, path: str) -> None:
        """Load FAISS index + metadata from disk."""
        base = Path(path)

        index_file = base / "dna_index.faiss"
        meta_file = base / "dna_metadata.json"

        if index_file.exists():
            self.index = faiss.read_index(str(index_file))
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")

        if meta_file.exists():
            with open(meta_file) as f:
                self.metadata = json.load(f)

        centroids_file = base / "dna_centroids.json"
        if centroids_file.exists():
            with open(centroids_file) as f:
                raw = json.load(f)
            self._artist_centroids = {k: np.array(v, dtype=np.float32) for k, v in raw.items()}
