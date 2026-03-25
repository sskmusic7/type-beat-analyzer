#!/usr/bin/env python3
"""
CLI tool to test the FeatureExtractor on an audio file.

Usage:
    python audio_dna/test_features.py <path-to-audio-file>
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio_dna.feature_extractor import FeatureExtractor


def main():
    parser = argparse.ArgumentParser(description="Extract audio features with librosa.")
    parser.add_argument("audio", help="Path to a WAV or MP3 file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    extractor = FeatureExtractor()

    t0 = time.perf_counter()
    features = extractor.extract(str(audio_path))
    elapsed = time.perf_counter() - t0

    if args.json:
        print(json.dumps(features, indent=2))
        return

    print(f"\n{'=' * 60}")
    print(f"  Audio Features: {audio_path.name}")
    print(f"  Extracted in {elapsed:.1f}s")
    print(f"{'=' * 60}")

    print(f"\n  Duration:  {features['meta']['duration_sec']}s")
    print(f"  Tempo:     {features['tempo']['bpm']} BPM")
    print(f"             (half-time: {features['tempo']['half_time']}, "
          f"double: {features['tempo']['double_time']})")
    print(f"  Key:       {features['key']['key_label']} "
          f"(confidence: {features['key']['confidence']})")

    print(f"\n  Spectral:")
    print(f"    Centroid:  {features['spectral']['centroid_mean']} Hz")
    print(f"    Rolloff:   {features['spectral']['rolloff_mean']} Hz")
    print(f"    Bandwidth: {features['spectral']['bandwidth_mean']} Hz")
    print(f"    Flatness:  {features['spectral']['flatness_mean']}")

    print(f"\n  Energy:")
    print(f"    RMS mean:       {features['energy']['rms_mean']}")
    print(f"    Dynamic range:  {features['energy']['dynamic_range_db']} dB")

    print(f"\n  Rhythm:")
    print(f"    Onset density:   {features['rhythm']['onset_density']} onsets/sec")
    print(f"    Beat regularity: {features['rhythm']['beat_regularity']}")
    print(f"    Num beats:       {features['rhythm']['num_beats']}")

    print()


if __name__ == "__main__":
    main()
