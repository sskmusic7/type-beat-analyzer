"""
Blend Engine — Phase 6

FAISS-based similarity search over 83-dim AudioDNA vectors.
Given a user's beat, finds the closest artist matches and computes
blend percentages (e.g., "70% Drake / 20% Travis Scott / 10% Metro Boomin").

Uses mean-centering to remove genre baseline — cosine similarity measures
how an artist *deviates* from the average, not absolute position.
This gives real discrimination (range -1 to +1) instead of everything
clustering at 0.95+.
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
    Similarity search engine using FAISS over mean-centered AudioDNA vectors.

    Mean-centering subtracts the population average so that cosine similarity
    captures *relative* differences between artists rather than shared genre
    characteristics. This spreads similarity from [-1, +1] instead of [0.93, 1.0].
    """

    def __init__(self, index_path: Optional[str] = None):
        self.index = faiss.IndexFlatIP(DNA_DIM)  # Inner product (cosine after normalization)
        self.metadata: List[Dict[str, Any]] = []  # Parallel list: one entry per vector
        self._artist_centroids: Dict[str, np.ndarray] = {}  # Raw (uncentered) vectors
        self._mean_vector: Optional[np.ndarray] = None  # Population mean for centering

        if index_path and Path(index_path).exists():
            self.load(index_path)

    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        """L2-normalize a vector for cosine similarity via inner product."""
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec

    def _center(self, vec: np.ndarray) -> np.ndarray:
        """Subtract population mean to remove genre baseline."""
        if self._mean_vector is not None:
            return vec - self._mean_vector
        return vec

    def add_artists_from_dir(self, directory: str) -> int:
        """
        Load all artist DNA profiles from a directory, compute population
        mean, mean-center all vectors, then build the FAISS index.

        Returns number of artists added.
        """
        # Phase 1: Load all raw centroids
        raw_profiles: List[Tuple[Dict[str, Any], np.ndarray]] = []
        for p in sorted(Path(directory).glob("*.json")):
            try:
                with open(p) as f:
                    profile = json.load(f)
                if "centroid_vector" in profile:
                    vec = np.array(profile["centroid_vector"], dtype=np.float32)
                    raw_profiles.append((profile, vec))
            except Exception as e:
                logger.warning(f"Failed to load {p.name}: {e}")

        if not raw_profiles:
            return 0

        # Phase 2: Compute population mean
        all_vecs = np.array([v for _, v in raw_profiles], dtype=np.float32)
        self._mean_vector = all_vecs.mean(axis=0)

        # Phase 3: Mean-center, normalize, and add to FAISS index
        count = 0
        for profile, raw_vec in raw_profiles:
            artist = profile.get("artist", "unknown")
            self._artist_centroids[artist] = raw_vec  # Store raw for later

            centered = self._center(raw_vec)
            normed = self._normalize(centered).reshape(1, -1)
            self.index.add(normed)

            self.metadata.append({
                "artist": artist,
                "type": "centroid",
                "track_count": profile.get("track_count", 0),
                "top_key": profile.get("key", {}).get("top_key", ""),
                "bpm_mean": profile.get("tempo", {}).get("bpm_mean", 0),
            })
            count += 1

        logger.info(f"Loaded {count} artist profiles from {directory} (mean-centered)")
        return count

    def add_artist(self, artist_profile: Dict[str, Any]) -> None:
        """
        Add a single artist's centroid vector to the index.
        NOTE: If mean_vector hasn't been computed yet (no batch load),
        this falls back to raw normalization without centering.
        """
        artist = artist_profile["artist"]
        centroid = np.array(artist_profile["centroid_vector"], dtype=np.float32)
        self._artist_centroids[artist] = centroid

        centered = self._center(centroid)
        normed = self._normalize(centered).reshape(1, -1)
        self.index.add(normed)

        self.metadata.append({
            "artist": artist,
            "type": "centroid",
            "track_count": artist_profile.get("track_count", 0),
            "top_key": artist_profile.get("key", {}).get("top_key", ""),
            "bpm_mean": artist_profile.get("tempo", {}).get("bpm_mean", 0),
        })
        logger.info(f"Added artist centroid: {artist} ({artist_profile.get('track_count', '?')} tracks)")

    def query(
        self, beat_vector: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the top-k most similar artists to a beat.
        The beat vector is mean-centered the same way as artist vectors.
        """
        vec = np.array(beat_vector, dtype=np.float32)
        vec = self._center(vec)
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
        # Shift to positive range, then softmax with temperature
        scores = np.array([m["similarity"] for m in matches], dtype=np.float32)
        shifted = scores - scores.min() + 0.1
        exp_scores = np.exp(shifted * 5.0)  # temperature=5 for sharper peaks
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
        Uses mean-centered vectors for proper discrimination.
        """
        artists = list(self._artist_centroids.keys())
        if len(artists) < 2:
            return {}

        vecs = np.array([
            self._normalize(self._center(self._artist_centroids[a]))
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

    def save(self, path: str) -> None:
        """Save FAISS index + metadata + mean vector to disk."""
        base = Path(path)
        base.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(base / "dna_index.faiss"))
        with open(base / "dna_metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)

        centroids = {k: v.tolist() for k, v in self._artist_centroids.items()}
        with open(base / "dna_centroids.json", "w") as f:
            json.dump(centroids, f, indent=2)

        if self._mean_vector is not None:
            with open(base / "dna_mean_vector.json", "w") as f:
                json.dump(self._mean_vector.tolist(), f)

        logger.info(f"Saved blend engine to {base} ({self.index.ntotal} vectors)")

    def load(self, path: str) -> None:
        """Load FAISS index + metadata + mean vector from disk."""
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

        mean_file = base / "dna_mean_vector.json"
        if mean_file.exists():
            with open(mean_file) as f:
                self._mean_vector = np.array(json.load(f), dtype=np.float32)
