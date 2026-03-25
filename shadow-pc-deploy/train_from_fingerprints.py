#!/usr/bin/env python3
"""
Job 9: Bootstrap DNA profiles from existing fingerprint metadata.

Since original audio files were deleted after fingerprinting, this script:
1. Reads artist names from fingerprint_metadata.json
2. Filters out artists that already have DNA profiles
3. Downloads fresh tracks via YouTube for remaining artists
4. Builds DNA profiles using the batch training pipeline

Usage:
    python train_from_fingerprints.py              # Train all missing
    python train_from_fingerprints.py --max-tracks 10  # Limit per artist
    python train_from_fingerprints.py --limit 20   # Only first 20 missing artists
"""

import os
import sys
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="Train DNA from fingerprint DB artists")
    parser.add_argument("--max-tracks", type=int, default=10, help="Tracks per artist (default: 10)")
    parser.add_argument("--limit", type=int, default=0, help="Max artists to process (0=all)")
    parser.add_argument("--min-fingerprints", type=int, default=3,
                        help="Only include artists with >= N fingerprints (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Just list artists, don't train")
    args = parser.parse_args()

    # Load fingerprint metadata
    meta_path = Path("data/models/fingerprint_metadata.json")
    if not meta_path.exists():
        print("No fingerprint metadata found")
        return

    with open(meta_path) as f:
        metadata = json.load(f)

    # Count by artist
    artist_counts = {}
    for m in metadata:
        a = m.get("artist", "Unknown")
        artist_counts[a] = artist_counts.get(a, 0) + 1

    # Filter by min fingerprints
    eligible = {a: c for a, c in artist_counts.items()
                if c >= args.min_fingerprints and a != "Unknown"}

    # Check which already have DNA profiles
    dna_dir = Path("data/artist_dna")
    existing = set()
    if dna_dir.exists():
        for p in dna_dir.glob("*.json"):
            if p.name.startswith("_"):
                continue
            try:
                with open(p) as f:
                    data = json.load(f)
                existing.add(data.get("artist", "").lower())
            except Exception:
                continue

    # Find missing artists
    missing = []
    for artist, count in sorted(eligible.items(), key=lambda x: -x[1]):
        if artist.lower() not in existing:
            missing.append((artist, count))

    print(f"Fingerprint DB: {len(metadata)} fingerprints, {len(artist_counts)} artists")
    print(f"Eligible (>={args.min_fingerprints} fingerprints): {len(eligible)}")
    print(f"Already have DNA: {len(existing)}")
    print(f"Missing DNA profiles: {len(missing)}")
    print()

    if args.limit > 0:
        missing = missing[:args.limit]

    if not missing:
        print("All eligible artists already have DNA profiles!")
        return

    print(f"Will train {len(missing)} artists:")
    for artist, count in missing:
        print(f"  {artist} ({count} fingerprints)")

    if args.dry_run:
        print("\n(dry run — no training)")
        return

    # Import and run batch training
    from batch_train_dna import train_artist_dna, _cleanup_audio
    from ml.hybrid_trainer import HybridTrainer
    from audio_dna import ArtistDNA
    from audio_dna.gcs_storage import DNAStorage

    trainer = HybridTrainer(
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    )
    dna_builder = ArtistDNA(enable_stems=False)
    storage = DNAStorage()

    results = []
    for i, (artist, fp_count) in enumerate(missing, 1):
        print(f"\n[{i}/{len(missing)}] Training: {artist} ({fp_count} fingerprints in DB)")
        try:
            profile = train_artist_dna(
                artist=artist,
                trainer=trainer,
                dna_builder=dna_builder,
                storage=storage,
                max_tracks=args.max_tracks,
            )
            results.append({"artist": artist, "success": profile is not None})
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"artist": artist, "success": False, "error": str(e)})

    successes = sum(1 for r in results if r.get("success"))
    print(f"\n{'='*50}")
    print(f"Done: {successes}/{len(results)} artists profiled successfully")


if __name__ == "__main__":
    main()
