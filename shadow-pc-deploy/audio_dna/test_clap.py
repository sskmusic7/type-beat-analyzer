#!/usr/bin/env python3
"""
CLI tool to test CLAP zero-shot scoring on an audio file.

Usage:
    python audio_dna/test_clap.py <path-to-audio-file>
    python audio_dna/test_clap.py beat.wav
    python audio_dna/test_clap.py beat.mp3 --top 20
"""

import argparse
import sys
import time
from pathlib import Path

# Allow running from shadow-pc-deploy/ directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio_dna.clap_scorer import CLAPScorer


def main():
    parser = argparse.ArgumentParser(
        description="Score an audio file with CLAP zero-shot text prompts."
    )
    parser.add_argument("audio", help="Path to a WAV or MP3 file")
    parser.add_argument(
        "--top", type=int, default=15, help="Number of top tags to show (default: 15)"
    )
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    scorer = CLAPScorer()

    t0 = time.perf_counter()
    tags = scorer.top_tags(str(audio_path), n=args.top)
    elapsed = time.perf_counter() - t0

    print(f"\n{'=' * 60}")
    print(f"  CLAP Tags for: {audio_path.name}")
    print(f"  Scored {len(scorer.prompts)} prompts in {elapsed:.1f}s")
    print(f"{'=' * 60}\n")

    for rank, (prompt, score) in enumerate(tags, 1):
        bar = "#" * int(score * 40)
        print(f"  {rank:2d}. {score:.4f}  {bar:<40s}  {prompt}")

    print()


if __name__ == "__main__":
    main()
