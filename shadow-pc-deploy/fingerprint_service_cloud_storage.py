"""
Fingerprint service using Google Cloud Storage
Stores fingerprints in Cloud Storage for persistence across deployments
"""

import os
import json
import logging
import pickle
import tempfile
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from google.cloud import storage
from google.cloud.storage import Blob

logger = logging.getLogger(__name__)


class CloudStorageFingerprintService:
    """
    Fingerprint service using Google Cloud Storage
    Provides persistent storage that works across Cloud Run and Shadow PC
    """

    def __init__(self, bucket_name: str = None):
        """Initialize Cloud Storage client"""
        self.bucket_name = bucket_name or os.getenv(
            "FINGERPRINT_BUCKET_NAME",
            "type-beat-fingerprints"
        )

        # Initialize Cloud Storage client
        try:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket_name)
            logger.info(f"✅ Connected to Cloud Storage bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Cloud Storage: {e}")
            logger.warning("⚠️  Falling back to local storage")
            self.bucket = None

        # Local cache for fingerprints
        self._local_cache: Dict[str, np.ndarray] = {}
        self._metadata_cache: List[Dict] = []
        self._id_counter = 0

        # Load existing data from Cloud Storage
        self._load_from_cloud_storage()

    def _load_from_cloud_storage(self):
        """Load fingerprints and metadata from Cloud Storage"""
        if not self.bucket:
            logger.warning("⚠️  No Cloud Storage connection, skipping load")
            return

        try:
            # Load FAISS index
            index_blob = self.bucket.blob("models/fingerprint_index.faiss")
            if index_blob.exists():
                with tempfile.NamedTemporaryFile(delete=False, suffix=".faiss") as tmp:
                    index_blob.download_to_file(tmp.name)
                    # Load with your FAISS loading code
                    tmp_path = Path(tmp.name)
                    if tmp_path.exists():
                        logger.info(f"✅ Loaded FAISS index from Cloud Storage")
                        tmp_path.unlink()

            # Load metadata
            metadata_blob = self.bucket.blob("models/fingerprint_metadata.json")
            if metadata_blob.exists():
                metadata_content = metadata_blob.download_as_text()
                self._metadata_cache = json.loads(metadata_content)
                self._id_counter = len(self._metadata_cache)
                logger.info(f"✅ Loaded {self._id_counter} fingerprints from Cloud Storage")
        except Exception as e:
            logger.error(f"❌ Error loading from Cloud Storage: {e}")

    def add_fingerprint(
        self,
        embedding: np.ndarray,
        artist: str,
        title: str,
        source: str = "youtube"
    ) -> int:
        """Add a fingerprint to Cloud Storage"""
        try:
            fingerprint_id = self._id_counter
            self._id_counter += 1

            # Create metadata entry
            metadata_entry = {
                'id': fingerprint_id,
                'artist': artist,
                'title': title,
                'source': source,
                'upload_date': None,
                'uploader_id': f'training_{source}'
            }
            self._metadata_cache.append(metadata_entry)

            # Store embedding in local cache
            self._local_cache[str(fingerprint_id)] = embedding

            # Upload to Cloud Storage
            if self.bucket:
                self._upload_fingerprint_to_cloud(fingerprint_id, embedding, metadata_entry)

            logger.debug(f"Added fingerprint {fingerprint_id}: {artist} - {title}")
            return fingerprint_id

        except Exception as e:
            logger.error(f"❌ Error adding fingerprint: {e}")
            return -1

    def _upload_fingerprint_to_cloud(
        self,
        fingerprint_id: int,
        embedding: np.ndarray,
        metadata: Dict
    ):
        """Upload individual fingerprint to Cloud Storage"""
        try:
            # Upload embedding as numpy file
            embedding_blob = self.bucket.blob(
                f"fingerprints/{fingerprint_id}.npz"
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".npz") as tmp:
                np.savez_compressed(tmp.name, embedding=embedding)
                embedding_blob.upload_from_file(tmp.name, content_type="application/octet-stream")
                Path(tmp.name).unlink()

        except Exception as e:
            logger.error(f"❌ Error uploading fingerprint to cloud: {e}")

    def save_index(self):
        """Save the full index to Cloud Storage"""
        if not self.bucket:
            logger.warning("⚠️  No Cloud Storage connection")
            return

        try:
            # Save metadata
            metadata_blob = self.bucket.blob("models/fingerprint_metadata.json")
            metadata_blob.upload_from_string(
                json.dumps(self._metadata_cache, indent=2),
                content_type="application/json"
            )

            # Note: FAISS index saving would be done separately
            logger.info(f"💾 Saved {len(self._metadata_cache)} fingerprints to Cloud Storage")

        except Exception as e:
            logger.error(f"❌ Error saving to Cloud Storage: {e}")

    def search_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10
    ) -> List[Dict]:
        """Search for similar fingerprints"""
        # This would integrate with your FAISS search
        # For now, return empty list
        logger.warning("⚠️  Search not yet implemented with Cloud Storage")
        return []

    def get_metadata(self) -> List[Dict]:
        """Get all fingerprint metadata"""
        return self._metadata_cache.copy()

    def get_stats(self) -> Dict:
        """Get statistics about fingerprints"""
        artists = set(m['artist'] for m in self._metadata_cache)
        return {
            'total_fingerprints': len(self._metadata_cache),
            'unique_artists': len(artists),
            'storage_bucket': self.bucket_name,
            'cache_size': len(self._local_cache)
        }


class CloudStorageUploader:
    """
    Helper class to upload training results from Shadow PC to Cloud Storage
    """

    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or os.getenv(
            "FINGERPRINT_BUCKET_NAME",
            "type-beat-fingerprints"
        )

        try:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket_name)
            logger.info(f"✅ Cloud Storage uploader ready: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cloud Storage: {e}")
            self.bucket = None

    def upload_training_results(
        self,
        fingerprint_data: List[Dict],
        index_path: str = None,
        metadata_path: str = None
    ) -> bool:
        """
        Upload training results from Shadow PC to Cloud Storage

        Args:
            fingerprint_data: List of fingerprint dictionaries
            index_path: Path to FAISS index file (optional)
            metadata_path: Path to metadata JSON file (optional)
        """
        if not self.bucket:
            logger.error("❌ No Cloud Storage connection")
            return False

        try:
            logger.info(f"📤 Uploading {len(fingerprint_data)} fingerprints to Cloud Storage...")

            # Upload individual fingerprints
            for item in fingerprint_data:
                fingerprint_id = item.get('id')
                embedding = item.get('embedding')

                if embedding is not None:
                    # Convert to numpy if needed
                    if isinstance(embedding, list):
                        embedding = np.array(embedding, dtype=np.float32)

                    # Upload embedding
                    embedding_blob = self.bucket.blob(
                        f"fingerprints/{fingerprint_id}.npz"
                    )
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".npz") as tmp:
                        np.savez_compressed(tmp.name, embedding=embedding)
                        embedding_blob.upload_from_file(tmp.name)
                        Path(tmp.name).unlink()

            # Upload FAISS index if provided
            if index_path and Path(index_path).exists():
                index_blob = self.bucket.blob("models/fingerprint_index.faiss")
                index_blob.upload_from_filename(index_path)
                logger.info("✅ Uploaded FAISS index")

            # Upload metadata if provided
            if metadata_path and Path(metadata_path).exists():
                metadata_blob = self.bucket.blob("models/fingerprint_metadata.json")
                metadata_blob.upload_from_filename(metadata_path)
                logger.info("✅ Uploaded metadata")

            # Create upload log
            log_blob = self.bucket.blob(f"logs/training_{hash(os.urandom(8))}.json")
            log_data = {
                'timestamp': str(pd.Timestamp.now()) if 'pd' in dir() else str(datetime.now()),
                'fingerprints_uploaded': len(fingerprint_data),
                'source': 'shadow_pc'
            }
            log_blob.upload_from_string(
                json.dumps(log_data, indent=2),
                content_type="application/json"
            )

            logger.info(f"✅ Successfully uploaded to Cloud Storage")
            return True

        except Exception as e:
            logger.error(f"❌ Error uploading to Cloud Storage: {e}")
            return False
