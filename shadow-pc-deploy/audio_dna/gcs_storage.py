"""
GCS Storage for AudioDNA profiles — Phase 7

Stores and retrieves artist DNA profiles and blend engine indexes
from Google Cloud Storage alongside existing fingerprints.

Bucket structure:
    gs://type-beat-fingerprints/
        models/fingerprint_index.faiss    (existing)
        models/fingerprint_metadata.json  (existing)
        dna/artists/{artist_name}.json    (artist DNA profiles)
        dna/index/dna_index.faiss         (blend engine FAISS index)
        dna/index/dna_metadata.json       (blend engine metadata)
        dna/index/dna_centroids.json      (artist centroids)
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DNAStorage:
    """
    Upload/download AudioDNA artifacts to/from Google Cloud Storage.
    """

    def __init__(self, bucket_name: str = "type-beat-fingerprints"):
        self.bucket_name = bucket_name
        self._client = None
        self._bucket = None

    def _ensure_client(self):
        if self._client is not None:
            return
        from google.cloud import storage
        self._client = storage.Client()
        self._bucket = self._client.bucket(self.bucket_name)
        logger.info(f"Connected to GCS bucket: {self.bucket_name}")

    def upload_artist_profile(self, profile: Dict[str, Any]) -> str:
        """Upload an artist DNA profile to GCS."""
        self._ensure_client()
        artist = profile["artist"]
        safe_name = artist.lower().replace(" ", "_").replace("/", "_")
        blob_path = f"dna/artists/{safe_name}.json"

        blob = self._bucket.blob(blob_path)
        blob.upload_from_string(
            json.dumps(profile, indent=2),
            content_type="application/json",
        )
        logger.info(f"Uploaded artist DNA: gs://{self.bucket_name}/{blob_path}")
        return blob_path

    def download_artist_profile(self, artist: str) -> Optional[Dict[str, Any]]:
        """Download an artist DNA profile from GCS."""
        self._ensure_client()
        safe_name = artist.lower().replace(" ", "_").replace("/", "_")
        blob_path = f"dna/artists/{safe_name}.json"

        blob = self._bucket.blob(blob_path)
        if not blob.exists():
            return None

        data = blob.download_as_text()
        return json.loads(data)

    def list_artist_profiles(self) -> List[str]:
        """List all artist DNA profiles in GCS."""
        self._ensure_client()
        blobs = self._bucket.list_blobs(prefix="dna/artists/")
        artists = []
        for blob in blobs:
            if blob.name.endswith(".json"):
                name = Path(blob.name).stem
                artists.append(name)
        return artists

    def upload_blend_index(self, local_dir: str) -> None:
        """Upload blend engine FAISS index + metadata to GCS."""
        self._ensure_client()
        local = Path(local_dir)

        for filename in ["dna_index.faiss", "dna_metadata.json", "dna_centroids.json"]:
            local_file = local / filename
            if local_file.exists():
                blob_path = f"dna/index/{filename}"
                blob = self._bucket.blob(blob_path)
                blob.upload_from_filename(str(local_file))
                logger.info(f"Uploaded: gs://{self.bucket_name}/{blob_path}")

    def download_blend_index(self, local_dir: str) -> bool:
        """Download blend engine index from GCS to local directory."""
        self._ensure_client()
        local = Path(local_dir)
        local.mkdir(parents=True, exist_ok=True)

        downloaded = False
        for filename in ["dna_index.faiss", "dna_metadata.json", "dna_centroids.json"]:
            blob_path = f"dna/index/{filename}"
            blob = self._bucket.blob(blob_path)
            if blob.exists():
                blob.download_to_filename(str(local / filename))
                logger.info(f"Downloaded: gs://{self.bucket_name}/{blob_path}")
                downloaded = True

        return downloaded

    def sync_all_profiles_to_local(self, local_dir: str) -> int:
        """Download all artist profiles from GCS to local directory."""
        self._ensure_client()
        local = Path(local_dir)
        local.mkdir(parents=True, exist_ok=True)

        count = 0
        blobs = self._bucket.list_blobs(prefix="dna/artists/")
        for blob in blobs:
            if blob.name.endswith(".json"):
                local_file = local / Path(blob.name).name
                blob.download_to_filename(str(local_file))
                count += 1

        logger.info(f"Synced {count} artist profiles from GCS to {local}")
        return count
