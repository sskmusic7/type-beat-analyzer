"""
Pydantic schemas for API request/response models
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ArtistMatch(BaseModel):
    artist: str
    confidence: float  # 0.0 to 1.0
    trending: Optional['TrendingData'] = None


class TrendingData(BaseModel):
    rank: Optional[int] = None
    velocity: float  # views/day since upload
    total_views: int
    upload_date: Optional[datetime] = None
    engagement_rate: Optional[float] = None
    trend_direction: str  # "up", "down", "stable"


class AnalysisResult(BaseModel):
    matches: List[ArtistMatch]
    processing_time_ms: float


class TrendingArtist(BaseModel):
    artist: str
    rank: int
    velocity: float
    total_views: int
    trend_direction: str


class FingerprintMatch(BaseModel):
    id: int
    artist: str
    title: str
    similarity: float
    distance: float
    rank: int
    audio_hash: str


class FingerprintUpload(BaseModel):
    artist: str
    title: Optional[str] = None
    uploader_id: Optional[str] = None


class FingerprintStats(BaseModel):
    total_fingerprints: int
    artists: int
    artist_list: List[str]


# Update forward references
ArtistMatch.model_rebuild()
AnalysisResult.model_rebuild()
