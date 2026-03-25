"""
Audio DNA — multi-model audio analysis for type beat profiling.

Modules:
    CLAPScorer         - Zero-shot text-prompt scoring (Phase 1)
    FeatureExtractor   - Tempo/key/spectral/MFCC/energy/rhythm (Phase 2)
    StemSeparator      - Demucs v4 stem separation (Phase 3)
    AudioDNA           - Unified profile combining all modules (Phase 4)
"""

from .clap_scorer import CLAPScorer
from .feature_extractor import FeatureExtractor
from .stem_separator import StemSeparator
from .audio_dna import AudioDNA
from .artist_dna import ArtistDNA
from .blend_engine import BlendEngine

__all__ = [
    "CLAPScorer", "FeatureExtractor", "StemSeparator",
    "AudioDNA", "ArtistDNA", "BlendEngine",
]
