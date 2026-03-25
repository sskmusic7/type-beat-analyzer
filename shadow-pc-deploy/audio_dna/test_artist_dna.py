#!/usr/bin/env python3
"""
CLI tool to build an artist DNA profile from local audio files.

Usage:
    python audio_dna/test_artist_dna.py --artist "SSK" --dir "path/to/tracks"
    python audio_dna/test_artist_dna.py --artist "SSK" --files track1.mp3 track2.mp3
    python audio_dna/test_artist_dna.py --artist "SSK" --dir "path/to/tracks" --stems
"""

import argparse
import json
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from audio_dna.artist_dna import ArtistDNA


def main():
    parser = argparse.ArgumentParser(description="Build an artist DNA profile.")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--dir", help="Directory containing audio files")
    parser.add_argument("--files", nargs="+", help="Specific audio files")
    parser.add_argument("--stems", action="store_true", help="Enable stem separation (slow)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--no-save", action="store_true", help="Don't save profile to disk")
    args = parser.parse_args()

    # Collect audio files
    audio_paths = []
    if args.dir:
        d = Path(args.dir)
        audio_paths.extend(sorted(str(p) for p in d.glob("*.mp3")))
        audio_paths.extend(sorted(str(p) for p in d.glob("*.wav")))
    if args.files:
        audio_paths.extend(args.files)

    if not audio_paths:
        print("Error: no audio files found. Use --dir or --files.", file=sys.stderr)
        sys.exit(1)

    print(f"\nFound {len(audio_paths)} tracks for '{args.artist}'")
    for p in audio_paths:
        print(f"  - {Path(p).name}")

    builder = ArtistDNA(enable_stems=args.stems)
    profile = builder.build_artist_profile(audio_paths, args.artist, save=not args.no_save)

    if args.json:
        print(json.dumps(profile, indent=2))
        return

    print(f"\n{'=' * 60}")
    print(f"  Artist DNA: {profile['artist']}")
    print(f"  Tracks: {profile['track_count']}")
    print(f"  Vector: {profile['vector_dim']} dimensions")
    print(f"{'=' * 60}")

    t = profile.get("tempo", {})
    if t:
        print(f"\n  TEMPO:  {t['bpm_mean']} BPM avg (range: {t['bpm_min']}-{t['bpm_max']})")

    k = profile.get("key", {})
    if k:
        print(f"  KEY:    {k['top_key']} (most common)")
        top3 = list(k.get("distribution", {}).items())[:3]
        for key, pct in top3:
            print(f"          {key}: {pct*100:.0f}%")

    tags = profile.get("signature_tags", [])
    if tags:
        print(f"\n  SIGNATURE TAGS ({len(tags)}):")
        for tag in tags[:10]:
            bar = "#" * int(tag["avg_score"] * 30)
            print(f"    {tag['avg_score']:.3f} ({tag['frequency']*100:.0f}%) {bar} {tag['tag']}")

    s = profile.get("spectral", {})
    if s:
        print(f"\n  SPECTRAL: centroid={s['centroid_mean']} Hz, flatness={s['flatness_mean']}")

    e = profile.get("energy", {})
    if e:
        print(f"  ENERGY:   rms={e['rms_mean']:.4f}")

    r = profile.get("rhythm", {})
    if r:
        print(f"  RHYTHM:   density={r['onset_density_mean']} onsets/s")

    stems = profile.get("stems")
    if stems:
        print(f"\n  STEM MIX (avg):")
        for name, data in stems.items():
            pct = data["mix_ratio_mean"] * 100
            print(f"    {name:8s}: {pct:5.1f}%")

    m = profile.get("meta", {})
    print(f"\n  Processed in {m.get('processing_time_sec', '?')}s")
    print()


if __name__ == "__main__":
    main()
