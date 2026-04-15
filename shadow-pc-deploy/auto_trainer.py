#!/usr/bin/env python3
"""
Auto-Trainer Daemon for Type Beat Analyzer

Autonomous training pipeline that runs fingerprints + DNA + stems
for artists in a persistent queue. Zero AI/LLM tokens — pure Python.

Modes:
    --daemon       Process next N artists (for Task Scheduler, every 4h)
    --batch        Process ALL pending artists
    --discover     Find new artists via Spotify Related Artists + train them
    --dry-run      Show what would happen without doing anything
    --no-stems     Skip stem separation (faster)
    --max-artists  Limit artists per run (default: 3)
    --max-tracks   Tracks per artist (default: 15)

Usage:
    python auto_trainer.py --daemon --max-artists 3
    python auto_trainer.py --batch --artists "Drake,Future"
    python auto_trainer.py --discover --dry-run
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

# Load .env from same directory
load_dotenv(Path(__file__).parent / ".env")

# Add module directories to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "backend"))

import numpy as np
from ml.hybrid_trainer import HybridTrainer
from app.fingerprint_service_cloud_storage import CloudStorageUploader
from app.fingerprint_service import FingerprintService

# Optional heavy deps (torch/CLAP) — graceful skip on low-resource machines
try:
    from audio_dna import ArtistDNA
    HAS_ARTIST_DNA = True
except ImportError:
    HAS_ARTIST_DNA = False
    logger = logging.getLogger("auto_trainer")
    # logger not defined yet at import time, will log at runtime

try:
    from audio_dna.gcs_storage import DNAStorage
    HAS_DNA_STORAGE = True
except ImportError:
    HAS_DNA_STORAGE = False

# ── Logging ──────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("auto_trainer.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("auto_trainer")

# ── Constants ────────────────────────────────────────────────

QUEUE_PATH = Path(__file__).parent / "data" / "artist_queue.json"
LOCK_PATH = Path(__file__).parent / "auto_trainer.lock"
DNA_DIR = Path(__file__).parent / "data" / "artist_dna"
MODELS_DIR = Path(__file__).parent / "data" / "models"
METADATA_PATH = MODELS_DIR / "fingerprint_metadata.json"

MAX_RETRIES = 3
RETRY_BACKOFF_DAYS = [1, 3, 7]  # days between retries


# ── ArtistQueue ──────────────────────────────────────────────

class ArtistQueue:
    """Persistent JSON queue tracking artist training state."""

    def __init__(self, path: Path = QUEUE_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {"pending": [], "completed": [], "failed": []}
        self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path) as f:
                self.data = json.load(f)
            logger.info(
                f"Queue loaded: {len(self.data['pending'])} pending, "
                f"{len(self.data['completed'])} completed, "
                f"{len(self.data['failed'])} failed"
            )
        else:
            logger.info("No queue file found, will seed on first run")

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def _safe_name(self, name: str) -> str:
        return name.lower().replace(" ", "_").replace("/", "_")

    def _all_names(self) -> set:
        """All artist names across all lists (lowercase)."""
        names = set()
        for entry in self.data["pending"]:
            names.add(entry["name"].lower())
        for entry in self.data["completed"]:
            names.add(entry["name"].lower())
        for entry in self.data["failed"]:
            names.add(entry["name"].lower())
        return names

    def is_known(self, artist: str) -> bool:
        return artist.lower() in self._all_names()

    def add(self, artist: str, priority: int = 5, source: str = "manual"):
        """Add artist to pending queue if not already known."""
        if self.is_known(artist):
            return False
        self.data["pending"].append({
            "name": artist,
            "priority": priority,
            "source": source,
            "added_at": datetime.utcnow().isoformat(),
        })
        return True

    def next_pending(self, count: int = 1) -> List[Dict]:
        """Get next N pending artists, sorted by priority (highest first)."""
        # Also check failed artists ready for retry
        self._promote_retryable()
        pending = sorted(self.data["pending"], key=lambda x: -x.get("priority", 5))
        return pending[:count]

    def mark_completed(self, artist: str, has_fingerprints: bool = True,
                       has_dna: bool = True, has_stems: bool = False,
                       fingerprint_count: int = 0, track_count: int = 0):
        """Move artist from pending to completed."""
        self.data["pending"] = [
            e for e in self.data["pending"] if e["name"].lower() != artist.lower()
        ]
        # Update if already in completed (re-training)
        self.data["completed"] = [
            e for e in self.data["completed"] if e["name"].lower() != artist.lower()
        ]
        self.data["completed"].append({
            "name": artist,
            "has_fingerprints": has_fingerprints,
            "has_dna": has_dna,
            "has_stems": has_stems,
            "fingerprint_count": fingerprint_count,
            "track_count": track_count,
            "completed_at": datetime.utcnow().isoformat(),
        })
        self.save()

    def mark_failed(self, artist: str, error: str):
        """Move artist from pending to failed with retry tracking."""
        self.data["pending"] = [
            e for e in self.data["pending"] if e["name"].lower() != artist.lower()
        ]
        # Check if already failed before (increment retries)
        existing = None
        for entry in self.data["failed"]:
            if entry["name"].lower() == artist.lower():
                existing = entry
                break
        if existing:
            existing["retries"] = existing.get("retries", 0) + 1
            existing["last_error"] = error
            existing["last_failed_at"] = datetime.utcnow().isoformat()
            retry_idx = min(existing["retries"] - 1, len(RETRY_BACKOFF_DAYS) - 1)
            next_retry = datetime.utcnow() + timedelta(days=RETRY_BACKOFF_DAYS[retry_idx])
            existing["next_retry"] = next_retry.isoformat()
        else:
            next_retry = datetime.utcnow() + timedelta(days=RETRY_BACKOFF_DAYS[0])
            self.data["failed"].append({
                "name": artist,
                "error": error,
                "retries": 1,
                "last_failed_at": datetime.utcnow().isoformat(),
                "next_retry": next_retry.isoformat(),
            })
        self.save()

    def _promote_retryable(self):
        """Move failed artists past their retry date back to pending."""
        now = datetime.utcnow()
        still_failed = []
        for entry in self.data["failed"]:
            retries = entry.get("retries", 0)
            next_retry = entry.get("next_retry")
            if retries >= MAX_RETRIES:
                still_failed.append(entry)  # permanently failed
                continue
            if next_retry:
                retry_dt = datetime.fromisoformat(next_retry)
                if now >= retry_dt:
                    logger.info(f"Retrying previously failed artist: {entry['name']}")
                    self.data["pending"].append({
                        "name": entry["name"],
                        "priority": 3,  # lower priority for retries
                        "source": f"retry_{retries + 1}",
                        "added_at": now.isoformat(),
                    })
                else:
                    still_failed.append(entry)
            else:
                still_failed.append(entry)
        self.data["failed"] = still_failed

    def seed_from_existing(self):
        """
        Seed queue from existing fingerprint metadata and DNA profiles.
        Marks artists with existing data as completed.
        """
        # Load fingerprint metadata to find artists with fingerprints
        fp_artists: Dict[str, int] = {}
        if METADATA_PATH.exists():
            with open(METADATA_PATH) as f:
                metadata = json.load(f)
            for entry in metadata:
                artist = entry.get("artist", "")
                if artist:
                    fp_artists[artist] = fp_artists.get(artist, 0) + 1

        # Load DNA profiles
        dna_artists: set = set()
        if DNA_DIR.exists():
            for p in DNA_DIR.glob("*.json"):
                try:
                    with open(p) as f:
                        data = json.load(f)
                    dna_artists.add(data.get("artist", p.stem))
                except Exception:
                    continue

        # Check which DNA profiles have stems
        stem_artists: set = set()
        if DNA_DIR.exists():
            for p in DNA_DIR.glob("*.json"):
                try:
                    with open(p) as f:
                        data = json.load(f)
                    if data.get("stems"):
                        stem_artists.add(data.get("artist", p.stem))
                except Exception:
                    continue

        # Mark existing artists as completed
        added = 0
        for artist, fp_count in fp_artists.items():
            if not self.is_known(artist):
                has_dna = artist in dna_artists
                has_stems = artist in stem_artists
                self.data["completed"].append({
                    "name": artist,
                    "has_fingerprints": True,
                    "has_dna": has_dna,
                    "has_stems": has_stems,
                    "fingerprint_count": fp_count,
                    "track_count": 0,
                    "completed_at": "seeded",
                })
                added += 1

        # DNA-only artists (no fingerprints yet)
        for artist in dna_artists:
            if not self.is_known(artist) and artist not in fp_artists:
                self.data["completed"].append({
                    "name": artist,
                    "has_fingerprints": False,
                    "has_dna": True,
                    "has_stems": artist in stem_artists,
                    "fingerprint_count": 0,
                    "track_count": 0,
                    "completed_at": "seeded",
                })
                added += 1

        self.save()
        logger.info(f"Seeded {added} artists from existing data")
        return added

    def get_incomplete(self) -> List[Dict]:
        """Get completed artists missing DNA or stems for re-training."""
        incomplete = []
        for entry in self.data["completed"]:
            if not entry.get("has_dna") or not entry.get("has_stems"):
                incomplete.append(entry)
        return incomplete

    def stats(self) -> Dict:
        pending = len(self.data["pending"])
        completed = len(self.data["completed"])
        failed = len(self.data["failed"])
        with_dna = sum(1 for e in self.data["completed"] if e.get("has_dna"))
        with_stems = sum(1 for e in self.data["completed"] if e.get("has_stems"))
        with_fp = sum(1 for e in self.data["completed"] if e.get("has_fingerprints"))
        return {
            "pending": pending,
            "completed": completed,
            "failed": failed,
            "with_fingerprints": with_fp,
            "with_dna": with_dna,
            "with_stems": with_stems,
            "total_known": pending + completed + failed,
        }


# ── ArtistDiscoverer ─────────────────────────────────────────

class ArtistDiscoverer:
    """Discover new artists via Spotify Related Artists API."""

    # Hip-hop/R&B/Pop genre whitelist (Spotify genre tags)
    GENRE_WHITELIST = {
        "rap", "hip hop", "trap", "drill", "r&b", "pop", "latin",
        "reggaeton", "afrobeats", "uk rap", "plugg", "rage",
        "melodic rap", "southern hip hop", "conscious hip hop",
        "gangster rap", "west coast rap", "east coast hip hop",
        "chicago rap", "detroit hip hop", "atlanta hip hop",
        "underground hip hop", "alternative r&b",
    }

    def __init__(self):
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET required for discovery")

        self.sp = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )

    def _search_artist_id(self, name: str) -> Optional[str]:
        """Find Spotify artist ID by name."""
        try:
            results = self.sp.search(q=f"artist:{name}", type="artist", limit=1)
            items = results.get("artists", {}).get("items", [])
            if items:
                return items[0]["id"]
        except Exception as e:
            logger.warning(f"Spotify search failed for {name}: {e}")
        return None

    def _is_relevant_genre(self, genres: List[str]) -> bool:
        """Check if artist's genres overlap with our whitelist."""
        for genre in genres:
            genre_lower = genre.lower()
            for allowed in self.GENRE_WHITELIST:
                if allowed in genre_lower:
                    return True
        return False

    def discover_related(self, artist: str, max_related: int = 5) -> List[str]:
        """Get related artists from Spotify."""
        artist_id = self._search_artist_id(artist)
        if not artist_id:
            return []

        try:
            related = self.sp.artist_related_artists(artist_id)
            results = []
            for item in related.get("artists", []):
                if self._is_relevant_genre(item.get("genres", [])):
                    results.append(item["name"])
                    if len(results) >= max_related:
                        break
            return results
        except Exception as e:
            logger.warning(f"Related artists lookup failed for {artist}: {e}")
            return []

    def discover_from_all_completed(self, queue: ArtistQueue,
                                     max_per_artist: int = 5,
                                     max_total: int = 50) -> List[str]:
        """Discover related artists for all completed artists in queue."""
        discovered = []
        for entry in queue.data["completed"]:
            if len(discovered) >= max_total:
                break
            artist = entry["name"]
            related = self.discover_related(artist, max_related=max_per_artist)
            for r in related:
                if not queue.is_known(r) and r not in discovered:
                    discovered.append(r)
                    if len(discovered) >= max_total:
                        break
            time.sleep(0.3)  # rate limit

        return discovered


# ── FullTrainer ──────────────────────────────────────────────

class FullTrainer:
    """
    Orchestrates the full training pipeline:
    download → fingerprint → DNA → stems → GCS upload → cleanup
    """

    def __init__(self, enable_stems: bool = True, max_tracks: int = 15):
        self.enable_stems = enable_stems
        self.max_tracks = max_tracks

        # Initialize shared components
        self.trainer = HybridTrainer(
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        )
        self.uploader = CloudStorageUploader()
        self.dna_storage = DNAStorage() if HAS_DNA_STORAGE else None

    def train_artist(self, artist: str, queue: ArtistQueue) -> bool:
        """
        Full pipeline for one artist. Returns True on success.

        Steps:
        1. Download audio (yt-dlp)
        2. Generate fingerprints (FAISS)
        3. Build DNA profile (no stems)
        4. Build DNA profile with stems (if enabled)
        5. Upload all to GCS
        6. Trigger Cloud Run refresh
        7. Clean up audio files
        """
        t0 = time.perf_counter()
        logger.info(f"{'=' * 60}")
        logger.info(f"FULL TRAINING: {artist}")
        logger.info(f"{'=' * 60}")

        audio_files: List[str] = []
        fingerprint_count = 0
        has_dna = False
        has_stems = False

        try:
            # ── Step 1: Download audio ──
            logger.info(f"[1/7] Downloading up to {self.max_tracks} tracks...")
            audio_files = self.trainer.download_from_youtube(artist, max_videos=self.max_tracks)
            if not audio_files:
                raise RuntimeError(f"No tracks downloaded for {artist}")
            logger.info(f"Downloaded {len(audio_files)} tracks")

            # ── Step 2: Generate fingerprints ──
            logger.info(f"[2/7] Generating fingerprints...")
            fingerprint_count = self._train_fingerprints(artist, audio_files)
            logger.info(f"Generated {fingerprint_count} fingerprints")

            # ── Step 3: Build DNA profile (no stems — fast) ──
            dna_profile = None
            if not HAS_ARTIST_DNA:
                logger.info(f"[3/7] Skipping DNA (audio_dna not available — torch missing?)")
            else:
                logger.info(f"[3/7] Building DNA profile...")
                try:
                    dna_builder = ArtistDNA(enable_stems=False)
                    dna_profile = dna_builder.build_artist_profile(audio_files, artist, save=True)
                    has_dna = True
                    logger.info(
                        f"DNA: {dna_profile['track_count']} tracks, "
                        f"BPM {dna_profile['tempo'].get('bpm_mean', '?')}, "
                        f"Key {dna_profile['key']['top_key']}"
                    )
                except Exception as e:
                    logger.warning(f"DNA profiling failed: {e}")

            # ── Step 4: Stem separation (if enabled) ──
            if not HAS_ARTIST_DNA:
                logger.info(f"[4/7] Skipping stems (audio_dna not available)")
            elif self.enable_stems:
                logger.info(f"[4/7] Running stem separation (this takes a while)...")
                try:
                    stem_builder = ArtistDNA(enable_stems=True)
                    stem_profile = stem_builder.build_artist_profile(audio_files, artist, save=True)
                    has_stems = True
                    logger.info(f"Stems complete: {stem_profile.get('stems', {})}")
                except Exception as e:
                    logger.warning(f"Stem separation failed: {e}")
            else:
                logger.info(f"[4/7] Skipping stems (--no-stems)")

            # ── Step 5: Upload to GCS ──
            logger.info(f"[5/7] Uploading to GCS...")
            self._upload_all(artist, dna_profile if has_dna else None)

            # ── Step 6: Trigger Cloud Run refresh ──
            logger.info(f"[6/7] Triggering Cloud Run refresh...")
            self._trigger_refresh()

            # ── Step 7: Cleanup ──
            logger.info(f"[7/7] Cleaning up audio files...")
            self._cleanup(audio_files)

            elapsed = time.perf_counter() - t0
            logger.info(
                f"COMPLETE: {artist} — {fingerprint_count} fingerprints, "
                f"DNA={'yes' if has_dna else 'no'}, "
                f"stems={'yes' if has_stems else 'no'}, "
                f"{elapsed:.0f}s total"
            )

            queue.mark_completed(
                artist,
                has_fingerprints=fingerprint_count > 0,
                has_dna=has_dna,
                has_stems=has_stems,
                fingerprint_count=fingerprint_count,
                track_count=len(audio_files),
            )
            return True

        except Exception as e:
            logger.error(f"FAILED: {artist} — {e}")
            queue.mark_failed(artist, str(e)[:200])
            self._cleanup(audio_files)
            return False

    def _train_fingerprints(self, artist: str, audio_files: List[str]) -> int:
        """Generate fingerprints and add to local FAISS index."""
        # Download current FAISS index from GCS
        self._download_faiss_from_gcs()
        fp_service = FingerprintService()
        initial_count = fp_service.index.ntotal

        count = 0
        for i, audio_file in enumerate(audio_files, 1):
            try:
                fingerprint = fp_service._generate_fingerprint(audio_file, duration=None)
                if fingerprint is not None:
                    embedding = np.array(fingerprint, dtype=np.float32).reshape(1, -1)
                    fp_service.index.add(embedding)
                    fp_service.metadata.append({
                        "id": fp_service.id_counter,
                        "artist": artist,
                        "title": Path(audio_file).stem,
                        "audio_hash": f"auto_trainer_{artist}_{fp_service.id_counter}",
                        "upload_date": datetime.now().isoformat(),
                        "uploader_id": "auto_trainer",
                    })
                    fp_service.id_counter += 1
                    count += 1
            except Exception as e:
                logger.warning(f"Fingerprint failed for {Path(audio_file).name}: {e}")

        if count > 0:
            fp_service._save_index()
            logger.info(f"FAISS index: {initial_count} → {fp_service.index.ntotal} fingerprints")

        return count

    def _download_faiss_from_gcs(self):
        """Download current FAISS index from GCS to local data/models/."""
        from google.cloud import storage as gcs

        bucket_name = os.getenv("FINGERPRINT_BUCKET_NAME", "type-beat-fingerprints")
        local_dir = MODELS_DIR
        local_dir.mkdir(parents=True, exist_ok=True)

        try:
            client = gcs.Client()
            bucket = client.bucket(bucket_name)
            for fname in ["fingerprint_index.faiss", "fingerprint_metadata.json"]:
                blob = bucket.blob(f"models/{fname}")
                if blob.exists():
                    blob.download_to_filename(str(local_dir / fname))
            logger.info("Downloaded FAISS index from GCS")
        except Exception as e:
            logger.warning(f"Could not download from GCS (using local): {e}")

    def _upload_all(self, artist: str, dna_profile: Optional[Dict] = None):
        """Upload FAISS index + DNA profile to GCS."""
        # Upload FAISS index
        local_index = MODELS_DIR / "fingerprint_index.faiss"
        local_metadata = MODELS_DIR / "fingerprint_metadata.json"
        if local_index.exists() and local_metadata.exists():
            from google.cloud import storage as gcs

            bucket_name = os.getenv("FINGERPRINT_BUCKET_NAME", "type-beat-fingerprints")
            client = gcs.Client()
            bucket = client.bucket(bucket_name)
            bucket.blob("models/fingerprint_index.faiss").upload_from_filename(str(local_index))
            bucket.blob("models/fingerprint_metadata.json").upload_from_filename(str(local_metadata))
            logger.info("Uploaded FAISS index + metadata to GCS")

        # Upload DNA profile
        if dna_profile and self.dna_storage:
            try:
                self.dna_storage.upload_artist_profile(dna_profile)
                logger.info(f"Uploaded DNA profile for {artist} to GCS")
            except Exception as e:
                logger.warning(f"DNA GCS upload failed: {e}")

    def _trigger_refresh(self):
        """Tell Cloud Run to reload fingerprints."""
        import requests

        cloud_run_url = os.getenv(
            "CLOUD_RUN_URL",
            "https://type-beat-backend-287783957820.us-central1.run.app",
        )
        try:
            resp = requests.post(f"{cloud_run_url}/api/fingerprint/refresh", timeout=30)
            if resp.status_code == 200:
                logger.info(f"Cloud Run refresh triggered: {resp.json()}")
            else:
                logger.warning(f"Cloud Run refresh returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"Could not trigger Cloud Run refresh: {e}")

    def _cleanup(self, audio_files: List[str]):
        """Remove downloaded audio files and temp directories."""
        dirs_to_remove = set()
        for f in audio_files:
            p = Path(f)
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass
            if p.parent.name.startswith("typebeat_"):
                dirs_to_remove.add(p.parent)

        for d in dirs_to_remove:
            try:
                if d.exists():
                    shutil.rmtree(d)
            except Exception:
                pass


# ── Lock File ────────────────────────────────────────────────

class LockFile:
    """Prevent overlapping Task Scheduler runs."""

    def __init__(self, path: Path = LOCK_PATH):
        self.path = path
        self._fd = None

    def acquire(self) -> bool:
        try:
            self._fd = open(self.path, "w")
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(self._fd.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._fd.write(str(os.getpid()))
            self._fd.flush()
            return True
        except (OSError, IOError):
            logger.warning("Another auto_trainer instance is already running (lock file held)")
            if self._fd:
                self._fd.close()
                self._fd = None
            return False

    def release(self):
        if self._fd:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    self._fd.seek(0)
                    msvcrt.locking(self._fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
                self._fd.close()
            except Exception:
                pass
            try:
                self.path.unlink(missing_ok=True)
            except Exception:
                pass
            self._fd = None


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Auto-Trainer Daemon for Type Beat Analyzer"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--daemon", action="store_true",
                      help="Process next N artists (for Task Scheduler)")
    mode.add_argument("--batch", action="store_true",
                      help="Process ALL pending artists")
    mode.add_argument("--discover", action="store_true",
                      help="Find new artists via Spotify + train them")
    mode.add_argument("--stats", action="store_true",
                      help="Show queue statistics")
    mode.add_argument("--seed", action="store_true",
                      help="Seed queue from existing data (run once)")
    mode.add_argument("--retrain-stems", action="store_true",
                      help="Re-train completed artists that are missing stems")

    parser.add_argument("--artists", type=str, default=None,
                        help="Comma-separated artist names (for --batch)")
    parser.add_argument("--max-artists", type=int, default=3,
                        help="Max artists per run (default: 3)")
    parser.add_argument("--max-tracks", type=int, default=15,
                        help="Tracks per artist (default: 15)")
    parser.add_argument("--no-stems", action="store_true",
                        help="Skip stem separation (faster)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without doing anything")

    args = parser.parse_args()

    # ── Initialize queue ──
    queue = ArtistQueue()

    # Seed if queue is empty
    if not queue.data["pending"] and not queue.data["completed"] and not queue.data["failed"]:
        logger.info("Queue is empty, seeding from existing data...")
        queue.seed_from_existing()

    # ── Stats mode ──
    if args.stats:
        s = queue.stats()
        print(f"\n{'=' * 50}")
        print(f"  Auto-Trainer Queue Stats")
        print(f"{'=' * 50}")
        print(f"  Pending:          {s['pending']}")
        print(f"  Completed:        {s['completed']}")
        print(f"  Failed:           {s['failed']}")
        print(f"  With Fingerprints:{s['with_fingerprints']}")
        print(f"  With DNA:         {s['with_dna']}")
        print(f"  With Stems:       {s['with_stems']}")
        print(f"  Total Known:      {s['total_known']}")
        print(f"{'=' * 50}\n")

        incomplete = queue.get_incomplete()
        if incomplete:
            print(f"  Incomplete artists ({len(incomplete)}):")
            for e in incomplete[:10]:
                missing = []
                if not e.get("has_dna"):
                    missing.append("DNA")
                if not e.get("has_stems"):
                    missing.append("stems")
                print(f"    {e['name']}: missing {', '.join(missing)}")
            if len(incomplete) > 10:
                print(f"    ... and {len(incomplete) - 10} more")
        return

    # ── Seed mode ──
    if args.seed:
        count = queue.seed_from_existing()
        print(f"Seeded {count} artists from existing data")
        s = queue.stats()
        print(f"Queue: {s['completed']} completed, {s['pending']} pending")
        return

    # ── Discover mode ──
    if args.discover:
        logger.info("Discovering new artists via Spotify Related Artists...")
        discoverer = ArtistDiscoverer()
        new_artists = discoverer.discover_from_all_completed(
            queue, max_per_artist=5, max_total=args.max_artists * 5
        )

        if args.dry_run:
            print(f"\n[DRY RUN] Would discover {len(new_artists)} new artists:")
            for a in new_artists:
                print(f"  + {a}")
            return

        added = 0
        for artist in new_artists:
            if queue.add(artist, priority=5, source="spotify_related"):
                added += 1
        queue.save()
        logger.info(f"Added {added} new artists to queue")

        if added == 0:
            logger.info("No new artists discovered. Queue is saturated.")
            return

        # Fall through to train discovered artists
        # Get the newly added pending artists
        args.daemon = False
        args.batch = True

    # ── Retrain stems mode ──
    if args.retrain_stems:
        incomplete = [
            e for e in queue.get_incomplete()
            if not e.get("has_stems") and e.get("has_fingerprints")
        ]
        if not incomplete:
            print("All completed artists already have stems.")
            return

        artists_to_train = [e["name"] for e in incomplete[:args.max_artists]]

        if args.dry_run:
            print(f"\n[DRY RUN] Would retrain stems for {len(artists_to_train)} artists:")
            for a in artists_to_train:
                print(f"  ~ {a}")
            return

        # Move them back to pending for re-training
        for name in artists_to_train:
            queue.data["completed"] = [
                e for e in queue.data["completed"] if e["name"].lower() != name.lower()
            ]
            queue.add(name, priority=4, source="retrain_stems")
        queue.save()
        # Fall through to batch training
        args.batch = True
        args.no_stems = False  # force stems on

    # ── Acquire lock ──
    lock = LockFile()
    if not lock.acquire():
        logger.error("Could not acquire lock. Another instance may be running.")
        sys.exit(1)

    try:
        # ── Determine artists to train ──
        if args.batch and args.artists:
            # Explicit artist list
            artist_names = [a.strip() for a in args.artists.split(",")]
            for name in artist_names:
                queue.add(name, priority=10, source="manual_batch")
            queue.save()
            to_train = queue.next_pending(count=len(artist_names))
        elif args.batch:
            to_train = queue.next_pending(count=999)
        else:  # daemon mode
            to_train = queue.next_pending(count=args.max_artists)

        if not to_train:
            logger.info("No pending artists to train.")
            return

        if args.dry_run:
            print(f"\n[DRY RUN] Would train {len(to_train)} artists:")
            for entry in to_train:
                print(f"  → {entry['name']} (priority: {entry.get('priority', 5)}, source: {entry.get('source', '?')})")
            s = queue.stats()
            print(f"\nQueue: {s['pending']} pending, {s['completed']} completed, {s['failed']} failed")
            return

        # ── Train ──
        enable_stems = not args.no_stems
        full_trainer = FullTrainer(enable_stems=enable_stems, max_tracks=args.max_tracks)

        successes = 0
        failures = 0
        for i, entry in enumerate(to_train, 1):
            artist = entry["name"]
            logger.info(f"\n[{i}/{len(to_train)}] Training: {artist}")
            ok = full_trainer.train_artist(artist, queue)
            if ok:
                successes += 1
            else:
                failures += 1
            time.sleep(2)  # brief pause between artists

        # ── Summary ──
        logger.info(f"\n{'=' * 50}")
        logger.info(f"AUTO-TRAINER RUN COMPLETE")
        logger.info(f"  Success: {successes}")
        logger.info(f"  Failed:  {failures}")
        s = queue.stats()
        logger.info(f"  Queue:   {s['pending']} pending, {s['completed']} completed, {s['failed']} failed")
        logger.info(f"  DNA:     {s['with_dna']}, Stems: {s['with_stems']}")
        logger.info(f"{'=' * 50}")

    finally:
        lock.release()


if __name__ == "__main__":
    main()
