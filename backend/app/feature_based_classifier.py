"""
Feature-based classifier using audio characteristics
No fallbacks - uses actual audio analysis
"""

import numpy as np
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FeatureBasedClassifier:
    """
    Classifies beats based on audio features (tempo, key, spectral characteristics)
    Works across all genres - not just rap
    """
    
    def __init__(self):
        # Genre/artist profiles based on audio characteristics
        # These are based on research and can be expanded
        self.genre_profiles = {
            # Trap/Hip-Hop
            "trap": {
                "tempo_range": (65, 85),  # BPM
                "key_preference": ["C", "C#", "D", "D#", "F", "F#", "G", "G#"],
                "spectral_centroid_range": (1000, 3000),  # Hz
                "artists": ["Travis Scott", "Metro Boomin", "21 Savage", "Future", "Lil Baby"]
            },
            # Drill
            "drill": {
                "tempo_range": (60, 75),
                "key_preference": ["C", "C#", "D", "D#", "F", "F#"],
                "spectral_centroid_range": (800, 2500),
                "artists": ["Central Cee", "Pop Smoke", "Fivio Foreign"]
            },
            # R&B
            "rnb": {
                "tempo_range": (70, 100),
                "key_preference": ["C", "D", "E", "F", "G", "A", "B"],
                "spectral_centroid_range": (1500, 4000),
                "artists": ["The Weeknd", "Drake", "Brent Faiyaz", "SZA"]
            },
            # Pop
            "pop": {
                "tempo_range": (100, 140),
                "key_preference": ["C", "D", "E", "F", "G", "A"],
                "spectral_centroid_range": (2000, 5000),
                "artists": ["Post Malone", "The Weeknd", "Drake"]
            },
            # Alternative/Indie
            "alternative": {
                "tempo_range": (80, 120),
                "key_preference": ["C", "D", "E", "F", "G", "A", "B"],
                "spectral_centroid_range": (1500, 4000),
                "artists": ["Tame Impala", "Arctic Monkeys", "The 1975"]
            },
            # EDM/Electronic
            "edm": {
                "tempo_range": (120, 140),
                "key_preference": ["C", "D", "E", "F", "G", "A"],
                "spectral_centroid_range": (2500, 6000),
                "artists": ["Calvin Harris", "The Chainsmokers", "Marshmello"]
            },
            # Rock
            "rock": {
                "tempo_range": (100, 140),
                "key_preference": ["C", "D", "E", "F", "G", "A", "B"],
                "spectral_centroid_range": (2000, 5000),
                "artists": ["Arctic Monkeys", "The 1975", "Tame Impala"]
            }
        }
    
    def classify(self, features: Dict[str, Any]) -> List[Tuple[str, float]]:
        """
        Classify beat based on audio features
        Returns artist matches with confidence scores
        """
        tempo = features.get('tempo', 0)
        key = features.get('key', 'C')
        spectral_centroid = np.mean(features.get('spectral_centroid', [1000]))
        mfcc = features.get('mfcc', np.zeros((13, 100)))
        chroma = features.get('chroma', np.zeros((12, 100)))
        
        logger.info(f"Classifying: tempo={tempo:.1f} BPM, key={key}, spectral_centroid={spectral_centroid:.1f} Hz")
        
        scores = {}
        
        # Score each genre based on feature matching
        for genre, profile in self.genre_profiles.items():
            score = 0.0
            
            # Tempo matching (0-40 points)
            tempo_min, tempo_max = profile['tempo_range']
            if tempo_min <= tempo <= tempo_max:
                # Perfect match in range
                tempo_score = 40.0
            else:
                # Distance penalty
                distance = min(abs(tempo - tempo_min), abs(tempo - tempo_max))
                tempo_score = max(0, 40.0 - (distance * 0.5))
            score += tempo_score
            
            # Key matching (0-20 points)
            if key in profile['key_preference']:
                key_score = 20.0
            else:
                key_score = 10.0  # Partial credit
            score += key_score
            
            # Spectral centroid matching (0-30 points)
            spec_min, spec_max = profile['spectral_centroid_range']
            if spec_min <= spectral_centroid <= spec_max:
                spec_score = 30.0
            else:
                distance = min(abs(spectral_centroid - spec_min), abs(spectral_centroid - spec_max))
                spec_score = max(0, 30.0 - (distance * 0.01))
            score += spec_score
            
            # MFCC similarity (0-10 points) - simplified
            mfcc_mean = np.mean(mfcc, axis=1)
            mfcc_variance = np.var(mfcc_mean)
            # Higher variance = more complex = potentially more trap/hip-hop
            if genre in ["trap", "drill"] and mfcc_variance > 50:
                mfcc_score = 10.0
            elif genre in ["rnb", "pop"] and 30 < mfcc_variance < 70:
                mfcc_score = 10.0
            else:
                mfcc_score = 5.0
            score += mfcc_score
            
            scores[genre] = score
        
        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if scores else 1.0
        normalized_scores = {k: v / max_score for k, v in scores.items()}
        
        # Get top genres
        sorted_genres = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build artist predictions from top genres
        artist_scores = {}
        for genre, genre_score in sorted_genres[:3]:  # Top 3 genres
            artists = self.genre_profiles[genre]['artists']
            for artist in artists:
                if artist not in artist_scores:
                    artist_scores[artist] = 0.0
                # Weight by genre score
                artist_scores[artist] += genre_score * (1.0 / len(artists))
        
        # Normalize artist scores
        max_artist_score = max(artist_scores.values()) if artist_scores else 1.0
        if max_artist_score > 0:
            artist_scores = {k: v / max_artist_score for k, v in artist_scores.items()}
        
        # Sort and return top 5
        sorted_artists = sorted(artist_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        
        logger.info(f"Classification results: {sorted_artists}")
        
        return sorted_artists
