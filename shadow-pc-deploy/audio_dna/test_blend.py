#!/usr/bin/env python3
"""
CLI tool to test the blend engine.

Usage:
    # Query a beat against loaded artist profiles:
    python audio_dna/test_blend.py --beat beat.mp3 --profiles data/artist_dna/

    # Just load profiles and show similarity matrix:
    python audio_dna/test_blend.py --profiles data/artist_dna/ --matrix
"""

import argparse
import json
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from audio_dna.blend_engine import BlendEngine
from audio_dna.audio_dna import AudioDNA


def main():
    parser = argparse.ArgumentParser(description="Test the blend engine.")
    parser.add_argument("--beat", help="Path to a beat to analyze")
    parser.add_argument("--profiles", required=True, help="Directory of artist DNA profiles")
    parser.add_argument("--matrix", action="store_true", help="Show artist similarity matrix")
    parser.add_argument("--top", type=int, default=5, help="Number of matches")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    engine = BlendEngine()
    count = engine.add_artists_from_dir(args.profiles)
    print(f"\nLoaded {count} artist profiles into blend engine")

    if args.matrix:
        matrix = engine.artist_similarity_matrix()
        if matrix:
            print(f"\nArtist Similarity Matrix:")
            for artist_a, sims in matrix.items():
                for artist_b, score in sorted(sims.items(), key=lambda x: -x[1]):
                    print(f"  {artist_a} <-> {artist_b}: {score:.4f}")
        else:
            print("Need 2+ artists for similarity matrix.")

    if args.beat:
        audio_path = Path(args.beat)
        if not audio_path.exists():
            print(f"Error: file not found: {audio_path}", file=sys.stderr)
            sys.exit(1)

        print(f"\nAnalyzing beat: {audio_path.name}")
        dna = AudioDNA(enable_stems=False)
        profile = dna.profile_fast(str(audio_path))
        vector = dna.to_vector(profile)

        result = engine.blend(vector, top_k=args.top)

        if args.json:
            print(json.dumps(result, indent=2))
            return

        print(f"\n{'=' * 60}")
        print(f"  Blend Analysis: {audio_path.name}")
        print(f"{'=' * 60}")
        print(f"\n  Primary match: {result['primary']}")
        print(f"\n  BLEND:")
        for m in result["matches"]:
            pct = m["blend_pct"]
            bar = "#" * int(pct / 2)
            print(f"    {m['artist']:20s} {pct:5.1f}%  {bar}")
            print(f"      similarity={m['similarity']:.4f}, "
                  f"BPM={m.get('bpm_mean', '?')}, key={m.get('top_key', '?')}")
        print()


if __name__ == "__main__":
    main()
