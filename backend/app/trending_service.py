"""
Trending intelligence service
Pulls data from YouTube Data API and caches in Redis
"""

import os
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import redis
import json

from app.schemas import TrendingData, TrendingArtist

logger = logging.getLogger(__name__)


class TrendingService:
    """
    Service for fetching and caching trending type beat data
    Uses YouTube Data API v3 to track "[Artist] type beat" searches
    """
    
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        
        # Redis connection with error handling
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
        except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
            logger.warning(f"Redis not available, using in-memory cache: {str(e)}")
            self.redis_client = None
            self.redis_available = False
            self._memory_cache = {}
        
        if self.youtube_api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            except Exception as e:
                logger.warning(f"YouTube API initialization failed: {str(e)}")
                self.youtube = None
        else:
            logger.warning("YOUTUBE_API_KEY not set, trending features will be limited")
            self.youtube = None
    
    async def get_trending_data(self, artist_name: str) -> TrendingData:
        """
        Get trending data for a specific artist
        
        Args:
            artist_name: Name of the artist
        
        Returns:
            TrendingData with rank, velocity, views, etc.
        """
        # Check cache first
        cache_key = f"trending:{artist_name.lower()}"
        cached = None
        
        if self.redis_available and self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
            except Exception as e:
                logger.warning(f"Redis get failed: {str(e)}")
        elif not self.redis_available:
            # Use in-memory cache
            cached = self._memory_cache.get(cache_key)
        
        if cached:
            try:
                data = json.loads(cached) if isinstance(cached, str) else cached
                return TrendingData(**data)
            except Exception as e:
                logger.warning(f"Failed to parse cached data: {str(e)}")
        
        # Fetch from YouTube API
        if self.youtube:
            try:
                data = await self._fetch_youtube_trending(artist_name)
                # Cache for 1 hour
                cache_data = json.dumps(data.dict())
                if self.redis_available and self.redis_client:
                    try:
                        self.redis_client.setex(cache_key, 3600, cache_data)
                    except Exception as e:
                        logger.warning(f"Redis setex failed: {str(e)}")
                elif not self.redis_available:
                    # Use in-memory cache (no expiration for simplicity)
                    self._memory_cache[cache_key] = cache_data
                return data
            except Exception as e:
                logger.error(f"Error fetching YouTube data: {str(e)}")
        
        # Return default if API unavailable
        return TrendingData(
            rank=None,
            velocity=0.0,
            total_views=0,
            upload_date=None,
            engagement_rate=None,
            trend_direction="stable"
        )
    
    async def get_top_trending(self, limit: int = 20) -> List[TrendingArtist]:
        """
        Get top trending artists for type beats
        
        Args:
            limit: Number of artists to return
        
        Returns:
            List of TrendingArtist sorted by velocity
        """
        cache_key = "trending:top"
        cached = None
        
        if self.redis_available and self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
            except Exception as e:
                logger.warning(f"Redis get failed: {str(e)}")
        elif not self.redis_available:
            cached = self._memory_cache.get(cache_key)
        
        if cached:
            try:
                data = json.loads(cached) if isinstance(cached, str) else cached
                return [TrendingArtist(**item) for item in data]
            except Exception as e:
                logger.warning(f"Failed to parse cached data: {str(e)}")
        
        # TODO: Fetch from YouTube API for multiple artists
        # For MVP, return mock data
        if not self.youtube:
            return self._get_mock_trending(limit)
        
        # Fetch real data (implement when API key is available)
        try:
            artists = await self._fetch_top_trending_artists(limit)
            # Cache for 6 hours
            cache_data = json.dumps([a.dict() for a in artists])
            if self.redis_available and self.redis_client:
                try:
                    self.redis_client.setex(cache_key, 21600, cache_data)
                except Exception as e:
                    logger.warning(f"Redis setex failed: {str(e)}")
            elif not self.redis_available:
                self._memory_cache[cache_key] = cache_data
            return artists
        except Exception as e:
            logger.error(f"Error fetching top trending: {str(e)}")
            return self._get_mock_trending(limit)
    
    async def _fetch_youtube_trending(self, artist_name: str) -> TrendingData:
        """
        Fetch trending data from YouTube for a specific artist
        """
        search_query = f"{artist_name} type beat"
        logger.info(f"Fetching trending data for: {artist_name}")
        logger.info(f"Search query: {search_query}")
        
        try:
            # Search for recent uploads (last 7 days)
            search_response = self.youtube.search().list(
                q=search_query,
                part='id,snippet',
                type='video',
                order='date',
                maxResults=10,
                publishedAfter=(datetime.now() - timedelta(days=7)).isoformat() + 'Z'
            ).execute()
            
            if not search_response.get('items'):
                logger.warning(f"No videos found for {artist_name}")
                return TrendingData(
                    rank=None,
                    velocity=0.0,
                    total_views=0,
                    trend_direction="stable"
                )
            
            # Get video statistics
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            videos_response = self.youtube.videos().list(
                part='statistics,snippet',
                id=','.join(video_ids)
            ).execute()
            
            # Calculate velocity (views per day) - IMPROVED
            total_views = 0
            velocities = []
            video_count = 0
            
            for video in videos_response.get('items', []):
                stats = video['statistics']
                views = int(stats.get('viewCount', 0))
                total_views += views
                video_count += 1
                
                # Calculate time since upload (handle same-day uploads)
                published = datetime.fromisoformat(
                    video['snippet']['publishedAt'].replace('Z', '+00:00')
                )
                now = datetime.now(published.tzinfo)
                time_diff = now - published
                
                # Use hours for more accurate calculation
                hours_old = time_diff.total_seconds() / 3600
                
                # Minimum 1 hour to avoid division issues
                if hours_old < 1:
                    hours_old = 1
                
                # Calculate velocity: views per day
                # For very recent videos, this gives a more accurate picture
                velocity = views / (hours_old / 24)
                velocities.append(velocity)
            
            # Use median velocity for more accurate trending (less affected by outliers)
            if velocities:
                velocities_sorted = sorted(velocities)
                mid = len(velocities_sorted) // 2
                if len(velocities_sorted) % 2 == 0:
                    avg_velocity = (velocities_sorted[mid-1] + velocities_sorted[mid]) / 2
                else:
                    avg_velocity = velocities_sorted[mid]
            else:
                avg_velocity = 0.0
            
            # Improved trend direction thresholds
            # Based on typical type beat performance
            if avg_velocity > 200:  # Lowered from 1000
                direction = "up"
            elif avg_velocity < 20:  # Lowered from 100
                direction = "down"
            else:
                direction = "stable"
            
            logger.info(f"{artist_name}: velocity={avg_velocity:.2f}, total_views={total_views}, direction={direction}, videos={video_count}")
            
            return TrendingData(
                rank=None,  # Will be set when comparing with other artists
                velocity=round(avg_velocity, 2),  # Round to 2 decimals
                total_views=total_views,
                upload_date=None,
                engagement_rate=None,
                trend_direction=direction
            )
        
        except HttpError as e:
            logger.error(f"YouTube API error: {str(e)}")
            raise
    
    async def _fetch_top_trending_artists(self, limit: int) -> List[TrendingArtist]:
        """
        Fetch top trending artists by analyzing multiple searches
        """
        # List of artists to check (will be expanded)
        artists_to_check = [
            "Drake", "Travis Scott", "Metro Boomin", "Central Cee",
            "21 Savage", "Future", "Lil Baby", "Playboi Carti"
        ]
        
        trending_list = []
        
        for artist in artists_to_check[:limit]:
            try:
                data = await self._fetch_youtube_trending(artist)
                # Only add if we got meaningful data
                if data.total_views > 0 or data.velocity > 0:
                    trending_list.append(TrendingArtist(
                        artist=artist,
                        rank=0,  # Will be sorted
                        velocity=data.velocity,
                        total_views=data.total_views,
                        trend_direction=data.trend_direction
                    ))
            except Exception as e:
                logger.error(f"Error fetching data for {artist}: {str(e)}")
        
        # Sort by velocity (descending), then by total_views as tiebreaker
        trending_list.sort(key=lambda x: (x.velocity, x.total_views), reverse=True)
        for i, artist in enumerate(trending_list, 1):
            artist.rank = i
        
        return trending_list[:limit]
    
    def _get_mock_trending(self, limit: int) -> List[TrendingArtist]:
        """
        Mock trending data for testing when API is unavailable
        """
        mock_artists = [
            ("Drake", 2500.0, 150000),
            ("Travis Scott", 2200.0, 130000),
            ("Metro Boomin", 1800.0, 110000),
            ("Central Cee", 1600.0, 95000),
            ("21 Savage", 1400.0, 85000),
            ("Future", 1200.0, 75000),
            ("Lil Baby", 1000.0, 65000),
            ("Playboi Carti", 900.0, 55000),
        ]
        
        return [
            TrendingArtist(
                artist=artist,
                rank=i + 1,
                velocity=velocity,
                total_views=views,
                trend_direction="up" if i < 3 else "stable"
            )
            for i, (artist, velocity, views) in enumerate(mock_artists[:limit])
        ]
