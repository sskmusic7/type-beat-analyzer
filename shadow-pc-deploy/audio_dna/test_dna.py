#!/usr/bin/env python3
"""
CLI tool to generate a full AudioDNA profile for an audio file.

Usage:
    python audio_dna/test_dna.py <path-to-audio-file>
    python audio_dna/test_dna.py beat.mp3 --fast          # skip stems
    python audio_dna/test_dna.py beat.mp3 --json           # raw JSON
    python audio_dna/test_dna.py beat.mp3 --json --fast    # fast + JSON
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio_dna.audio_dna import AudioDNA


def main():
    parser = argparse.ArgumentParser(description="Generate AudioDNA profile for a track.")
    parser.add_argument("audio", help="Path to a WAV or MP3 file")
    parser.add_argument("--fast", action="store_true", help="Skip stem separation (much faster)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--no-clap", action="store_true", help="Skip CLAP scoring")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    dna = AudioDNA(
        enable_clap=not args.no_clap,
        enable_stems=not args.fast,
    )

    t0 = time.perf_counter()
    if args.fast:
        profile = dna.profile_fast(str(audio_path))
    else:
        profile = dna.profile(str(audio_path))
    elapsed = time.perf_counter() - t0

    if args.json:
        print(json.dumps(profile, indent=2))
        return

    print(f"\n{'=' * 60}")
    print(f"  AudioDNA Profile: {audio_path.name}")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"{'=' * 60}")

    # Features
    f = profile.get("features", {})
    if f:
        print(f"\n  TEMPO:    {f['tempo']['bpm']} BPM")
        print(f"  KEY:      {f['key']['key_label']} (conf: {f['key']['confidence']})")
        print(f"  ENERGY:   RMS={f['energy']['rms_mean']:.4f}, "
              f"Dynamic range={f['energy']['dynamic_range_db']} dB")
        print(f"  RHYTHM:   {f['rhythm']['onset_density']} onsets/s, "
              f"regularity={f['rhythm']['beat_regularity']}")

    # CLAP tags
    tags = profile.get("clap_tags", [])
    if tags:
        print(f"\n  TOP CLAP TAGS:")
        for i, t in enumerate(tags[:10], 1):
            bar = "#" * int(t["score"] * 30)
            print(f"    {i:2d}. {t['score']:.3f} {bar:<30s} {t['tag']}")

    # Stems
    stems = profile.get("stems")
    if stems and stems.get("stems"):
        print(f"\n  STEM MIX:")
        for name, data in stems["stems"].items():
            pct = data["mix_ratio"] * 100
            bar = "#" * int(pct / 2)
            print(f"    {name:8s}: {pct:5.1f}% {bar}")
        print(f"    Dominant: {stems['dominant_stem']}")
        print(f"    Has vocals: {stems['has_vocals']}")

    # Vector size
    vec = dna.to_vector(profile)
    print(f"\n  DNA Vector: {len(vec)} dimensions")
    print()


if __name__ == "__main__":
    main()
