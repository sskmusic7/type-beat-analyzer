"""
DnaService — Cloud Run native DNA inference service.

Downloads artist DNA profiles from GCS on startup, loads them into
a BlendEngine for similarity search, and provides inference methods
for the /api/dna/* endpoints.

Singleton pattern: one instance per Cloud Run container.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DnaService:
    """
    Manages artist DNA profiles and runs inference locally on Cloud Run.

    On init:
    1. Downloads all artist DNA profiles from GCS to a temp directory
    2. Loads them into a BlendEngine via add_artists_from_dir()
    3. Caches in memory for the lifetime of the container

    NOTE: CLAPScorer downloads a ~600MB model on first use (cold start).
    Subsequent requests reuse the cached model.
    """

    _instance: Optional["DnaService"] = None

    def __init__(self):
        self._temp_dir: Optional[str] = None
        self._engine = None
        self._artist_profiles: List[Dict[str, Any]] = []
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "DnaService":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self) -> None:
        """
        Download artist profiles from GCS and build the FAISS index.
        Call this once at startup.
        """
        if self._initialized:
            return

        from audio_dna import BlendEngine

        logger.info("Initializing DnaService: downloading artist profiles from GCS...")

        # Create temp directory for artist profiles
        self._temp_dir = tempfile.mkdtemp(prefix="dna_artists_")
        profiles_dir = Path(self._temp_dir)

        # Download all artist DNA profiles from GCS
        count = self._download_profiles_from_gcs(profiles_dir)
        logger.info(f"Downloaded {count} artist DNA profiles from GCS")

        # Load into BlendEngine
        self._engine = BlendEngine()
        if count > 0:
            loaded = self._engine.add_artists_from_dir(str(profiles_dir))
            logger.info(f"Loaded {loaded} artist profiles into BlendEngine")
        else:
            logger.warning("No artist DNA profiles found in GCS")

        # Cache artist metadata for the /artists endpoint
        self._load_artist_metadata(profiles_dir)

        self._initialized = True
        logger.info(f"DnaService initialized: {self._engine.index.ntotal} artists in FAISS index")

    def _download_profiles_from_gcs(self, local_dir: Path) -> int:
        """Download all artist DNA JSON files from GCS."""
        try:
            from google.cloud import storage
            import os

            bucket_name = os.getenv("FINGERPRINT_BUCKET_NAME", "type-beat-fingerprints")
            client = storage.Client()
            bucket = client.bucket(bucket_name)

            count = 0
            prefix = "dna/artists/"
            blobs = bucket.list_blobs(prefix=prefix)

            for blob in blobs:
                if not blob.name.endswith(".json"):
                    continue
                filename = blob.name.split("/")[-1]
                if filename.startswith("_"):
                    continue
                local_path = local_dir / filename
                blob.download_to_filename(str(local_path))
                count += 1

            return count
        except Exception as e:
            logger.error(f"Failed to download DNA profiles from GCS: {e}")
            return 0

    def _load_artist_metadata(self, profiles_dir: Path) -> None:
        """Load artist metadata from downloaded JSON files."""
        self._artist_profiles = []
        for p in sorted(profiles_dir.glob("*.json")):
            if p.stem.startswith("_"):
                continue
            try:
                with open(p) as f:
                    data = json.load(f)
                self._artist_profiles.append({
                    "artist": data.get("artist", p.stem),
                    "track_count": data.get("track_count", 0),
                    "bpm_mean": data.get("tempo", {}).get("bpm_mean"),
                    "top_key": data.get("key", {}).get("top_key"),
                })
            except Exception:
                continue

    def get_artists(self) -> Dict[str, Any]:
        """Return list of artist metadata."""
        return {"artists": self._artist_profiles}

    def get_similarity_matrix(self) -> Dict[str, Any]:
        """Compute and return artist-to-artist similarity matrix."""
        if not self._engine or self._engine.index.ntotal < 2:
            return {"artists": [], "matrix": [], "pairs": [], "top_pairs": []}

        raw = self._engine.artist_similarity_matrix()
        artists = sorted(raw.keys())

        # Build 2D matrix
        matrix = []
        for a in artists:
            row = []
            for b in artists:
                if a == b:
                    row.append(1.0)
                else:
                    row.append(raw.get(a, {}).get(b, 0.0))
            matrix.append(row)

        # Build sorted pairs list
        pairs = []
        seen = set()
        for a in artists:
            for b in artists:
                if a != b and (b, a) not in seen:
                    seen.add((a, b))
                    pairs.append({
                        "artist_a": a,
                        "artist_b": b,
                        "similarity": raw.get(a, {}).get(b, 0.0),
                    })
        pairs.sort(key=lambda p: -p["similarity"])
        top_pairs = pairs[:50]

        return {"artists": artists, "matrix": matrix, "pairs": pairs, "top_pairs": top_pairs}

    def blend_audio(self, file_path: str) -> Dict[str, Any]:
        """
        Run AudioDNA profiling + BlendEngine blend on an audio file.

        Returns the full blend result with beat_profile, matching the
        response format from Shadow PC's /dna/blend-upload endpoint.
        """
        if not self._engine or self._engine.index.ntotal == 0:
            raise ValueError("No artist profiles loaded. Train artists first.")

        from audio_dna import AudioDNA

        dna = AudioDNA(enable_stems=False)
        profile = dna.profile_fast(file_path)
        vector = dna.to_vector(profile)
        result = self._engine.blend(vector, top_k=5)

        # Add beat_profile to match Shadow PC response format
        result["beat_profile"] = {
            "bpm": profile.get("features", {}).get("tempo", {}).get("bpm"),
            "key": profile.get("features", {}).get("key", {}).get("key_label"),
            "top_tags": [t["tag"] for t in profile.get("clap_tags", [])[:5]],
        }

        return result
