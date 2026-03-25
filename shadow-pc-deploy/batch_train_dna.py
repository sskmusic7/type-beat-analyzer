#!/usr/bin/env python3
"""
Batch Artist DNA Training Script

Downloads tracks per artist from YouTube, generates AudioDNA profiles,
aggregates into ArtistDNA, and uploads to GCS.

Usage:
    python batch_train_dna.py                      # Train all default artists
    python batch_train_dna.py --artists "Drake,Future"  # Train specific artists
    python batch_train_dna.py --max-tracks 10      # Limit tracks per artist
    python batch_train_dna.py --stems               # Enable stem separation (slower)
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

from ml.hybrid_trainer import HybridTrainer
from audio_dna import ArtistDNA
from audio_dna.gcs_storage import DNAStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_dna_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default target artists for DNA profiling
DEFAULT_ARTISTS = [
    "Drake",
    "Travis Scott",
    "Metro Boomin",
    "Future",
    "21 Savage",
    "Gunna",
    "Lil Baby",
    "Young Thug",
    "Playboi Carti",
    "Don Toliver",
    "Yeat",
    "Ken Carson",
    "Destroy Lonely",
    "SZA",
    "Summer Walker",
]


def train_artist_dna(
    artist: str,
    trainer: HybridTrainer,
    dna_builder: ArtistDNA,
    storage: DNAStorage,
    max_tracks: int = 20,
    upload_gcs: bool = True,
) -> dict | None:
    """Download tracks for an artist and build their DNA profile."""
    logger.info(f"{'='*60}")
    logger.info(f"Training DNA for: {artist}")
    logger.info(f"{'='*60}")

    t0 = time.perf_counter()

    # Step 1: Download tracks from YouTube
    logger.info(f"Downloading up to {max_tracks} tracks...")
    audio_files = trainer.download_from_youtube(artist, max_videos=max_tracks)

    if not audio_files:
        logger.warning(f"No tracks downloaded for {artist}, skipping")
        return None

    logger.info(f"Downloaded {len(audio_files)} tracks for {artist}")

    # Step 2: Build artist DNA profile
    try:
        profile = dna_builder.build_artist_profile(audio_files, artist, save=True)
    except Exception as e:
        logger.error(f"DNA profiling failed for {artist}: {e}")
        # Clean up downloaded files
        _cleanup_audio(audio_files)
        return None

    # Step 3: Upload to GCS
    if upload_gcs:
        try:
            storage.upload_artist_profile(profile)
            logger.info(f"Uploaded {artist} DNA to GCS")
        except Exception as e:
            logger.warning(f"GCS upload failed for {artist}: {e}")

    # Step 4: Clean up downloaded audio files
    _cleanup_audio(audio_files)

    elapsed = time.perf_counter() - t0
    logger.info(
        f"Done: {artist} — {profile['track_count']} tracks, "
        f"BPM {profile['tempo'].get('bpm_mean', '?')}, "
        f"Key {profile['key']['top_key']}, "
        f"{len(profile['signature_tags'])} signature tags, "
        f"{elapsed:.0f}s"
    )
    return profile


def _cleanup_audio(audio_files: list[str]):
    """Remove downloaded audio files and their parent temp directories."""
    dirs_to_remove = set()
    for f in audio_files:
        p = Path(f)
        if p.exists():
            p.unlink()
        # Track parent dirs that look like our temp dirs
        if p.parent.name.startswith("typebeat_"):
            dirs_to_remove.add(p.parent)

    for d in dirs_to_remove:
        try:
            if d.exists():
                shutil.rmtree(d)
                logger.info(f"Cleaned up temp dir: {d}")
        except Exception as e:
            logger.warning(f"Failed to clean up {d}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Batch Artist DNA Training")
    parser.add_argument(
        "--artists",
        type=str,
        default=None,
        help="Comma-separated artist names (default: built-in list of 15)",
    )
    parser.add_argument(
        "--max-tracks",
        type=int,
        default=20,
        help="Max tracks to download per artist (default: 20)",
    )
    parser.add_argument(
        "--stems",
        action="store_true",
        help="Enable stem separation (adds ~80s/track, better quality)",
    )
    parser.add_argument(
        "--no-gcs",
        action="store_true",
        help="Skip GCS upload (local only)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip artists that already have a DNA profile (default: True)",
    )
    args = parser.parse_args()

    artists = (
        [a.strip() for a in args.artists.split(",")]
        if args.artists
        else DEFAULT_ARTISTS
    )

    # Check which artists already have profiles
    dna_dir = Path(__file__).parent / "data" / "artist_dna"
    if args.skip_existing and dna_dir.exists():
        existing = {p.stem.lower() for p in dna_dir.glob("*.json")}
        original_count = len(artists)
        artists = [
            a for a in artists
            if a.lower().replace(" ", "_").replace("/", "_") not in existing
        ]
        skipped = original_count - len(artists)
        if skipped:
            logger.info(f"Skipping {skipped} artists with existing profiles")

    if not artists:
        logger.info("All artists already have DNA profiles. Nothing to do.")
        return

    logger.info(f"Training DNA for {len(artists)} artists: {', '.join(artists)}")
    logger.info(f"Max tracks per artist: {args.max_tracks}")
    logger.info(f"Stems: {'enabled' if args.stems else 'disabled'}")
    logger.info(f"GCS upload: {'disabled' if args.no_gcs else 'enabled'}")
    logger.info("")

    # Initialize components
    trainer = HybridTrainer(
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    )
    dna_builder = ArtistDNA(enable_stems=args.stems)
    storage = DNAStorage()

    # Train each artist
    results = []
    for i, artist in enumerate(artists, 1):
        logger.info(f"\n[{i}/{len(artists)}] Processing: {artist}")
        try:
            profile = train_artist_dna(
                artist=artist,
                trainer=trainer,
                dna_builder=dna_builder,
                storage=storage,
                max_tracks=args.max_tracks,
                upload_gcs=not args.no_gcs,
            )
            results.append({
                "artist": artist,
                "success": profile is not None,
                "track_count": profile["track_count"] if profile else 0,
                "bpm": profile["tempo"].get("bpm_mean") if profile else None,
                "key": profile["key"]["top_key"] if profile else None,
            })
        except Exception as e:
            logger.error(f"Unexpected error for {artist}: {e}")
            results.append({"artist": artist, "success": False, "error": str(e)})

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("BATCH DNA TRAINING COMPLETE")
    logger.info(f"{'='*60}")
    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if not r.get("success")]
    logger.info(f"Success: {len(successes)}/{len(results)}")
    for r in successes:
        logger.info(f"  {r['artist']}: {r['track_count']} tracks, BPM {r['bpm']}, Key {r['key']}")
    if failures:
        logger.info(f"Failed: {len(failures)}")
        for r in failures:
            logger.info(f"  {r['artist']}: {r.get('error', 'no tracks')}")

    # Save results summary
    summary_path = dna_dir / "_batch_results.json"
    with open(summary_path, "w") as f:
        json.dump({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "results": results}, f, indent=2)
    logger.info(f"\nResults saved to {summary_path}")


if __name__ == "__main__":
    main()
