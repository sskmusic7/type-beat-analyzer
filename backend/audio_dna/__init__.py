"""
Audio DNA — inference modules for Cloud Run.

Only inference classes are exported here. Training-only modules
(StemSeparator, ArtistDNA, DNAStorage) remain on Shadow PC.

Modules:
    CLAPScorer         - Zero-shot text-prompt scoring
    FeatureExtractor   - Tempo/key/spectral/MFCC/energy/rhythm
    AudioDNA           - Unified profile combining CLAP + features
    BlendEngine        - FAISS similarity search + blend percentages
"""

from .clap_scorer import CLAPScorer
from .feature_extractor import FeatureExtractor
from .audio_dna import AudioDNA
from .blend_engine import BlendEngine

__all__ = [
    "CLAPScorer", "FeatureExtractor", "AudioDNA", "BlendEngine",
]
